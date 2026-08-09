import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import { useAuthStore, AuthStatus } from '../../store/authStore';
import type { ScanHistoryResponse, UserProfileResponse } from '../../lib/types';
import { scoreColor } from '../../lib/types';

// ── Skeleton block ────────────────────────────────────────────────────────────
const Skeleton = ({ w = '100%', h = 20, r = 8 }: { w?: string | number; h?: number; r?: number }) => (
  <div style={{
    width: w, height: h,
    borderRadius: r,
    backgroundColor: 'var(--color-divider)',
    animation: 'pulse 1.4s ease-in-out infinite',
  }} />
);

// ── HeroScanCard ──────────────────────────────────────────────────────────────
const HeroScanCard = ({ onTap }: { onTap: () => void }) => (
  <div style={{
    backgroundColor: 'var(--color-dark-green)',
    borderRadius: 20,
    overflow: 'hidden',
    position: 'relative',
    cursor: 'pointer',
  }} onClick={onTap}>
    {/* Decorative circle */}
    <div style={{
      position: 'absolute', right: -20, bottom: -20,
      width: 140, height: 140,
      borderRadius: '50%',
      backgroundColor: 'var(--color-medium-green)',
      opacity: 0.15,
    }} />
    <div style={{ padding: '1.5rem' }}>
      <p className="text-label" style={{ color: 'rgba(255,255,255,0.54)', marginBottom: '0.625rem' }}>
        SCAN INGREDIENTS
      </p>
      <h2 style={{
        fontSize: 'clamp(1.5rem, 4vw, 1.875rem)',
        fontWeight: 700,
        color: '#fff',
        lineHeight: 1.15,
        margin: '0 0 0.75rem',
      }}>
        Decode what<br />you eat.
      </h2>
      <p style={{
        fontSize: 'var(--text-body-md)',
        color: 'rgba(255,255,255,0.7)',
        lineHeight: 1.55,
        margin: '0 0 1.25rem',
      }}>
        Enter a barcode or paste ingredients. We translate E-codes,
        classify NOVA tier, and flag items matched to your profile.
      </p>
      <button style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.625rem 1.125rem',
        backgroundColor: 'rgba(255,255,255,0.15)',
        border: '1px solid rgba(255,255,255,0.25)',
        borderRadius: 30,
        color: '#fff',
        fontSize: 'var(--text-body-md)',
        fontWeight: 600,
        cursor: 'pointer',
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>
          <path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
        </svg>
        Start Scan
      </button>
    </div>
  </div>
);

// ── StatsRow ──────────────────────────────────────────────────────────────────
interface Stats { total: number; safe: number; flagged: number }

