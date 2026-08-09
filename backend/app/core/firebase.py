import os
import sys
import firebase_admin
from firebase_admin import credentials
from .config import settings

def init_firebase():
    if "pytest" in sys.modules:
        return
        
        
    if not settings.FIREBASE_CREDENTIALS_PATH or not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        print(
            "ERROR: Firebase credentials file not found at "
            f"'{settings.FIREBASE_CREDENTIALS_PATH}'.\n"
            "Please download the service account JSON from the Firebase console "
            "and update FIREBASE_CREDENTIALS_PATH in your .env file.",
            file=sys.stderr
        )
        sys.exit(1)

    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

init_firebase()
