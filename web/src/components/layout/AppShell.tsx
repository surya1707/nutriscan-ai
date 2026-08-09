import React, { useState, useRef, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore, AuthStatus } from '../../store/authStore';

// ── Icon components (inline SVG, matching mobile/lib/shared/widgets/main_shell.dart) ─

const EcoIcon = ({ filled }: { filled?: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke={filled ? 'none' : 'currentColor'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17 8C8 10 5.9 16.17 3.82 19.88C3.19 21.02 4.14 22 5.37 22C5.79 22 6.22 21.84 6.52 21.54C9.35 18.67 11 15.03 12.53 11.4C13.32 12.03 14.04 12.73 14.71 13.48L17 8Z"/>
    <path d="M19 3C19 3 15 5 14 10C16 9.5 19 7 21 5C20.5 4.5 19 3 19 3Z"/>
  </svg>
);

const HistoryIcon = ({ filled }: { filled?: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={filled ? '2.2' : '1.8'} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
    <path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>
  </svg>
);

const PersonIcon = ({ filled }: { filled?: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke={filled ? 'none' : 'currentColor'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);

const ChevronDown = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m6 9 6 6 6-6"/>
  </svg>
);

// ── NavItem ───────────────────────────────────────────────────────────────────

interface NavItemProps {
  to: string;
  label: string;
  icon: (active: boolean) => React.ReactElement;
  vertical?: boolean;
}

const NavItem = ({ to, label, icon, vertical = true }: NavItemProps) => (
  <NavLink
    to={to}
    end={to === '/'}
    style={({ isActive }) => ({
      display: 'flex',
      flexDirection: vertical ? 'column' : 'row',
      alignItems: 'center',
      gap: vertical ? '0.25rem' : '0.625rem',
      padding: vertical ? '0.5rem 0' : '0.625rem 1rem',
      borderRadius: vertical ? 0 : '10px',
      color: isActive ? 'var(--color-nav-active)' : 'var(--color-nav-inactive)',
      textDecoration: 'none',
      fontSize: vertical ? 'var(--text-label)' : 'var(--text-body-md)',
      fontWeight: isActive ? 600 : 400,
      transition: 'color 120ms ease, background-color 120ms ease',
      backgroundColor: isActive && !vertical ? 'var(--color-light-green)' : 'transparent',
    })}
  >
    {({ isActive }) => (
      <>
        {icon(isActive)}
        <span>{label}</span>
      </>
    )}
  </NavLink>
);

// ── Avatar / dropdown ─────────────────────────────────────────────────────────

const UserAvatar = () => {
  const { user, status, logout } = useAuthStore();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const initial = user?.displayName?.[0]?.toUpperCase()
    ?? user?.email?.[0]?.toUpperCase()
    ?? '?';

  const isGuest = status === AuthStatus.Guest;

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        id="btn-user-avatar"
        onClick={() => setOpen((v) => !v)}
        aria-label="User menu"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0.25rem',
        }}
      >
        {user?.photoURL ? (
          <img
            src={user.photoURL}
            alt={user.displayName ?? 'User'}
            width={36} height={36}
            style={{ borderRadius: '50%', objectFit: 'cover' }}
          />
        ) : (
          <div style={{
            width: 36, height: 36,
            borderRadius: '50%',
            backgroundColor: 'var(--color-light-green)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--color-medium-green)',
            fontWeight: 600,
            fontSize: '0.9375rem',
          }}>
            {isGuest ? <PersonIcon /> : initial}
          </div>
        )}
        <ChevronDown />
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: '0.5rem',
          backgroundColor: 'var(--color-card-bg)',
          border: '1px solid var(--color-divider)',
          borderRadius: 'var(--radius-card)',
          minWidth: 160,
          zIndex: 100,
          overflow: 'hidden',
        }}>
          {!isGuest && (
            <button
              onClick={() => { setOpen(false); navigate('/profile'); }}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '0.75rem 1rem', background: 'none', border: 'none',
                cursor: 'pointer', fontSize: 'var(--text-body-md)',
                color: 'var(--color-text-primary)',
              }}
            >
              Profile
            </button>
          )}
          {!isGuest && <hr className="divider" />}
          <button
            id="btn-signout"
            onClick={async () => { setOpen(false); await logout(); navigate('/login'); }}
            style={{
              display: 'block', width: '100%', textAlign: 'left',
              padding: '0.75rem 1rem', background: 'none', border: 'none',
              cursor: 'pointer', fontSize: 'var(--text-body-md)',
              color: isGuest ? 'var(--color-text-secondary)' : 'var(--color-flagged-red)',
            }}
          >
            {isGuest ? 'Sign In' : 'Sign Out'}
          </button>
        </div>
      )}
    </div>
  );
};

// ── AppShell ──────────────────────────────────────────────────────────────────

