import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AppShell      from './components/layout/AppShell';
import LoginPage     from './features/auth/LoginPage';
import HomePage      from './features/home/HomePage';
import HistoryPage   from './features/history/HistoryPage';
import ProfilePage   from './features/profile/ProfilePage';
import ScanPage      from './features/scan/ScanPage';
import ResultsPage   from './features/scan/ResultsPage';

/**
 * Route map:
 *
 *  /login          → LoginPage         (public)
 *  /               → HomePage          (protected, inside AppShell)
 *  /history        → HistoryPage       (protected, inside AppShell)
 *  /profile        → ProfilePage       (protected, inside AppShell)
 *  /scan           → ScanPage          (protected, inside AppShell)
 *  /results/:id    → ResultsPage       (protected, inside AppShell)
 *  *               → redirect → /      (catch-all)
 */
export default function App() {
  return (
    <Routes>
      {/* ── Public ───────────────────────────────────────────────────────── */}
      <Route path="/login" element={<LoginPage />} />

      {/* ── Protected (wrapped in AppShell) ──────────────────────────────── */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/"            element={<HomePage />}    />
          <Route path="/history"     element={<HistoryPage />} />
          <Route path="/profile"     element={<ProfilePage />} />
          <Route path="/scan"        element={<ScanPage />}    />
          <Route path="/results/:id" element={<ResultsPage />} />
        </Route>
      </Route>

      {/* ── Catch-all ────────────────────────────────────────────────────── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
