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
sleep 10

echo "== Shard ${SHARD_NUM}: installing APK =="
adb install -r mobile-tests/apk/app-debug.apk

# Pre-warm the app's Impeller GPU init before the first Appium session.
# Flutter 3.x / Impeller replaces the Dart isolate once during GPU backend
# initialisation. If the first Appium session catches the app mid-init it
# connects to an isolate that is immediately destroyed, causing every
# flutter:waitFor to return Error:{} from a dead WebSocket.
# Fix: launch the app briefly via monkey (fires the GPU init cycle), wait
# for Impeller to finish, then force-stop so the first Appium session gets
# a clean cold-start against an already-warmed GPU context.
echo "== Shard ${SHARD_NUM}: pre-warming GPU (Impeller init) =="
adb shell monkey -p com.example.nutriscan -c android.intent.category.LAUNCHER 1 || true
sleep 12
adb shell am force-stop com.example.nutriscan || true
sleep 2

cd mobile-tests
export APK_PATH="$(pwd)/apk/app-debug.apk"
export DEVICE_NAME="emulator-5554"

# Record the full set of test IDs this shard is SUPPOSED to run, before
# executing anything. If the job gets killed partway through (e.g. the
# 120-minute cap), raw-results.jsonl only contains whatever finished --
# there's otherwise no record that the rest never ran at all. Diffing
# this list against raw-results.jsonl at merge time is how
# generate_reports.py reports genuinely-never-executed tests instead of
# them just silently vanishing from the totals.
mkdir -p reports
python -m pytest "${TEST_FILES[@]}" --collect-only -q -p no:cacheprovider \
  | grep '::' > "reports/collected-shard-${SHARD_NUM}.txt" || true

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

# The shard job's pass/fail status in the GitHub Actions UI should reflect
# whether the shard *ran to completion*, not whether every individual test
# passed — that's a separate concern already enforced by
# check_pass_rate.py's threshold gate in the merge-reports job. Without
# this, every shard with even one failing test (i.e. basically every run)
# shows as a red X job, which is misleading at a glance and makes a
# genuinely-broken shard (crashed emulator, Appium never started, pytest
# itself erroring) indistinguishable from one that simply found bugs.
#
# pytest exit codes: 0 = all passed, 1 = some tests failed (still a normal,
# completed run) — both are "shard completed" as far as this job's status
# goes. 2 = usage error, 3 = internal/collection error, 4 = usage error,
# 5 = no tests collected — these mean something actually broke and should
# still fail the job.
echo "== Shard ${SHARD_NUM}: pytest exit code was ${PYTEST_EXIT} =="
if [ "${PYTEST_EXIT}" -eq 0 ] || [ "${PYTEST_EXIT}" -eq 1 ]; then
  echo "== Shard ${SHARD_NUM}: completed (pass/fail counts are in the report, not this job's status) =="
  exit 0
fi

echo "== Shard ${SHARD_NUM}: pytest exited abnormally (${PYTEST_EXIT}), not just test failures — failing the job =="
exit "${PYTEST_EXIT}"