import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import { useAuthStore, AuthStatus } from '../../store/authStore';
import type { ScanHistoryResponse, UserProfileResponse } from '../../lib/types';
import { scoreColor } from '../../lib/types';
import { ScanBarcode, User, LayoutGrid, CheckCircle2, AlertTriangle, UserCog, ChevronRight, History, Leaf } from 'lucide-react';

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
  <div className="bg-gradient-premium" style={{
    borderRadius: 20,
    overflow: 'hidden',
    position: 'relative',
    cursor: 'pointer',
    boxShadow: '0 10px 30px -10px rgba(45,74,62,0.4)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  }} onClick={onTap}
     onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
     onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}>
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
        <ScanBarcode size={18} />
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
    <StatCard loading={loading} icon={<LayoutGrid size={20} />} iconColor="var(--color-text-secondary)" value={stats.total.toString()} label="Total scans" />
    <StatCard loading={loading} icon={<CheckCircle2 size={20} />} iconColor="var(--color-safe-green)" value={stats.safe.toString()} label="Safe" />
    <StatCard loading={loading} icon={<AlertTriangle size={20} />} iconColor="var(--color-flagged-red)" value={stats.flagged.toString()} label="Flagged" />
  </div>
);

const PersonalizeBanner = ({ onTap }: { onTap: () => void }) => (
  <div onClick={onTap} className="bg-gradient-accent card-hover" style={{
    borderRadius: 14,
    padding: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    cursor: 'pointer',
    color: '#fff'
  }}>
    <div style={{
      width: 38, height: 38,
      borderRadius: 10,
      backgroundColor: 'rgba(255,255,255,0.2)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <UserCog size={20} color="#fff" />
    </div>
    <div style={{ flex: 1 }}>
      <p style={{ fontWeight: 600, fontSize: 'var(--text-body-md)', color: '#fff', margin: 0 }}>
        Personalize your scans
      </p>
      <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', margin: '0.125rem 0 0', lineHeight: 1.4 }}>
        Add your allergies, conditions and goals for tailored verdicts.
      </p>
    </div>
    <ChevronRight size={18} color="#fff" />
  </div>
);

// ── ScanCard (recent item) ────────────────────────────────────────────────────
const ScanCard = ({ scan, onClick }: { scan: ScanHistoryResponse; onClick: () => void }) => {
  const score = scan.health_score ?? 0;
  const color = scoreColor(score);
  return (
    <div onClick={onClick} className="card card-hover" style={{
      padding: '0.875rem 1rem',
      display: 'flex',
      alignItems: 'center',
      gap: '0.875rem',
      cursor: 'pointer',
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
              <User size={22} />
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
              <Leaf size={26} color="var(--color-medium-green)" />
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
