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
    options.set_capability("noReset", False)
    options.set_capability("fullReset", False)
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
