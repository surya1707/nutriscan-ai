import { create } from 'zustand';
import type { User as FirebaseUser } from 'firebase/auth';
import {
  onAuthStateChanged,
  signOut,
  signInWithPopup,
  GoogleAuthProvider,
} from 'firebase/auth';
import { auth } from '../lib/firebase';

const GUEST_KEY = 'nutriscan_is_guest';

export const AuthStatus = {
  Loading:          'loading',
  Authenticated:    'authenticated',
  Guest:            'guest',
  Unauthenticated:  'unauthenticated',
} as const;
export type AuthStatus = typeof AuthStatus[keyof typeof AuthStatus];

interface AuthState {
  status: AuthStatus;
  /** Authenticated Firebase user, or null. */
  user: FirebaseUser | null;
  /** Current Firebase ID token (refreshed automatically by the listener). */
  idToken: string | null;
  /** True while the initial Firebase auth-state check is in progress. */
  isLoading: boolean;
  /** Guest flag — local-only mode, no backend sync. Persisted in localStorage. */
  isGuest: boolean;

  // Actions
  setUser: (user: FirebaseUser, idToken: string) => void;
  clearUser: () => void;
  continueAsGuest: () => void;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: AuthStatus.Loading,
  user: null,
  idToken: null,
  isLoading: true,
  isGuest: false,

  setUser: (user, idToken) =>
    set({
      status: AuthStatus.Authenticated,
      user,
      idToken,
      isLoading: false,
      isGuest: false,
    }),

  clearUser: () => {
    // Preserve guest flag if already guest (sign-in attempt cancelled)
    const isGuest = get().isGuest;
    set({
      status: isGuest ? AuthStatus.Guest : AuthStatus.Unauthenticated,
      user: null,
      idToken: null,
      isLoading: false,
    });
  },

  continueAsGuest: () => {
    localStorage.setItem(GUEST_KEY, 'true');
    set({ status: AuthStatus.Guest, isGuest: true, isLoading: false });
  },

  signInWithGoogle: async () => {
    set({ isLoading: true });
    try {
      const provider = new GoogleAuthProvider();
      const credential = await signInWithPopup(auth, provider);
      const idToken = await credential.user.getIdToken();
      localStorage.removeItem(GUEST_KEY);
      set({
        status: AuthStatus.Authenticated,
        user: credential.user,
        idToken,
        isLoading: false,
        isGuest: false,
      });
    } catch (err) {
      // Popup cancelled or error — revert to previous state
      set({ isLoading: false });
      throw err;
    }
  },

  logout: async () => {
    await signOut(auth);
    localStorage.removeItem(GUEST_KEY);
    set({
      status: AuthStatus.Unauthenticated,
      user: null,
      idToken: null,
      isLoading: false,
      isGuest: false,
    });
  },
}));

/**
 * Bootstrap the Firebase auth listener once at app start.
 * Reads the guest flag from localStorage immediately to avoid a flash
 * of the login screen for returning guests.
 */
export function bootstrapAuth(): () => void {
  // Hydrate guest status synchronously before Firebase resolves
  const isGuest = localStorage.getItem(GUEST_KEY) === 'true';
  if (isGuest) {
    useAuthStore.getState().continueAsGuest();
  }

  return onAuthStateChanged(auth, async (firebaseUser) => {
    if (firebaseUser) {
      const idToken = await firebaseUser.getIdToken();
      useAuthStore.getState().setUser(firebaseUser, idToken);
    } else {
      useAuthStore.getState().clearUser();
    }
  });
}
