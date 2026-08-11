import { useEffect, useRef, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import type { ScanResponse, ScanHistoryResponse, IngredientResult, ScoreBreakdown } from '../../lib/types';
import { scoreColor, scoreLabel } from '../../lib/types';
import { BarChart2, AlertTriangle, Factory, Microscope, HeartPulse, AlertCircle, ArrowLeft } from 'lucide-react';

// ── Normalised shape ──────────────────────────────────────────────────────────
interface ResultData {
  productName: string;
  brand:       string;
  score:       number;
  novaClass:   number;
  ingredients: IngredientResult[];
  breakdown?:  ScoreBreakdown;
  nutrients?:  Record<string, unknown>;
}

function fromScanResponse(r: ScanResponse): ResultData {
  return {
    productName: r.product_name ?? 'Scanned Label',
    brand:       r.brand ?? 'Unknown',
    score:       r.safety_score,
    novaClass:   r.nova_class,
    ingredients: r.ingredients,
    breakdown:   r.breakdown,
    nutrients:   r.nutrients ?? undefined,
  };
}

function fromHistoryResponse(h: ScanHistoryResponse): ResultData {
  return {
    productName: h.product_name ?? 'Unknown product',
    brand:       h.brand ?? '',
    score:       h.health_score ?? 0,
    novaClass:   h.nova_group ?? 4,
    ingredients: (h.ingredients as IngredientResult[] | null) ?? [],
    breakdown:   undefined, // not persisted in history
    nutrients:   h.nutrients ?? undefined,
  };
}

// ── Animated score gauge (CSS conic-gradient) ─────────────────────────────────
const ScoreGauge = ({ score }: { score: number }) => {
  const [displayed, setDisplayed] = useState(0);
  const [progress, setProgress] = useState(0);
  const raf = useRef<number>(0);
  const start = useRef<number | null>(null);
  const color = scoreColor(score);

  useEffect(() => {
    const duration = 1200;
    const animate = (ts: number) => {
      if (!start.current) start.current = ts;
      const elapsed = ts - start.current;
      const t = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setDisplayed(Math.round(score * ease));
      setProgress(ease);
      if (t < 1) raf.current = requestAnimationFrame(animate);
    };
    raf.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf.current);
  }, [score]);

  // Arc via SVG
  const radius = 64;
  const circ = 2 * Math.PI * radius;
  const startAngle = 135; // degrees from 12 o'clock
  const sweepDeg = 270;
  const offset = circ - (circ * (sweepDeg / 360)) * progress;

  return (
    <div style={{ position: 'relative', width: 160, height: 160, margin: '0 auto' }}>
      <svg width="160" height="160" viewBox="0 0 160 160"
        style={{ transform: `rotate(${startAngle - 90}deg)` }} aria-hidden="true">
        {/* Track */}
        <circle cx="80" cy="80" r={radius}
          fill="none" stroke="rgba(255,255,255,0.12)"
          strokeWidth="12" strokeLinecap="round"
          strokeDasharray={`${circ * (sweepDeg / 360)} ${circ * ((360 - sweepDeg) / 360)}`}
        />
        {/* Progress */}
        <circle cx="80" cy="80" r={radius}
          fill="none" stroke={color}
          strokeWidth="12" strokeLinecap="round"
          strokeDasharray={`${circ * (sweepDeg / 360)} ${circ}`}
          strokeDashoffset={offset}
          style={{ transition: 'stroke 300ms ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 52, fontWeight: 800, color, lineHeight: 1 }}>{displayed}</span>
        <span style={{ fontSize: 11, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginTop: 2 }}>
          Health Score
        </span>
      </div>
    </div>
  );
};

// ── HeroScoreHeader ───────────────────────────────────────────────────────────
const HeroScoreHeader = ({ data }: { data: ResultData }) => {
  const color = scoreColor(data.score);
  return (
    <div style={{
      background: 'linear-gradient(135deg, var(--color-dark-green) 0%, var(--color-medium-green) 100%)',
      padding: '1.75rem 1.5rem 2rem',
    }}>
      <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '1.5px', color: 'rgba(255,255,255,0.54)', margin: '0 0 0.25rem', textAlign: 'center' }}>
        {data.brand.toUpperCase()}
      </p>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: '#fff', margin: '0 0 1.5rem', textAlign: 'center', lineHeight: 1.2 }}>
        {data.productName}
      </h2>
      <ScoreGauge score={data.score} />
      <div style={{ marginTop: '1.25rem', textAlign: 'center' }}>
        <span style={{
          display: 'inline-block',
          padding: '0.375rem 1rem',
          borderRadius: 9999,
          backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
          border: `1px solid color-mix(in srgb, ${color} 40%, transparent)`,
          color,
          fontSize: 13, fontWeight: 600, letterSpacing: '0.3px',
        }}>
          {scoreLabel(data.score)}
        </span>
      </div>
    </div>
  );
};

