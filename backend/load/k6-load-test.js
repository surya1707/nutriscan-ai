/**
 * k6 load/smoke test for nutriscan-ai backend.
 *
 * SCOPE (read before assuming this covers everything):
 * k6 makes real HTTP requests against a live server process -- it cannot
 * use FastAPI's in-process ASGITransport the way the pytest suite does.
 * That live server requires Firebase Admin SDK to initialize successfully
 * at import time (app/core/firebase.py calls init_firebase() unconditionally
 * unless "pytest" is in sys.modules), or the process exits immediately
 * (confirmed: sys.exit(1) when FIREBASE_CREDENTIALS_PATH is missing/invalid).
 *
 * There is no real Firebase project available in CI, so this script can
 * only load-test the endpoints reachable WITHOUT a genuinely valid ID
 * token: POST /scan/analyse, POST /scan/barcode, GET /health, GET /.
 * /users/me and /history need a real signed token this environment cannot
 * produce, so they are intentionally NOT covered here -- see the handover
 * README "Known testing gaps" for how to extend this once a real (or
 * emulator) Firebase project is available.
 *
 * Run locally against an already-running server:
 *   k6 run backend/load/k6-load-test.js
 *   BASE_URL=http://127.0.0.1:8000 k6 run backend/load/k6-load-test.js
 *
 * The CI workflow (.github/workflows/backend-tests.yml) boots the server
 * itself with a throwaway, locally-generated Firebase service-account JSON
 * (see tests/reporting/ci_helpers/gen_fake_firebase_creds.py) purely so the
 * process can start -- it contains no real secrets and cannot verify a real
 * token, only enough for firebase_admin.initialize_app() to succeed.
 */
import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

const errorRate = new Rate("errors");
const scanDuration = new Trend("scan_analyse_duration", true);
const barcodeDuration = new Trend("scan_barcode_duration", true);

export const options = {
  scenarios: {
    smoke: {
      executor: "constant-vus",
      vus: 1,
      duration: "10s",
      tags: { scenario: "smoke" },
      exec: "smoke",
    },
    baseline_load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "20s", target: 10 }, // ramp to 10 concurrent users
        { duration: "40s", target: 10 }, // hold
        { duration: "10s", target: 0 },  // ramp down
      ],
      startTime: "12s", // run after the smoke scenario finishes
      tags: { scenario: "baseline_load" },
      exec: "baselineLoad",
    },
  },
  thresholds: {
    // These are deliberately conservative for a student/portfolio project
    // running on free-tier infrastructure (Render), not a production SLO.
    http_req_duration: ["p(95)<1500"],
    errors: ["rate<0.01"],
    // /scan/analyse has a real 30/minute rate limit (see routers/scan.py).
    // The baseline_load scenario is expected to hit 429s once a VU crosses
    // that threshold -- that's correct behavior, not a failure. We only
    // fail the build on unexpected 5xx errors, tracked separately below.
  },
};

const SAMPLE_INGREDIENTS = [
  ["water", "salt", "sugar"],
  ["E102", "E621", "palm oil"],
  ["curcumin", "ascorbic acid"],
  ["high fructose corn syrup", "E211"],
];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function smoke() {
  group("health", () => {
    const res = http.get(`${BASE_URL}/health`);
    check(res, {
      "health status is 200": (r) => r.status === 200,
      "health body has status field": (r) => JSON.parse(r.body).status !== undefined,
    });
    errorRate.add(res.status !== 200);
  });

  group("root", () => {
    const res = http.get(`${BASE_URL}/`);
    check(res, { "root status is 200": (r) => r.status === 200 });
    errorRate.add(res.status !== 200);
  });

  sleep(1);
}

export function baselineLoad() {
  group("scan_analyse", () => {
    const payload = JSON.stringify({ ingredients: pick(SAMPLE_INGREDIENTS) });
    const res = http.post(`${BASE_URL}/scan/analyse`, payload, {
      headers: { "Content-Type": "application/json" },
      tags: { name: "POST /scan/analyse" },
    });
    scanDuration.add(res.timings.duration);
    check(res, {
      "scan/analyse is 200 or 429 (rate limited)": (r) => r.status === 200 || r.status === 429,
      "scan/analyse never 5xx": (r) => r.status < 500,
    });
    errorRate.add(res.status >= 500);
  });

  group("scan_barcode_not_found", () => {
    // A barcode guaranteed not to exist on Open Food Facts -- exercises the
    // "not found" path (404) without depending on external API availability
    // for a *successful* lookup, which would make this test flaky.
    const payload = JSON.stringify({ barcode: "0000000000000" });
    const res = http.post(`${BASE_URL}/scan/barcode`, payload, {
      headers: { "Content-Type": "application/json" },
      tags: { name: "POST /scan/barcode" },
    });
    barcodeDuration.add(res.timings.duration);
    check(res, {
      "scan/barcode never 5xx": (r) => r.status < 500,
    });
    errorRate.add(res.status >= 500);
  });

  sleep(Math.random() * 2 + 0.5);
}
