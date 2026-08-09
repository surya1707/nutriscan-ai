import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { sendSignInLinkToEmail } from 'firebase/auth';
import { auth } from '../../lib/firebase';
import { useAuthStore, AuthStatus } from '../../store/authStore';

// ── Inline Google "G" SVG (no external icon lib needed) ──────────────────────
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z" />
    <path fill="#FF3D00" d="m6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z" />
    <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z" />
    <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z" />
  </svg>
);

export default function LoginPage() {
  const navigate = useNavigate();
  const { status, signInWithGoogle, continueAsGuest } = useAuthStore();

  const [showEmail, setShowEmail] = useState(false);
  const [email, setEmail] = useState('');
  const [emailSent, setEmailSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect if already authenticated or guest
  useEffect(() => {
    if (status === AuthStatus.Authenticated || status === AuthStatus.Guest) {
      navigate('/', { replace: true });
    }
  }, [status, navigate]);

  const handleGoogle = async () => {
    setError(null);
    setIsLoading(true);
    try {
      await signInWithGoogle();
      // navigation handled by useEffect
    } catch (err: unknown) {
      const e = err as { code?: string; message?: string };
      if (e.code !== 'auth/popup-closed-by-user') {
        setError(e.message ?? 'Sign-in failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmail = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await sendSignInLinkToEmail(auth, email, {
        url: `${window.location.origin}/login`,
        handleCodeInApp: true,
      });
      localStorage.setItem('nutriscan_email_for_signin', email);
      setEmailSent(true);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message ?? 'Failed to send link. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuest = async () => {
    setError(null);
    setIsLoading(true);
    await continueAsGuest();
    // navigation handled by useEffect
    setIsLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-cream)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0,
      }}>
        {/* Brand icon */}
        <div style={{
          width: 72,
          height: 72,
          borderRadius: '50%',
          backgroundColor: 'var(--color-light-green)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1.25rem',
        }}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M17 8C8 10 5.9 16.17 3.82 19.88C3.19 21.02 4.14 22 5.37 22C5.79 22 6.22 21.84 6.52 21.54C9.35 18.67 11 15.03 12.53 11.4C13.32 12.03 14.04 12.73 14.71 13.48L17 8Z" fill="var(--color-dark-green)"/>
            <path d="M19 3C19 3 15 5 14 10C16 9.5 19 7 21 5C20.5 4.5 19 3 19 3Z" fill="var(--color-medium-green)"/>
          </svg>
        </div>

        {/* Heading */}
        <h1 style={{
          fontSize: 'var(--text-display)',
          fontWeight: 700,
          color: 'var(--color-dark-green)',
          margin: 0,
          textAlign: 'center',
          lineHeight: 1.15,
        }}>
          NutriScan AI
        </h1>
        <p style={{
          fontSize: 'var(--text-body-lg)',
          color: 'var(--color-text-secondary)',
          marginTop: '0.5rem',
          marginBottom: '2.5rem',
          textAlign: 'center',
        }}>
          Sync your scans across devices
        </p>

        {/* Error message */}
        {error && (
          <div style={{
            width: '100%',
            backgroundColor: '#fff0ef',
            border: '1px solid var(--color-flagged-red)',
            borderRadius: 'var(--radius-card)',
            padding: '0.75rem 1rem',
            marginBottom: '1rem',
            color: 'var(--color-flagged-red)',
            fontSize: 'var(--text-body-md)',
          }}>
            {error}
          </div>
        )}

        {/* Email sent confirmation */}
        {emailSent && (
          <div style={{
            width: '100%',
            backgroundColor: '#eaf7f0',
            border: '1px solid var(--color-safe-green)',
            borderRadius: 'var(--radius-card)',
            padding: '0.75rem 1rem',
            marginBottom: '1rem',
            color: 'var(--color-safe-green)',
            fontSize: 'var(--text-body-md)',
          }}>
            ✓ Sign-in link sent to <strong>{email}</strong>. Check your inbox.
          </div>
        )}

        {/* Buttons */}
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Google */}
          <button
            id="btn-google-signin"
            onClick={handleGoogle}
            disabled={isLoading}
            className="btn-primary"
            style={{ width: '100%', gap: '0.625rem' }}
          >
            <GoogleIcon />
            Continue with Google
          </button>

          {/* Email */}
          {!showEmail ? (
            <button
              id="btn-email-signin"
              onClick={() => setShowEmail(true)}
              className="btn-ghost"
              style={{ width: '100%' }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              Continue with Email
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                id="input-email"
                type="email"
                className="input"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleEmail()}
                style={{ flex: 1 }}
                autoFocus
              />
              <button
                id="btn-email-send"
                onClick={handleEmail}
                disabled={isLoading}
                className="btn-primary"
                style={{ paddingLeft: '1rem', paddingRight: '1rem', flexShrink: 0 }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Divider */}
        <div style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          margin: '1.25rem 0',
        }}>
          <hr className="divider" style={{ flex: 1 }} />
          <span className="text-label" style={{ color: 'var(--color-text-muted)' }}>or</span>
          <hr className="divider" style={{ flex: 1 }} />
        </div>

        {/* Guest */}
        <button
          id="btn-guest"
          onClick={handleGuest}
          disabled={isLoading}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--text-body-md)',
            textDecoration: 'underline',
            padding: '0.25rem',
          }}
        >
          Continue as Guest
        </button>

        <p style={{
          marginTop: '0.625rem',
          fontSize: 'var(--text-label)',
          color: 'var(--color-text-muted)',
          textAlign: 'center',
        }}>
          Guest mode is local-only · scans won't sync
        </p>
      </div>
    </div>
  );
}
