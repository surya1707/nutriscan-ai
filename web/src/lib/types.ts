/**
 * TypeScript types mirroring the FastAPI backend schemas exactly.
 * Field names match backend/app/schemas/*.py — do not rename.
 */

// ── scan.py ─────────────────────────────────────────────────────────────────

export interface IngredientResult {
  name:   string;
  status: 'safe' | 'caution' | 'danger';
  reason: string;
}

export interface ScoreBreakdown {
  allergenDeduction:  number;
  novaDeduction:      number;
  additiveDeduction:  number;
  conditionDeduction: number;
}

export interface ScanResponse {
  product_name?: string;
  brand?:        string;
  ingredients:   IngredientResult[];
  safety_score:  number;
  nova_class:    number;
  breakdown:     ScoreBreakdown;
  nutrients?:    Record<string, unknown>;
}

// ── history.py ───────────────────────────────────────────────────────────────

export interface ScanHistoryResponse {
  id:           number;
  user_id:      string;
  scanned_at:   string;
  product_name?: string;
  brand?:        string;
  health_score?: number;
  nova_group?:   number;
  nutrients?:    Record<string, unknown> | null;
  ingredients?:  IngredientResult[] | null;
}

// ── user.py ──────────────────────────────────────────────────────────────────

export interface UserProfileResponse {
  id:            string;
  allergies?:    string[];
  conditions?:   string[];
  goals?:        string[];
  display_name?: string;
}

export interface UserProfileUpdateRequest {
  allergies?:    string[];
  conditions?:   string[];
  goals?:        string[];
  display_name?: string;
}

// ── Score helpers ─────────────────────────────────────────────────────────────

/** Returns the design-token color string for a health/safety score 0–100. */
export function scoreColor(score: number): string {
  if (score >= 70) return 'var(--color-safe-green)';
  if (score >= 45) return 'var(--color-caution-amber)';
  return 'var(--color-flagged-red)';
}

export function scoreBgColor(score: number): string {
  if (score >= 70) return '#eaf7f0';
  if (score >= 45) return '#fdf3e0';
  return '#fde8e6';
}

export function scoreLabel(score: number): string {
  if (score >= 75) return '✅ Great Choice';
  if (score >= 50) return '⚠️ Consume Moderately';
  if (score >= 25) return '🔴 Poor Nutritional Quality';
  return '🚫 Avoid — Very Unhealthy';
}

/** Maps backend status string → CSS color token. */
export function ingredientStatusColor(status: string): string {
  if (status === 'safe')   return 'var(--color-safe-green)';
  if (status === 'danger') return 'var(--color-flagged-red)';
  return 'var(--color-caution-amber)';
}
