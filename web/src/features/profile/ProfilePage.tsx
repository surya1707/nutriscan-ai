import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import { useAuthStore, AuthStatus } from '../../store/authStore';
import type { UserProfileResponse, UserProfileUpdateRequest } from '../../lib/types';

// ── Exact lists from mobile/lib/features/profile/screens/profile_screen.dart ─
const ALLERGIES = [
  'Peanuts', 'Tree Nuts', 'Dairy', 'Eggs', 'Soy',
  'Wheat / Gluten', 'Fish', 'Shellfish', 'Sesame', 'Mustard', 'Sulfites', 'Corn',
];
const CONDITIONS = [
  'Diabetes', 'Hypertension', 'High Cholesterol', 'Celiac Disease',
  'IBS', 'Kidney Disease', 'PCOS', 'Heart Disease',
];
const GOALS = [
  'Vegan', 'Vegetarian', 'Keto', 'Low Sodium', 'Low Sugar',
  'High Protein', 'Whole Foods', 'Halal', 'Kosher', 'Gluten-Free',
];

// ── Toast ─────────────────────────────────────────────────────────────────────
const Toast = ({ msg, type }: { msg: string; type: 'success' | 'error' }) => (
  <div style={{
    position: 'fixed',
    bottom: '1.5rem',
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: type === 'success' ? 'var(--color-safe-green)' : 'var(--color-flagged-red)',
    color: '#fff',
    padding: '0.75rem 1.25rem',
    borderRadius: 'var(--radius-card)',
    fontSize: 'var(--text-body-md)',
    fontWeight: 600,
    zIndex: 999,
    boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
    whiteSpace: 'nowrap',
    animation: 'toastIn 200ms ease',
  }}>
    {msg}
    <style>{`@keyframes toastIn { from{opacity:0;transform:translateX(-50%) translateY(8px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }`}</style>
  </div>
);

// ── ChipGroup ─────────────────────────────────────────────────────────────────
const ChipGroup = ({
  items, selected, onToggle,
}: { items: string[]; selected: string[]; onToggle: (v: string) => void }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
    {items.map((item) => {
      const active = selected.includes(item);
      return (
        <button
          key={item}
          onClick={() => onToggle(item)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 9999,
            border: `1px solid ${active ? 'var(--color-dark-green)' : 'var(--color-chip-border)'}`,
            backgroundColor: active ? 'var(--color-dark-green)' : '#fff',
            color: active ? '#fff' : 'var(--color-chip-text)',
            fontSize: 13,
            fontWeight: 400,
            cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
        >
          {item}
        </button>
      );
    })}
  </div>
);

const SectionLabel = ({ label }: { label: string }) => (
  <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-medium-green)', margin: '0 0 0.625rem' }}>
    {label}
  </p>
);

