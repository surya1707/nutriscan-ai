#!/usr/bin/env bash
# Runs one test shard inside the reactivecircus/android-emulator-runner
# `script:` step. Deliberately a real script file (not an inline
# multi-line `script: |` block) because that action executes each line
# of an inline block as its OWN separate `sh -c` subprocess — `cd`,
# `export`, and `$!` do not persist across lines there. A script file
# runs as a single continuous bash process, so all of that works
# normally here.
#
# Usage: ci_run_shard.sh <shard-number> <space-separated-test-files>
set -euo pipefail

SHARD_NUM="$1"
shift
TEST_FILES=("$@")

echo "== Shard ${SHARD_NUM}: starting Appium =="
appium --base-path / --log-level info &
APPIUM_PID=$!
sleep 8

echo "== Shard ${SHARD_NUM}: installing APK =="
adb install -r mobile-tests/apk/app-debug.apk

cd mobile-tests
export APK_PATH="$(pwd)/apk/app-debug.apk"
export DEVICE_NAME="emulator-5554"

echo "== Shard ${SHARD_NUM}: running pytest on: ${TEST_FILES[*]} =="
set +e
python -m pytest "${TEST_FILES[@]}" \
  --shard-name "shard-${SHARD_NUM}" \
  -v --reruns 1 --reruns-delay 3 \
  -p no:cacheprovider
PYTEST_EXIT=$?
set -e

echo "== Shard ${SHARD_NUM}: stopping Appium (pid ${APPIUM_PID}) =="
kill "${APPIUM_PID}" 2>/dev/null || true

# Exit non-zero if pytest failed, but only AFTER Appium is torn down and
# results are written to disk — the report-generation/upload steps that
# follow run regardless (they're gated on `if: always()`, not on this
# script's exit code).
exit "${PYTEST_EXIT}"