"""
Resilient Appium-Flutter driver wrapper with two timeout tiers.

[CORRECTION — verified against the actually-installed
Appium-Python-Client==3.1.1] Two things commonly suggested for this
don't work on this pinned version:

  1. `socket.setdefaulttimeout(N)` does nothing useful — AppiumConnection
     builds its own urllib3 pool and ignores the global socket default.
  2. The classmethod shortcut `AppiumConnection.set_timeout(N)`, called
     at import time before any instance exists, raises:
         AttributeError: type object 'AppiumConnection' has no
         attribute '_client_config'
     `_client_config` is only populated once an *instance* is
     constructed (see `RemoteConnection.__init__`), so the classmethod
     form only works AFTER a connection has already been made once
     elsewhere in the process — not as a one-time import-time setting.
     `AppiumClientConfig` (sometimes cited as a fix) does not exist in
     this version at all — importing it is an immediate ImportError
     that zeroes out collection for the whole shard.

  The verified, working mechanism on this version: construct an
  `AppiumConnection` instance yourself, mutate its
  `.client_config.timeout` attribute directly (an ordinary settable
  attribute on the `ClientConfig` object — confirmed via
  `inspect.getsource`), and pass that already-configured connection
  object as `command_executor` to `webdriver.Remote(...)`.

Two tiers:
  - APPIUM_COMMAND_TIMEOUT (12s default) for ordinary polling calls.
    Measured from real CI logs on the reference project this pattern
    was validated against: the slowest healthy call was ~3.9s, so 12s
    gives ~3x headroom without paying the cost of a 45s hang on a
    truly stuck call.
  - NEW_SESSION_TIMEOUT (60s default) is set only for the
    `new_session()` call itself, because Flutter's Observatory/VM
    Service handshake on a cold-started emulator can legitimately take
    longer than 12s the first time. Immediately after the session is
    created, the connection's timeout is dropped back to the everyday
    12s tier.
"""

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_connection import AppiumConnection

from config import (
    APPIUM_COMMAND_TIMEOUT,
    APPIUM_SERVER_URL,
    APK_PATH,
    APP_PACKAGE,
    AUTOMATION_NAME,
    DEVICE_NAME,
    NEW_SESSION_TIMEOUT,
    PLATFORM_NAME,
)


def build_capabilities() -> UiAutomator2Options:
    options = UiAutomator2Options()
    options.platform_name = PLATFORM_NAME
    options.automation_name = AUTOMATION_NAME
    options.device_name = DEVICE_NAME
    options.app = APK_PATH
    options.app_package = APP_PACKAGE
    options.new_command_timeout = 300
    # Flutter driver capabilities, not exposed as typed UiAutomator2Options fields:
    options.set_capability("noReset", True)
    options.set_capability("fullReset", False)
    # Without this, the app has zero runtime permissions after install (Android
    # 6.0+ default), so the Scanner screen permanently renders its
    # _NoCameraPermissionView with no capture/gallery/flash/AR buttons at all —
    # this was the root cause of test_camera_file_upload.py failing 26/26 and
    # much of test_inapp_messaging.py failing too. autoGrantPermissions grants
    # every manifest-declared runtime permission (camera included) at install
    # time, matching what test_capture_with_camera_permission_revoked_* already
    # assumed was the normal starting state (it explicitly revokes, then grants
    # back at the end — implying "granted" was always meant to be the default).
    options.set_capability("appium:autoGrantPermissions", True)
    # Wait up to 30s for a stable Dart isolate before sending the first command.
    # Required on Flutter 3.x / Impeller: the GPU backend replaces the isolate
    # once during init, so the isolate resolved at session-create time is dead
    # by the time the first flutter:waitFor arrives. This capability makes the
    # driver poll for a live isolate instead of failing immediately.
    options.set_capability("appium:flutterServerLaunchTimeout", 30000)
    return options


def new_driver():
    """Start a new session using the long (60s) timeout tier for the
    handshake itself, then drop back to the everyday (12s) tier for
    every command issued afterwards."""
    connection = AppiumConnection(APPIUM_SERVER_URL, keep_alive=True)
    connection.client_config.timeout = NEW_SESSION_TIMEOUT

    driver = webdriver.Remote(command_executor=connection, options=build_capabilities())

    # Session is up — drop to the everyday tier for all further commands.
    driver.command_executor.client_config.timeout = APPIUM_COMMAND_TIMEOUT
    return driver


def quit_driver(driver) -> None:
    if driver is None:
        return
    try:
        driver.quit()
    except BaseException:
        # A hung teardown must never crash the shard — catch BaseException,
        # not just Exception, since a signal-driven timeout mid-teardown
        # can raise something that isn't a plain Exception subclass.
        pass


class DriverProxy:
    """Transparent wrapper around the real Appium/Flutter-Driver session
    that can be reconnected in place.

    ROOT CAUSE this exists to fix: `utils.adb_helpers.force_stop_app()` /
    `relaunch_app()` kill and restart the app process directly via
    `adb shell`, completely outside Appium's own app-lifecycle commands.
    That's necessary because this engine combo doesn't support
    `driver.background_app()` (see adb_helpers module docstring) — but it
    means every such restart hands the app a brand-new Dart isolate that
    the *existing* Flutter-Driver session was never told about. The
    session's `appium:flutterServerLaunchTimeout` capability only waits
    for a live isolate once, at initial session creation — it does not
    re-run on a later adb-triggered relaunch. Every `flutter:*` command
    sent afterwards (waitFor/click/enterText/getText) is talking to a
    process that no longer exists, so it fails or times out. Since the
    `driver` fixture is session-scoped (one connection for the whole
    shard) and nearly every test resets app state this way, this is why
    the suite fails almost universally rather than test-by-test.

    Fix: after any raw-adb force-stop/relaunch, call `.reconnect()` to
    quit the stale session and open a fresh one — reusing the same
    session-creation path (`new_driver()`) that already correctly waits
    for a live isolate before returning.
    """

    def __init__(self, driver):
        self._driver = driver

    def reconnect(self):
        """Quit the (likely already-dead) session and open a fresh one
        against whatever app process is currently running. Call this
        immediately after any `adb_helpers.force_stop_app()` /
        `relaunch_app()` / `clear_app_data()` + relaunch sequence."""
        quit_driver(self._driver)
        self._driver = new_driver()
        return self._driver

    def __getattr__(self, name):
        # Forward everything (execute_script, get_screenshot_as_file,
        # command_executor, ...) to whichever real driver is current.
        return getattr(self._driver, name)