const StatCard = ({ icon, iconColor, value, label, loading }: {
  icon: React.ReactNode; iconColor: string; value: string; label: string; loading?: boolean;
}) => (
  <div className="card" style={{
    flex: 1,
    padding: '0.875rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  }}>
    {loading ? (
      <>
        <Skeleton h={22} w={22} r={4} />
        <Skeleton h={26} w={48} r={4} />
        <Skeleton h={16} w="70%" r={4} />
      </>
    ) : (
      <>
        <span style={{ color: iconColor }}>{icon}</span>
        <span style={{ fontSize: '1.375rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          {value}
        </span>
        <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
          {label}
        </span>
      </>
    )}
  </div>
);

const StatsRow = ({ stats, loading }: { stats: Stats; loading: boolean }) => (
  <div style={{ display: 'flex', gap: '0.625rem' }}>
    <StatCard loading={loading} icon={
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
        <rect x="2" y="3" width="6" height="6" rx="1"/><rect x="9" y="3" width="6" height="6" rx="1"/>
        <rect x="16" y="3" width="6" height="6" rx="1"/><rect x="2" y="12" width="6" height="6" rx="1"/>
        <rect x="9" y="12" width="6" height="6" rx="1"/><rect x="16" y="12" width="6" height="6" rx="1"/>
      </svg>
    } iconColor="var(--color-text-secondary)" value={stats.total.toString()} label="Total scans" />
    <StatCard loading={loading} icon={
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4" stroke="white" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    } iconColor="var(--color-safe-green)" value={stats.safe.toString()} label="Safe" />
    <StatCard loading={loading} icon={
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13" stroke="white" strokeWidth="2" strokeLinecap="round"/>
        <line x1="12" y1="17" x2="12.01" y2="17" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      </svg>
    } iconColor="var(--color-flagged-red)" value={stats.flagged.toString()} label="Flagged" />
  </div>
);

// ── PersonalizeBanner ─────────────────────────────────────────────────────────
const PersonalizeBanner = ({ onTap }: { onTap: () => void }) => (
  <div onClick={onTap} style={{
    backgroundColor: 'var(--color-light-green)',
    borderRadius: 14,
    padding: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    cursor: 'pointer',
  }}>
    <div style={{
      width: 38, height: 38,
      borderRadius: 10,
      backgroundColor: 'rgba(255,255,255,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-dark-green)" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    </div>
    <div style={{ flex: 1 }}>
      <p style={{ fontWeight: 600, fontSize: 'var(--text-body-md)', color: 'var(--color-dark-green)', margin: 0 }}>
        Personalize your scans
      </p>
      <p style={{ fontSize: 12, color: 'var(--color-medium-green)', margin: '0.125rem 0 0', lineHeight: 1.4 }}>
        Add your allergies, conditions and goals for tailored verdicts.
      </p>
    </div>
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-medium-green)" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="m9 18 6-6-6-6"/>
    </svg>
  </div>
);

// ── ScanCard (recent item) ────────────────────────────────────────────────────
const ScanCard = ({ scan, onClick }: { scan: ScanHistoryResponse; onClick: () => void }) => {
  const score = scan.health_score ?? 0;
  const color = scoreColor(score);
  return (
    <div onClick={onClick} className="card" style={{
      padding: '0.875rem 1rem',
      display: 'flex',
      alignItems: 'center',
      gap: '0.875rem',
      cursor: 'pointer',
      transition: 'opacity 120ms ease',
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12, flexShrink: 0,
        backgroundColor: score >= 70 ? '#eaf7f0' : score >= 45 ? '#fdf3e0' : '#fde8e6',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.25rem', fontWeight: 800, color,
      }}>
        {score}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{
          fontWeight: 600, fontSize: 'var(--text-body-md)',
          color: 'var(--color-text-primary)',
          margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {scan.product_name || 'Unknown product'}
        </p>
        <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0.125rem 0 0' }}>
          {scan.brand ?? ''}{scan.brand && scan.nova_group ? ' · ' : ''}
          {scan.nova_group != null ? `NOVA ${scan.nova_group}` : ''}
          {' · '}
          {new Date(scan.scanned_at).toLocaleDateString()}
        </p>
      </div>
      <span style={{
        fontSize: 11, fontWeight: 600,
        color, padding: '0.25rem 0.625rem',
        backgroundColor: score >= 70 ? '#eaf7f0' : score >= 45 ? '#fdf3e0' : '#fde8e6',
        borderRadius: 9999, flexShrink: 0,
      }}>
        {score >= 70 ? 'Safe' : score >= 45 ? 'Caution' : 'Flagged'}
      </span>
    </div>
  );
};

// ── HomePage ──────────────────────────────────────────────────────────────────
export default function HomePage() {
  const navigate = useNavigate();
  const { user, status } = useAuthStore();
  const isGuest = status === AuthStatus.Guest;

  const [history, setHistory] = useState<ScanHistoryResponse[]>([]);
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(!isGuest);
  const [loadingProfile, setLoadingProfile] = useState(!isGuest);

  useEffect(() => {
    if (isGuest) return;

    // Fetch history (used for stats + recent scans)
    apiClient.get<ScanHistoryResponse[]>('/history?limit=100')
      .then((r) => setHistory(r.data))
      .catch(() => {})
      .finally(() => setLoadingHistory(false));

    // Fetch profile (for personalize banner check)
    apiClient.get<UserProfileResponse>('/users/me')
      .then((r) => setProfile(r.data))
      .catch(() => {})
      .finally(() => setLoadingProfile(false));
  }, [isGuest]);

  const stats: Stats = {
    total:   history.length,
    safe:    history.filter((h) => (h.health_score ?? 0) >= 70).length,
    flagged: history.filter((h) => (h.health_score ?? 0) < 45).length,
  };

  const recentScans = history.slice(0, 5);
  const isProfileIncomplete =
    !loadingProfile && profile != null &&
    (profile.allergies?.length === 0 || !profile.allergies) &&
    (profile.conditions?.length === 0 || !profile.conditions) &&
    (profile.goals?.length === 0 || !profile.goals);

  const displayName = user?.displayName?.split(' ')[0] ?? (isGuest ? 'Guest' : 'there');

  return (
    <div style={{ padding: '1.5rem 1.25rem', maxWidth: 720, margin: '0 auto' }}>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }`}</style>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <p className="text-label" style={{ color: 'var(--color-medium-green)', marginBottom: '0.25rem' }}>
            NUTRISCAN AI
          </p>
          <h1 style={{
            fontSize: 'clamp(1.75rem, 5vw, 2rem)',
            fontWeight: 700, color: 'var(--color-text-primary)',
            margin: 0, lineHeight: 1.15,
          }}>
            Eat with<br />intelligence.
          </h1>
        </div>
        <div style={{ textAlign: 'center' }}>
          {user?.photoURL ? (
            <img src={user.photoURL} alt="" width={44} height={44}
              style={{ borderRadius: '50%', objectFit: 'cover' }} />
          ) : (
            <div style={{
              width: 44, height: 44, borderRadius: '50%',
              backgroundColor: 'var(--color-light-green)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--color-medium-green)',
            }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
          )}
          <p style={{ fontSize: 12, color: 'var(--color-medium-green)', fontWeight: 600, margin: '0.25rem 0 0' }}>
            {displayName}
          </p>
        </div>
      </div>

      {/* ── Hero scan card ─────────────────────────────────────────────────── */}
      <HeroScanCard onTap={() => navigate('/scan')} />

      {/* ── Stats ──────────────────────────────────────────────────────────── */}
      <div style={{ margin: '1rem 0' }}>
        {isGuest ? (
          <div className="card" style={{
            padding: '1rem', textAlign: 'center',
            color: 'var(--color-text-muted)', fontSize: 'var(--text-body-md)',
          }}>
            Sign in to track your scan statistics
          </div>
        ) : (
          <StatsRow stats={stats} loading={loadingHistory} />
        )}
      </div>

      {/* ── Personalize banner ─────────────────────────────────────────────── */}
      {!isGuest && isProfileIncomplete && (
        <div style={{ marginBottom: '1rem' }}>
          <PersonalizeBanner onTap={() => navigate('/profile')} />
        </div>
      )}

      {/* ── Recent scans ───────────────────────────────────────────────────── */}
      <div>
        <p className="text-title" style={{ color: 'var(--color-text-primary)', marginBottom: '0.75rem' }}>
          Recent scans
        </p>

        {isGuest ? (
          <div className="card" style={{
            padding: '2.5rem 1.25rem',
            textAlign: 'center',
          }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              backgroundColor: 'var(--color-light-green)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 0.875rem',
            }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--color-medium-green)" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
                <path d="M17 8C8 10 5.9 16.17 3.82 19.88C3.19 21.02 4.14 22 5.37 22C5.79 22 6.22 21.84 6.52 21.54C9.35 18.67 11 15.03 12.53 11.4C13.32 12.03 14.04 12.73 14.71 13.48L17 8Z"/>
              </svg>
            </div>
            <p style={{ fontWeight: 600, fontSize: 'var(--text-body-lg)', color: 'var(--color-text-primary)', margin: '0 0 0.375rem' }}>
              Sign in to see your history
            </p>
            <p style={{ fontSize: 'var(--text-body-md)', color: 'var(--color-text-secondary)', margin: 0 }}>
              Guest scans aren't saved across sessions.
            </p>
          </div>
        ) : loadingHistory ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card" style={{ padding: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
                <Skeleton w={44} h={44} r={12} />
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                  <Skeleton h={16} w="60%" />
                  <Skeleton h={12} w="40%" />
                </div>
              </div>
            ))}
          </div>
        ) : recentScans.length === 0 ? (
          <div className="card" style={{
            padding: '2.5rem 1.25rem', textAlign: 'center',
          }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              backgroundColor: 'var(--color-light-green)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 0.875rem',
            }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--color-medium-green)" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
                <path d="M17 8C8 10 5.9 16.17 3.82 19.88C3.19 21.02 4.14 22 5.37 22C5.79 22 6.22 21.84 6.52 21.54C9.35 18.67 11 15.03 12.53 11.4C13.32 12.03 14.04 12.73 14.71 13.48L17 8Z"/>
              </svg>
            </div>
            <p style={{ fontWeight: 600, fontSize: 'var(--text-body-lg)', color: 'var(--color-text-primary)', margin: '0 0 0.375rem' }}>
              No scans yet
            </p>
            <p style={{ fontSize: 'var(--text-body-md)', color: 'var(--color-text-secondary)', margin: '0 0 1rem' }}>
              Tap "Start Scan" to capture your first ingredient label.
            </p>
            <button onClick={() => navigate('/scan')} className="btn-primary" style={{ margin: '0 auto' }}>
              Start your first scan
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentScans.map((scan) => (
              <ScanCard key={scan.id} scan={scan} onClick={() => navigate(`/results/${scan.id}`)} />
            ))}
            {history.length > 5 && (
              <button onClick={() => navigate('/history')} className="btn-ghost" style={{ width: '100%', marginTop: '0.25rem' }}>
                View all {history.length} scans
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
