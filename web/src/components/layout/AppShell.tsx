import React, { useState, useRef, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore, AuthStatus } from '../../store/authStore';
import { Leaf, Clock, User, ChevronDown, LogOut, Menu, LogIn } from 'lucide-react';

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
            {isGuest ? <User size={20} /> : initial}
          </div>
        )}
        <ChevronDown size={16} />
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {isGuest ? <LogIn size={16} /> : <LogOut size={16} />}
              <span>{isGuest ? 'Sign In' : 'Sign Out'}</span>
            </div>
          </button>
        </div>
      )}
    </div>
  );
};

// ── AppShell ──────────────────────────────────────────────────────────────────

const NAV_ITEMS: NavItemProps[] = [
  { to: '/',        label: 'Home',    icon: (a) => <Leaf size={22} fill={a ? 'currentColor' : 'none'} strokeWidth={a ? 2 : 1.5} /> },
  { to: '/history', label: 'History', icon: (a) => <Clock size={22} fill={a ? 'currentColor' : 'none'} strokeWidth={a ? 2 : 1.5} /> },
  { to: '/profile', label: 'Profile', icon: (a) => <User size={22} fill={a ? 'currentColor' : 'none'} strokeWidth={a ? 2 : 1.5} /> },
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
              <Leaf size={20} color="var(--color-medium-green)" />
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
            <Menu size={24} />
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
                <Leaf size={20} color="var(--color-medium-green)" />
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