// ── NovaClassificationBadge ───────────────────────────────────────────────────
const NOVA_CONFIGS = [
  null,
  { bg: '#F0FBF5', accent: '#1E8C4A', title: 'Unprocessed / Natural',           desc: 'Foods in their natural state. Eat freely and enjoy.' },
  { bg: '#F4FBF0', accent: '#5BAD5B', title: 'Processed Culinary Ingredients',  desc: 'Simple ingredients like oils, flours, or spices. Use in moderation.' },
  { bg: '#FFF8EC', accent: '#D98B2A', title: 'Processed Foods',                 desc: 'Contains added salt, sugar, or oils. Limit your intake frequency.' },
  { bg: '#FFF1F0', accent: '#D94F3D', title: 'Ultra-Processed',                 desc: 'Industrial formulations with additives. Avoid frequent consumption.' },
];

const NovaClassificationBadge = ({ novaClass }: { novaClass: number }) => {
  const c = NOVA_CONFIGS[Math.min(novaClass, 4)] ?? NOVA_CONFIGS[4]!;
  return (
    <div style={{
      margin: '1.25rem',
      backgroundColor: c.bg,
      borderRadius: 20,
      padding: '1rem 1.25rem',
      display: 'flex', alignItems: 'center', gap: '1rem',
    }}>
      <div style={{
        backgroundColor: c.accent, borderRadius: 12,
        padding: '0.5rem 0.75rem', textAlign: 'center', flexShrink: 0,
      }}>
        <div style={{ color: '#fff', fontSize: 10, fontWeight: 700, letterSpacing: '1.2px' }}>NOVA</div>
        <div style={{ color: '#fff', fontSize: 26, fontWeight: 800, lineHeight: 1 }}>{novaClass}</div>
      </div>
      <div>
        <p style={{ fontWeight: 700, fontSize: 15, color: c.accent, margin: '0 0 0.25rem' }}>{c.title}</p>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.45 }}>{c.desc}</p>
      </div>
    </div>
  );
};

// ── SafetyScoreBreakdownCard ──────────────────────────────────────────────────
const BreakdownRow = ({ icon, label, deduction }: { icon: React.ReactNode; label: string; deduction: number }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
    <span>{icon}</span>
    <span style={{ flex: 1, fontSize: 13, color: 'var(--color-text-primary)' }}>{label}</span>
    <span style={{
      fontSize: 13, fontWeight: 600,
      color: deduction > 0 ? 'var(--color-flagged-red)' : 'var(--color-text-muted)',
    }}>
      {deduction > 0 ? `-${deduction.toFixed(0)}` : '0'}
    </span>
  </div>
);

