import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import type { ScanResponse } from '../../lib/types';

type Tab = 'barcode' | 'ingredients';

export default function ScanPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('barcode');

  // Barcode
  const [barcode, setBarcode] = useState('');

  // Ingredients (manual text)
  const [ingredientText, setIngredientText] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBarcode = async () => {
    if (!barcode.trim()) { setError('Enter a barcode number.'); return; }
    setError(null);
    setLoading(true);
    try {
      const { data } = await apiClient.post<ScanResponse>('/scan/barcode', { barcode: barcode.trim() });
      navigate('/results/new', { state: { result: data } });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      const detail = e.response?.data?.detail;
      setError(detail === 'Product not found in database'
        ? 'Product not found. Try entering the ingredients manually.'
        : detail ?? e.message ?? 'Lookup failed. Check the barcode and try again.');
    } finally {
      setLoading(false);
    }
  };

  const runIngredients = async () => {
    const lines = ingredientText
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);

    if (lines.length === 0) { setError('Paste at least one ingredient.'); return; }
    setError(null);
    setLoading(true);
    try {
      const { data } = await apiClient.post<ScanResponse>('/scan/analyse', { ingredients: lines });
      navigate('/results/new', { state: { result: data } });
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message ?? 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '1.5rem 1.25rem', maxWidth: 600, margin: '0 auto' }}>
      <h1 className="text-headline" style={{ color: 'var(--color-text-primary)', marginBottom: '0.25rem' }}>
        Scan a product
      </h1>
      <p className="text-body-md" style={{ color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>
        Look up by barcode or paste the ingredient list from the label.
      </p>

      {/* ── Tabs ────────────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        backgroundColor: 'var(--color-light-green)',
        borderRadius: 'var(--radius-card)',
        padding: '0.25rem',
        marginBottom: '1.5rem',
        gap: '0.25rem',
      }}>
        {(['barcode', 'ingredients'] as Tab[]).map((t) => (
          <button
            key={t}
            id={`tab-${t}`}
            onClick={() => { setTab(t); setError(null); }}
            style={{
              flex: 1,
              padding: '0.5rem 0',
              border: 'none',
              borderRadius: 'calc(var(--radius-card) - 4px)',
              backgroundColor: tab === t ? '#fff' : 'transparent',
              color: tab === t ? 'var(--color-dark-green)' : 'var(--color-text-secondary)',
              fontWeight: tab === t ? 600 : 400,
              fontSize: 'var(--text-body-md)',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              boxShadow: tab === t ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            }}
          >
            {t === 'barcode' ? '🔢 Enter barcode' : '📋 Paste ingredients'}
          </button>
        ))}
      </div>

      {/* ── Error ───────────────────────────────────────────────────────────── */}
      {error && (
        <div style={{
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

      {/* ── Barcode tab ─────────────────────────────────────────────────────── */}
      {tab === 'barcode' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label htmlFor="input-barcode" style={{
              display: 'block', marginBottom: '0.5rem',
              fontSize: 'var(--text-body-md)', fontWeight: 500,
              color: 'var(--color-medium-green)',
            }}>
              Barcode number
            </label>
            <input
              id="input-barcode"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              className="input"
              placeholder="e.g. 3017620422003"
              value={barcode}
              onChange={(e) => setBarcode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runBarcode()}
            />
            <p style={{ marginTop: '0.375rem', fontSize: 12, color: 'var(--color-text-muted)' }}>
              Works with EAN-8, EAN-13, UPC-A — uses the Open Food Facts database.
            </p>
          </div>
          <button
            id="btn-scan-barcode"
            onClick={runBarcode}
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%' }}
          >
            {loading ? 'Looking up…' : 'Look up product'}
          </button>
        </div>
      )}

      {/* ── Ingredients tab ─────────────────────────────────────────────────── */}
      {tab === 'ingredients' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Transparency notice */}
          <div style={{
            backgroundColor: '#fdf3e0',
            border: '1px solid var(--color-caution-amber)',
            borderRadius: 'var(--radius-card)',
            padding: '0.75rem 1rem',
            fontSize: 'var(--text-body-md)',
            color: '#7a5000',
          }}>
            <strong>📸 Web note:</strong> There is no live camera or OCR on the web version.
            Please copy the ingredients text from the product label manually and paste it below.
          </div>

          <div>
            <label htmlFor="input-ingredients" style={{
              display: 'block', marginBottom: '0.5rem',
              fontSize: 'var(--text-body-md)', fontWeight: 500,
              color: 'var(--color-medium-green)',
            }}>
              Ingredients (one per line, or comma-separated)
            </label>
            <textarea
              id="input-ingredients"
              className="input"
              placeholder={'Water, Sugar, E621, Palm Oil, Salt,\nModified Starch, Flavourings…'}
              value={ingredientText}
              onChange={(e) => setIngredientText(e.target.value)}
              rows={8}
              style={{ resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6 }}
            />
            <p style={{ marginTop: '0.375rem', fontSize: 12, color: 'var(--color-text-muted)' }}>
              We'll classify each ingredient and calculate your personalised health score.
            </p>
          </div>

          <button
            id="btn-analyse-ingredients"
            onClick={runIngredients}
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%' }}
          >
            {loading ? 'Analysing…' : 'Analyse ingredients'}
          </button>
        </div>
      )}
    </div>
  );
}