const NAV_ITEMS: NavItemProps[] = [
  { to: '/',        label: 'Home',    icon: (a) => <EcoIcon filled={a} /> },
  { to: '/history', label: 'History', icon: (a) => <HistoryIcon filled={a} /> },
  { to: '/profile', label: 'Profile', icon: (a) => <PersonIcon filled={a} /> },
];

export default function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', backgroundColor: 'var(--color-cream)' }}>

      {/* ── Desktop sidebar (≥1024px) ──────────────────────────────────────── */}
      <aside style={{
        width: 220,
        flexShrink: 0,
        display: 'none', // hidden by default, shown via media query via class
        borderRight: '1px solid var(--color-divider)',
        backgroundColor: 'var(--color-cream)',
        flexDirection: 'column',
        padding: '1.5rem 0',
      }} className="sidebar-desktop">

        {/* Brand */}
        <div style={{ padding: '0 1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: 32, height: 32,
              borderRadius: 10,
              backgroundColor: 'var(--color-light-green)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <EcoIcon />
            </div>
            <span style={{
              fontSize: 'var(--text-title)',
              fontWeight: 700,
              color: 'var(--color-dark-green)',
              letterSpacing: '-0.01em',
            }}>NutriScan</span>
          </div>
        </div>

        <hr className="divider" style={{ marginBottom: '0.75rem' }} />

        {/* Nav */}
        <nav style={{ flex: 1, padding: '0 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
          {NAV_ITEMS.map((item) => (
            <NavItem key={item.to} {...item} vertical={false} />
          ))}
        </nav>
      </aside>

      {/* ── Main content area ───────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Top bar (visible on mobile + tablet) */}
        <header style={{
          height: 56,
          borderBottom: '1px solid var(--color-divider)',
          backgroundColor: 'var(--color-cream)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 1.25rem',
          flexShrink: 0,
        }} className="topbar">
          {/* Hamburger (tablet only, hidden on desktop) */}
          <button
            id="btn-hamburger"
            onClick={() => setDrawerOpen(true)}
            className="hamburger-btn"
            aria-label="Open navigation"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '0.25rem', color: 'var(--color-text-primary)',
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <line x1="4" y1="6" x2="20" y2="6"/>
              <line x1="4" y1="12" x2="20" y2="12"/>
              <line x1="4" y1="18" x2="20" y2="18"/>
            </svg>
          </button>

          <span style={{
            fontWeight: 700,
            color: 'var(--color-dark-green)',
            fontSize: 'var(--text-title)',
          }} className="topbar-brand">
            NutriScan
          </span>

          <UserAvatar />
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflowY: 'auto' }}>
          <Outlet />
        </main>

        {/* ── Bottom tab bar (<768px) ─────────────────────────────────────── */}
        <nav style={{
          borderTop: '1px solid var(--color-divider)',
          backgroundColor: 'var(--color-cream)',
          display: 'flex',
          justifyContent: 'space-around',
          padding: '0.25rem 0 env(safe-area-inset-bottom, 0)',
          flexShrink: 0,
        }} className="bottom-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <NavItem key={item.to} {...item} vertical={true} />
          ))}
        </nav>
      </div>

      {/* ── Drawer overlay (tablet, 768–1023px) ────────────────────────────── */}
      {drawerOpen && (
        <>
          <div
            onClick={() => setDrawerOpen(false)}
            style={{
              position: 'fixed', inset: 0,
              backgroundColor: 'rgba(0,0,0,0.3)',
              zIndex: 200,
            }}
          />
          <div style={{
            position: 'fixed', top: 0, left: 0, bottom: 0,
            width: 260,
            backgroundColor: 'var(--color-cream)',
            borderRight: '1px solid var(--color-divider)',
            zIndex: 201,
            padding: '1.5rem 0.75rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.125rem',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0 0.25rem', marginBottom: '1rem',
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: 10,
                backgroundColor: 'var(--color-light-green)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <EcoIcon />
              </div>
              <span style={{ fontWeight: 700, color: 'var(--color-dark-green)', fontSize: 'var(--text-title)' }}>
                NutriScan
              </span>
            </div>
            <hr className="divider" style={{ marginBottom: '0.75rem' }} />
            {NAV_ITEMS.map((item) => (
              <div key={item.to} onClick={() => setDrawerOpen(false)}>
                <NavItem {...item} vertical={false} />
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Responsive CSS ─────────────────────────────────────────────────── */}
      <style>{`
        .sidebar-desktop { display: none !important; }
        .bottom-nav      { display: flex !important; }
        .topbar          { display: flex !important; }
        .hamburger-btn   { display: flex !important; }
        .topbar-brand    { display: block !important; }

        @media (min-width: 768px) {
          .bottom-nav    { display: none !important; }
          .hamburger-btn { display: flex !important; }
        }

        @media (min-width: 1024px) {
          .sidebar-desktop { display: flex !important; }
          .hamburger-btn   { display: none !important; }
          .topbar-brand    { display: none !important; }
          .topbar          {
            border-bottom: 1px solid var(--color-divider);
            display: flex !important;
          }
        }
      `}</style>
    </div>
  );
}