const SafetyScoreBreakdownCard = ({ breakdown }: { breakdown: ScoreBreakdown }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="card" style={{ margin: '0 1.25rem' }}>
      <button onClick={() => setExpanded((v) => !v)} style={{
        display: 'flex', alignItems: 'center', gap: '0.75rem',
        width: '100%', background: 'none', border: 'none',
        cursor: 'pointer', padding: '1rem', textAlign: 'left',
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          backgroundColor: 'rgba(214,228,223,0.4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <BarChart2 size={20} color="var(--color-medium-green)" />
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text-primary)', margin: 0 }}>
            Personal Score Breakdown
          </p>
          <p style={{ fontSize: 11, color: 'var(--color-text-secondary)', margin: 0 }}>
            Tap to see how your profile affected the score
          </p>
        </div>
        <span style={{ color: 'var(--color-text-muted)', fontSize: 18 }}>{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div style={{ padding: '0 1rem 1rem', borderTop: '1px solid var(--color-divider)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', paddingTop: '0.75rem' }}>
            <BreakdownRow icon={<AlertTriangle size={16} color="var(--color-flagged-red)" />} label="Allergens"           deduction={breakdown.allergenDeduction} />
            <BreakdownRow icon={<Factory size={16} color="var(--color-text-secondary)" />} label="NOVA Processing"     deduction={breakdown.novaDeduction} />
            <BreakdownRow icon={<Microscope size={16} color="var(--color-text-secondary)" />} label="Additives"           deduction={breakdown.additiveDeduction} />
            <BreakdownRow icon={<HeartPulse size={16} color="var(--color-flagged-red)" />} label="Personal Conditions"  deduction={breakdown.conditionDeduction} />
          </div>
        </div>
      )}
    </div>
  );
};

// ── NutrientInsightGrid ───────────────────────────────────────────────────────
interface NutrientTileData { name: string; value: string; unit: string; level: 'good' | 'moderate' | 'poor' | 'unknown' }

const LEVEL_COLORS = {
  good:     { dot: 'var(--color-safe-green)',    bg: '#eaf7f0', label: 'var(--color-safe-green)' },
  moderate: { dot: 'var(--color-caution-amber)', bg: '#fff7e6', label: 'var(--color-caution-amber)' },
  poor:     { dot: 'var(--color-flagged-red)',   bg: '#fff0ef', label: 'var(--color-flagged-red)' },
  unknown:  { dot: '#ccc', bg: '#f0f0f0', label: '#999' },
};

const LEVEL_LABELS = { good: 'HEALTHY', moderate: 'MODERATE', poor: 'HIGH', unknown: 'NO DATA' };

function parseNutrients(raw: Record<string, unknown>): NutrientTileData[] {
  const map: Record<string, { display: string; unit: string; highThreshold: number; lowGood: boolean }> = {
    sugars_100g:         { display: 'Sugars',    unit: 'g',   highThreshold: 10, lowGood: true },
    fat_100g:            { display: 'Fat',       unit: 'g',   highThreshold: 17.5, lowGood: true },
    'saturated-fat_100g': { display: 'Sat. Fat', unit: 'g',   highThreshold: 5, lowGood: true },
    sodium_100g:         { display: 'Sodium',    unit: 'mg',  highThreshold: 0.6, lowGood: true },
    proteins_100g:       { display: 'Protein',   unit: 'g',   highThreshold: 0, lowGood: false },
    fiber_100g:          { display: 'Fibre',     unit: 'g',   highThreshold: 0, lowGood: false },
    energy_100g:         { display: 'Energy',    unit: 'kcal',highThreshold: 400, lowGood: true },
    carbohydrates_100g:  { display: 'Carbs',     unit: 'g',   highThreshold: 60, lowGood: true },
  };

  return Object.entries(map).map(([key, meta]) => {
    const val = raw[key];
    if (val == null) {
      return { name: meta.display, value: '–', unit: meta.unit, level: 'unknown' };
    }
    const num = Number(val);
    let level: NutrientTileData['level'] = 'unknown';
    if (!isNaN(num)) {
      if (meta.lowGood) {
        level = meta.highThreshold === 0 ? 'good' : num > meta.highThreshold ? 'poor' : num > meta.highThreshold * 0.5 ? 'moderate' : 'good';
      } else {
        level = num > meta.highThreshold * 0.5 ? 'good' : num > 0 ? 'moderate' : 'poor';
      }
    }
    const display = meta.unit === 'kcal'
      ? String(Math.round(num / 4.184)) // kJ → kcal approximation if needed
      : num.toFixed(num < 10 ? 1 : 0);
    return { name: meta.display, value: isNaN(num) ? String(val) : display, unit: meta.unit, level };
  });
}