// ── Skeleton (profile load) ───────────────────────────────────────────────────
const Skeleton = ({ h = 16, w = '100%' }: { h?: number; w?: string | number }) => (
  <div style={{ height: h, width: w, borderRadius: 8, backgroundColor: 'var(--color-divider)', animation: 'pulse 1.4s ease-in-out infinite' }} />
);

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, status, logout } = useAuthStore();
  const isGuest = status === AuthStatus.Guest;

  const [loading, setLoading] = useState(!isGuest);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
  const toastTimer = useRef<number>(0);

  // Local editable state
  const [displayName, setDisplayName] = useState('');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [conditions, setConditions] = useState<string[]>([]);
  const [goals, setGoals] = useState<string[]>([]);

  const showToast = useCallback((msg: string, type: 'success' | 'error') => {
    setToast({ msg, type });
    clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 2800);
  }, []);

  useEffect(() => {
    if (isGuest) return;
    apiClient.get<UserProfileResponse>('/users/me')
      .then((r) => {
        const p = r.data;
        setDisplayName(p.display_name ?? '');
        setAllergies(p.allergies ?? []);
        setConditions(p.conditions ?? []);
        setGoals(p.goals ?? []);
      })
      .catch(() => showToast('Failed to load profile.', 'error'))
      .finally(() => setLoading(false));
  }, [isGuest, showToast]);

  const toggleItem = (setter: React.Dispatch<React.SetStateAction<string[]>>, val: string) =>
    setter((prev) => prev.includes(val) ? prev.filter((v) => v !== val) : [...prev, val]);

  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    const body: UserProfileUpdateRequest = { display_name: displayName.trim(), allergies, conditions, goals };
    try {
      await apiClient.patch('/users/me', body);
      showToast('Profile saved ✓', 'success');
    } catch {
      showToast('Save failed. Please try again.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSignOut = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  if (loading) {
    return (
      <div style={{ padding: '1.5rem 1.25rem', maxWidth: 600, margin: '0 auto' }}>
        <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }`}</style>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Skeleton h={32} w="50%" />
          <Skeleton h={120} />
          <Skeleton h={24} w="30%" />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {[...Array(6)].map((_, i) => <Skeleton key={i} h={36} w={90} />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem 1.25rem', maxWidth: 600, margin: '0 auto', paddingBottom: '6rem' }}>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <h1 className="text-headline" style={{ color: 'var(--color-dark-green)', margin: 0 }}>
          Health Profile
        </h1>
        <button
          id="btn-signout-profile"
          onClick={handleSignOut}
          aria-label="Sign out"
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.375rem', color: 'var(--color-flagged-red)' }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </button>
      </div>

      {/* Guest banner */}
      {isGuest && (
        <div style={{
          backgroundColor: 'var(--color-light-green)',
          borderRadius: 'var(--radius-card)',
          padding: '1rem',
          marginBottom: '1.25rem',
          display: 'flex', alignItems: 'center', gap: '0.75rem',
        }}>
          <span style={{ fontSize: 22 }}>🔒</span>
          <div>
            <p style={{ fontWeight: 600, fontSize: 'var(--text-body-md)', color: 'var(--color-dark-green)', margin: 0 }}>
              Sign in to sync your profile
            </p>
            <p style={{ fontSize: 12, color: 'var(--color-medium-green)', margin: '0.125rem 0 0' }}>
              Profile changes are local-only in guest mode.
            </p>
          </div>
          <button onClick={() => navigate('/login')} className="btn-primary" style={{ marginLeft: 'auto', flexShrink: 0, padding: '0.5rem 1rem', fontSize: 13 }}>
            Sign in
          </button>
        </div>
      )}

      {/* Preview banner */}
      <div style={{
        backgroundColor: 'var(--color-dark-green)',
        borderRadius: 16,
        padding: '1.25rem',
        marginBottom: '2rem',
      }}>
        <p className="text-label" style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '0.25rem' }}>
          HEALTH PROFILE
        </p>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: '#fff', margin: '0 0 0.25rem' }}>
          Make scans personal
        </h2>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', margin: 0, lineHeight: 1.5 }}>
          We analyze every label against your profile.
          {!isGuest && ' Stored securely in the cloud.'}
        </p>
      </div>

      {/* Display name */}
      <div style={{ marginBottom: '1.5rem' }}>
        <SectionLabel label="Display name" />
        <input
          id="input-display-name"
          type="text"
          className="input"
          placeholder={isGuest ? 'Guest' : user?.displayName ?? 'e.g. Alex'}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          disabled={isGuest}
        />
      </div>

      {/* Allergies */}
      <div style={{ marginBottom: '1.5rem' }}>
        <SectionLabel label="Allergies" />
        <ChipGroup
          items={ALLERGIES}
          selected={allergies}
          onToggle={(v) => !isGuest && toggleItem(setAllergies, v)}
        />
      </div>

      {/* Conditions */}
      <div style={{ marginBottom: '1.5rem' }}>
        <SectionLabel label="Chronic conditions" />
        <ChipGroup
          items={CONDITIONS}
          selected={conditions}
          onToggle={(v) => !isGuest && toggleItem(setConditions, v)}
        />
      </div>

      {/* Goals */}
      <div style={{ marginBottom: '2rem' }}>
        <SectionLabel label="Dietary goals" />
        <ChipGroup
          items={GOALS}
          selected={goals}
          onToggle={(v) => !isGuest && toggleItem(setGoals, v)}
        />
      </div>

      {/* Save button (pinned to bottom of viewport on mobile) */}
      {!isGuest && (
        <div style={{
          position: 'sticky', bottom: 0,
          backgroundColor: 'var(--color-cream)',
          padding: '0.75rem 0',
          borderTop: '1px solid var(--color-divider)',
          marginTop: '1rem',
        }}>
          <button
            id="btn-save-profile"
            onClick={handleSave}
            disabled={saving}
            className="btn-primary"
            style={{ width: '100%' }}
          >
            {saving ? (
              <>
                <span style={{
                  display: 'inline-block', width: 16, height: 16,
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderTopColor: '#fff',
                  borderRadius: '50%',
                  animation: 'spin 0.7s linear infinite',
                }} />
                Saving…
              </>
            ) : '💾 Save profile'}
          </button>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {toast && <Toast msg={toast.msg} type={toast.type} />}
    </div>
  );
}
