"""
adb-based replacements for the three appium-flutter-driver commands that
raise "not supported" against this app's automation engine:

    driver.background_app(N)             -> not supported
    driver.set_network_connection()      -> not supported
    driver.execute_script("mobile: scrollGesture", {...})  -> HTTP 500

All three are driven directly via `adb shell` instead. This module is the
single place that shells out to adb so every test file imports the same
implementation rather than re-inventing subprocess calls.
"""

import subprocess
import time

from config import APP_PACKAGE, DEVICE_NAME


def _adb(*args: str, check: bool = True) -> str:
    cmd = ["adb", "-s", DEVICE_NAME, *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if check and result.returncode != 0:
        raise RuntimeError(f"adb command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def background_app(seconds: float = 2.0) -> None:
    """Send the app to background then relaunch it after `seconds`."""
    _adb("shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(seconds)
    _adb(
        "shell", "monkey", "-p", APP_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1",
    )


def set_wifi_enabled(enabled: bool) -> None:
    _adb("shell", "svc", "wifi", "enable" if enabled else "disable")


def set_data_enabled(enabled: bool) -> None:
    _adb("shell", "svc", "data", "enable" if enabled else "disable")


def set_network_offline() -> None:
    set_wifi_enabled(False)
    set_data_enabled(False)


def set_network_online() -> None:
    set_wifi_enabled(True)
    set_data_enabled(True)


def swipe(x: int, y_start: int, y_end: int, duration_ms: int = 200) -> None:
    """Replacement for `mobile: scrollGesture`, which returns HTTP 500 on
    appium-flutter-driver for this app's Flutter engine version."""
    _adb("shell", "input", "swipe", str(x), str(y_start), str(x), str(y_end), str(duration_ms))


def force_stop_app() -> None:
    _adb("shell", "am", "force-stop", APP_PACKAGE)


def relaunch_app() -> None:
    _adb(
        "shell", "monkey", "-p", APP_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1",
    )


def clear_app_data() -> None:
    """Wipes the app's Drift/SQLite DB and SharedPreferences — used by
    session-management and offline tests that need a clean device state."""
    _adb("shell", "pm", "clear", APP_PACKAGE)


def grant_camera_permission() -> None:
    _adb("shell", "pm", "grant", APP_PACKAGE, "android.permission.CAMERA", check=False)


def revoke_camera_permission() -> None:
    _adb("shell", "pm", "revoke", APP_PACKAGE, "android.permission.CAMERA", check=False)


def take_device_screenshot(local_path: str) -> None:
    remote = "/sdcard/_appium_shot.png"
    _adb("shell", "screencap", "-p", remote)
    subprocess.run(
        ["adb", "-s", DEVICE_NAME, "pull", remote, local_path],
        capture_output=True, timeout=20,
    )
    _adb("shell", "rm", remote, check=False)


def pull_logcat(local_path: str) -> None:
    log = _adb("logcat", "-d", "-v", "time", check=False)
    with open(local_path, "w") as f:
        f.write(log)