const NutrientInsightGrid = ({ nutrients, hasFullData }: { nutrients?: Record<string, unknown>; hasFullData?: boolean }) => {
  if (!nutrients) return null;
  const tiles = parseNutrients(nutrients);
  const allUnknown = tiles.every((t) => t.level === 'unknown');
  if (allUnknown) return null;

  return (
    <div style={{ margin: '0 1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <h3 style={{ fontWeight: 700, fontSize: 17, color: 'var(--color-text-primary)', margin: 0 }}>
          Nutrient Breakdown
        </h3>
        {!hasFullData && (
          <span style={{
            fontSize: 10, color: 'var(--color-text-muted)',
            backgroundColor: '#f0f0f0', borderRadius: 6,
            padding: '0.125rem 0.5rem', fontWeight: 500,
          }}>
            Barcode scan for full data
          </span>
        )}
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '0.75rem',
      }}>
        {tiles.map((tile) => {
          const colors = LEVEL_COLORS[tile.level];
          return (
            <div key={tile.name} className="card" style={{
              padding: '1rem',
              backgroundColor: tile.level === 'unknown' ? '#f8f8f8' : 'var(--color-card-bg)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: 12, fontWeight: 500, color: tile.level === 'unknown' ? 'var(--color-text-muted)' : 'var(--color-text-secondary)' }}>
                  {tile.name}
                </span>
                <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: colors.dot, flexShrink: 0 }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.25rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: 26, fontWeight: 800, color: tile.level === 'unknown' ? '#bbb' : 'var(--color-text-primary)', lineHeight: 1 }}>
                  {tile.value}
                </span>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)', paddingBottom: 2 }}>{tile.unit}</span>
              </div>
              <span style={{
                fontSize: 10, fontWeight: 600,
                color: colors.label,
                backgroundColor: colors.bg,
                borderRadius: 6,
                padding: '0.125rem 0.5rem',
              }}>
                {LEVEL_LABELS[tile.level]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── IngredientAnalysisCard ────────────────────────────────────────────────────
const IngredientAnalysisCard = ({ ingredients }: { ingredients: IngredientResult[] }) => {
  const [expanded, setExpanded] = useState(false);
  const flaggedCount = ingredients.filter((i) => i.status === 'danger' || i.status === 'caution').length;
  const shown = expanded ? ingredients : ingredients.slice(0, 5);

  return (
    <div style={{ margin: '0 1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h3 style={{ fontWeight: 700, fontSize: 17, color: 'var(--color-text-primary)', margin: 0 }}>
          Ingredients
        </h3>
        {flaggedCount > 0 && (
          <span style={{
            fontSize: 11, fontWeight: 600,
            color: 'var(--color-flagged-red)',
            backgroundColor: '#fff0ef',
            border: '1px solid rgba(217,79,61,0.3)',
            borderRadius: 10,
            padding: '0.25rem 0.625rem',
          }}>
            ⚠ {flaggedCount} flagged
          </span>
        )}
      </div>

      <div className="card">
        {shown.map((item, i) => {
          const isDanger  = item.status === 'danger';
          const isCaution = item.status === 'caution';
          const isSafe    = item.status === 'safe';
          return (
            <div key={i}>
              <div style={{ padding: '0.75rem 1rem', display: 'flex', gap: '0.625rem', alignItems: 'flex-start' }}>
                {isDanger || isCaution ? (
                  <span style={{ marginTop: 2, flexShrink: 0 }}>
                    {isDanger ? <AlertTriangle size={16} color="var(--color-flagged-red)" /> : <AlertCircle size={16} color="var(--color-caution-amber)" />}
                  </span>
                ) : (
                  <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--color-safe-green)', marginTop: 6, marginLeft: 4, flexShrink: 0 }} />
                )}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    margin: 0,
                    fontSize: 13.5,
                    fontWeight: isSafe ? 400 : 600,
                    color: 'var(--color-text-primary)',
                    lineHeight: 1.4,
                  }}>
                    {item.name}
                  </p>
                  {(isDanger || isCaution) && item.reason && (
                    <p style={{
                      margin: '0.1875rem 0 0',
                      fontSize: 11,
                      color: isDanger ? 'var(--color-flagged-red)' : 'var(--color-caution-amber)',
                      fontWeight: 500,
                    }}>
                      {item.reason}
                    </p>
                  )}
                </div>
              </div>
              {i < shown.length - 1 && <hr className="divider" style={{ margin: '0 1rem' }} />}
            </div>
          );
        })}

        {ingredients.length > 5 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem',
              width: '100%', padding: '0.875rem',
              backgroundColor: 'rgba(214,228,223,0.35)', border: 'none',
              borderTop: '1px solid var(--color-divider)',
              borderRadius: '0 0 var(--radius-card) var(--radius-card)',
              cursor: 'pointer',
              color: 'var(--color-medium-green)',
              fontSize: 13, fontWeight: 600,
            }}
          >
            {expanded ? 'Show less ▲' : `Show ${ingredients.length - 5} more ▼`}
          </button>
        )}
      </div>
    </div>
  );
};

// ── ResultsPage ───────────────────────────────────────────────────────────────
export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [data, setData] = useState<ResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fresh scan result passed via navigation state (from ScanPage)
    const state = location.state as { result?: ScanResponse } | null;
    if (state?.result) {
      setData(fromScanResponse(state.result));
      setLoading(false);
      return;
    }

    // Fetch from history
    if (id && id !== 'new') {
      apiClient.get<ScanHistoryResponse>(`/history/${id}`)
        .then((r) => setData(fromHistoryResponse(r.data)))
        .catch((err) => {
          const e = err as { response?: { status?: number }; message?: string };
          setError(e.response?.status === 404 ? 'Scan not found.' : e.message ?? 'Failed to load scan.');
        })
        .finally(() => setLoading(false));
    } else {
      setError('No result data. Please run a scan first.');
      setLoading(false);
    }
  }, [id, location.state]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <div style={{
          width: 32, height: 32,
          border: '3px solid var(--color-light-green)',
          borderTopColor: 'var(--color-dark-green)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '2rem 1.25rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-dark-green)', marginBottom: '1rem' }}>No Result</h1>
        <p style={{ color: 'var(--color-flagged-red)', marginBottom: '1rem' }}>{error ?? 'Unknown error'}</p>
        <button onClick={() => navigate('/scan')} className="btn-primary">Try again</button>
      </div>
    );
  }

  return (
    <div>
      {/* Back button */}
      <div style={{
        backgroundColor: 'var(--color-dark-green)',
        padding: '0.75rem 1.25rem',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button
          id="btn-results-back"
          onClick={() => navigate(-1)}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.375rem',
            background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 10, padding: '0.375rem 0.75rem',
            color: '#fff', fontSize: 14, fontWeight: 500, cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} /> Back
        </button>
        <h1 style={{ fontSize: 17, fontWeight: 600, color: '#fff', margin: 0 }}>Scan Results</h1>
        <div style={{ width: 80 }} />
      </div>

      {/* Hero score */}
      <HeroScoreHeader data={data} />

      {/* Body sections */}
      <div style={{ backgroundColor: 'var(--color-cream)', paddingBottom: '2rem' }}>
        {/* Breakdown (fresh scan only) */}
        {data.breakdown && (
          <div style={{ marginTop: '1.25rem' }}>
            <SafetyScoreBreakdownCard breakdown={data.breakdown} />
          </div>
        )}

        {/* NOVA */}
        <div style={{ marginTop: '1.25rem' }}>
          <NovaClassificationBadge novaClass={data.novaClass} />
        </div>

        {/* Nutrients */}
        {data.nutrients && Object.keys(data.nutrients).length > 0 && (
          <div style={{ marginTop: '1.5rem' }}>
            <NutrientInsightGrid nutrients={data.nutrients} hasFullData={!!data.breakdown} />
          </div>
        )}

        {/* Ingredients */}
        {data.ingredients.length > 0 && (
          <div style={{ marginTop: '1.5rem' }}>
            <IngredientAnalysisCard ingredients={data.ingredients} />
          </div>
        )}

        {/* Divider + action */}
        <hr className="divider" style={{ margin: '1.75rem 1.25rem' }} />
        <div style={{ padding: '0 1.25rem' }}>
          <button
            id="btn-scan-another"
            onClick={() => navigate('/scan')}
            className="btn-ghost"
            style={{ width: '100%' }}
          >
            Scan another product
          </button>
        </div>
      </div>
    </div>
  );
}
