import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore, AuthStatus } from '../store/authStore';

/**
 * Wraps protected routes.
 *
 * - Loading  → minimal loading indicator (prevents /login flash)
 * - Guest    → allowed through (local-only mode)
 * - Authed   → allowed through
 * - Other    → redirect to /login
 */
const ProtectedRoute = () => {
  const { status } = useAuthStore();

  if (status === AuthStatus.Loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'var(--color-cream)',
      }}>
        <div style={{
          width: 32,
          height: 32,
          border: '3px solid var(--color-light-green)',
          borderTopColor: 'var(--color-dark-green)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (status === AuthStatus.Authenticated || status === AuthStatus.Guest) {
    return <Outlet />;
  }

  return <Navigate to="/login" replace />;
};

export default ProtectedRoute;
