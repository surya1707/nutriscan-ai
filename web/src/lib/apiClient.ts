import axios from 'axios';
import { useAuthStore } from '../store/authStore';

/**
 * Pre-configured Axios instance for the NutriScan FastAPI backend.
 * Base URL is set via VITE_API_URL (see .env.example).
 *
 * Request interceptor automatically attaches the Firebase ID token
 * from the Zustand auth store when available.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15_000,
});

// ── Auth token injection ──────────────────────────────────────────────────────
apiClient.interceptors.request.use((config) => {
  const idToken = useAuthStore.getState().idToken;
  if (idToken) {
    config.headers.Authorization = `Bearer ${idToken}`;
  }
  return config;
});

// ── Response error normaliser ─────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Let callers handle domain-specific errors; just re-throw as-is.
    return Promise.reject(error);
  }
);
