import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

/**
 * Firebase JS SDK — Web configuration.
 * Env var names match the fields in:
 *   mobile/lib/firebase_options.dart.example  →  FirebaseOptions.web
 *
 * Copy web/.env.example to web/.env.local and fill in real values.
 */
const firebaseConfig = {
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID,
};

export const firebaseApp = initializeApp(firebaseConfig);
export const auth = getAuth(firebaseApp);
