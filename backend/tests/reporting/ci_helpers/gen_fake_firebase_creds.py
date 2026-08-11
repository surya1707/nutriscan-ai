"""
Generates a throwaway "service account" JSON file that lets the live
FastAPI server (uvicorn app.main:app) boot in an ephemeral CI environment,
for k6 / real-HTTP testing.

WHY THIS EXISTS (confirmed by direct testing, not assumed):
app/core/firebase.py calls firebase_admin.initialize_app() unconditionally
at import time UNLESS "pytest" is in sys.modules. Outside pytest -- i.e.
exactly the case of `uvicorn app.main:app` for k6 -- if
FIREBASE_CREDENTIALS_PATH is missing or invalid, the process prints an
error and calls sys.exit(1). Confirmed live: the server does not start at
all without *some* file that looks like a valid service account.

WHAT THIS DOES NOT DO:
This does NOT let you generate a working Firebase ID token, and it does NOT
grant access to any real Firebase project. firebase_admin.initialize_app()
only validates the JSON's shape and builds a local signer from the private
key; it does not contact Firebase at all. Real ID token verification
(auth.verify_id_token) still requires a token signed by an actual Google
Firebase project and would fail with this (or any other) throwaway key.
That's why the k6 load test only targets the endpoints that don't require
a verified token -- see backend/load/k6-load-test.js.

The private key generated here is fresh, random, and thrown away at the end
of the CI job. It is never committed and grants access to nothing.
"""
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate(output_path: str) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    fake_service_account = {
        "type": "service_account",
        "project_id": "ci-ephemeral-fake-project",
        "private_key_id": "ci-fake-key-id",
        "private_key": pem,
        "client_email": "ci-fake@ci-ephemeral-fake-project.iam.gserviceaccount.com",
        "client_id": "000000000000000000000",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": (
            "https://www.googleapis.com/robot/v1/metadata/x509/"
            "ci-fake%40ci-ephemeral-fake-project.iam.gserviceaccount.com"
        ),
        "universe_domain": "googleapis.com",
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fake_service_account, indent=2))
    print(f"Wrote throwaway CI-only Firebase credentials to {path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ci-fake-firebase-creds.json"
    generate(output)
