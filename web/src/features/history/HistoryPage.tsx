import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import { useAuthStore, AuthStatus } from '../../store/authStore';
import type { ScanHistoryResponse } from '../../lib/types';
import { scoreColor } from '../../lib/types';
import { History } from 'lucide-react';

const PAGE_SIZE = 20;

const Skeleton = () => (
  <div className="card" style={{ padding: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
    <div style={{ width: 44, height: 44, borderRadius: 12, backgroundColor: 'var(--color-divider)', animation: 'pulse 1.4s ease-in-out infinite', flexShrink: 0 }} />
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
      <div style={{ height: 16, width: '55%', borderRadius: 6, backgroundColor: 'var(--color-divider)', animation: 'pulse 1.4s ease-in-out infinite' }} />
      <div style={{ height: 12, width: '35%', borderRadius: 6, backgroundColor: 'var(--color-divider)', animation: 'pulse 1.4s ease-in-out infinite' }} />
    </div>
  </div>
);

const ScanCard = ({ scan, onClick }: { scan: ScanHistoryResponse; onClick: () => void }) => {
  const score = scan.health_score ?? 0;
  const color = scoreColor(score);
  const bgColor = score >= 70 ? '#eaf7f0' : score >= 45 ? '#fdf3e0' : '#fde8e6';

  return (
    <div onClick={onClick} className="card card-hover" style={{
      padding: '0.875rem 1rem',
      display: 'flex', alignItems: 'center', gap: '0.875rem',
      cursor: 'pointer', transition: 'opacity 120ms ease',
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12, flexShrink: 0,
        backgroundColor: bgColor,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.125rem', fontWeight: 800, color,
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
          {[
            scan.brand,
            scan.nova_group != null ? `NOVA ${scan.nova_group}` : null,
            new Date(scan.scanned_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }),
          ].filter(Boolean).join(' · ')}
        </p>
      </div>
      <span style={{
        fontSize: 11, fontWeight: 600,
        color, backgroundColor: bgColor,
        borderRadius: 9999,
        padding: '0.25rem 0.625rem', flexShrink: 0,
      }}>
        {score >= 70 ? 'Safe' : score >= 45 ? 'Caution' : 'Flagged'}
      </span>
    </div>
  );
};

export default function HistoryPage() {
  const navigate = useNavigate();
  const { status } = useAuthStore();
  const isGuest = status === AuthStatus.Guest;

  const [items, setItems] = useState<ScanHistoryResponse[]>([]);
  const [loading, setLoading] = useState(!isGuest);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = useCallback(async (off: number, append = false) => {
    if (append) setLoadingMore(true);
    else setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<ScanHistoryResponse[]>(
        `/history?limit=${PAGE_SIZE}&offset=${off}`
      );
      setItems((prev) => append ? [...prev, ...data] : data);
      setHasMore(data.length === PAGE_SIZE);
      setOffset(off + data.length);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message ?? 'Failed to load history.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    if (!isGuest) fetchPage(0);
  }, [isGuest, fetchPage]);

  return (
    <div style={{ padding: '1.5rem 1.25rem', maxWidth: 720, margin: '0 auto' }}>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }`}</style>

      <h1 className="text-headline" style={{ color: 'var(--color-text-primary)', marginBottom: '0.25rem' }}>
        Scan History
      </h1>
      <p className="text-body-md" style={{ color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
        {isGuest ? 'Your past scans' : `All your saved scans, newest first.`}
      </p>

      {isGuest ? (
        <div className="card" style={{ padding: '2.5rem 1.25rem', textAlign: 'center' }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%',
            backgroundColor: 'var(--color-light-green)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 0.875rem',
          }}>
            <History size={26} color="var(--color-medium-green)" />
          </div>
          <p style={{ fontWeight: 600, fontSize: 'var(--text-body-lg)', color: 'var(--color-text-primary)', margin: '0 0 0.375rem' }}>
            Sign in to view history
          </p>
          <p style={{ fontSize: 'var(--text-body-md)', color: 'var(--color-text-secondary)', margin: '0 0 1.25rem' }}>
            Guest scans aren't saved to the cloud.
          </p>
          <button onClick={() => navigate('/login')} className="btn-primary">
            Sign in
          </button>
        </div>
      ) : loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {[...Array(6)].map((_, i) => <Skeleton key={i} />)}
        </div>
      ) : error ? (
        <div style={{
          backgroundColor: '#fff0ef',
          border: '1px solid var(--color-flagged-red)',
          borderRadius: 'var(--radius-card)',
          padding: '1rem',
          color: 'var(--color-flagged-red)',
          fontSize: 'var(--text-body-md)',
          textAlign: 'center',
        }}>
          {error}
          <button onClick={() => fetchPage(0)} className="btn-ghost" style={{ display: 'block', margin: '0.75rem auto 0' }}>
            Retry
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="card" style={{ padding: '2.5rem 1.25rem', textAlign: 'center' }}>
          <p style={{ fontWeight: 600, fontSize: 'var(--text-body-lg)', color: 'var(--color-text-primary)', margin: '0 0 0.375rem' }}>
            No scans yet
          </p>
          <p style={{ fontSize: 'var(--text-body-md)', color: 'var(--color-text-secondary)', margin: '0 0 1rem' }}>
            Start scanning to build up your history.
          </p>
          <button onClick={() => navigate('/scan')} className="btn-primary">
            Scan a product
          </button>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {items.map((scan) => (
              <ScanCard key={scan.id} scan={scan} onClick={() => navigate(`/results/${scan.id}`)} />
            ))}
          </div>

          {hasMore && (
            <button
              id="btn-load-more"
              onClick={() => fetchPage(offset, true)}
              disabled={loadingMore}
              className="btn-ghost"
              style={{ width: '100%', marginTop: '1rem' }}
            >
              {loadingMore ? 'Loading…' : 'Load more'}
            </button>
          )}
        </>
      )}
    </div>
  );
}
