/**
 * NutriScan design tokens — TypeScript mirror of
 * mobile/lib/core/theme/app_theme.dart (AppColors)
 *
 * Use for JS-land needs (dynamic styles, charting libraries, canvas, etc.).
 * For Tailwind class usage, the same values are declared via CSS @theme
 * in src/index.css and available as utilities like `bg-cream`, `text-dark-green`.
 */

export const colors = {
  // ── Brand ────────────────────────────────────
  cream:        '#F5F2EC',
  darkGreen:    '#2D4A3E',
  mediumGreen:  '#4A7C6F',
  lightGreen:   '#D6E4DF',
  chipBorder:   '#CBCBCB',
  chipText:     '#2D2D2D',

  // ── Status ───────────────────────────────────
  safeGreen:    '#2D8653',
  flaggedRed:   '#D94F3D',
  cautionAmber: '#E5A020',

  // ── Neutrals ─────────────────────────────────
  textPrimary:   '#1A1A1A',
  textSecondary: '#6B6B6B',
  textMuted:     '#9E9E9E',
  cardBg:        '#FFFFFF',
  divider:       '#E8E4DC',

  // ── Nav ──────────────────────────────────────
  navActive:   '#2D4A3E',
  navInactive: '#9E9E9E',

  // ── Overlay ──────────────────────────────────
  scannerOverlay: 'rgba(0, 0, 0, 0.6)',
} as const;

export type ColorToken = keyof typeof colors;

/** Type scale — mirrors Flutter TextTheme entries */
export const typography = {
  display:  { fontSize: 32, fontWeight: 700, lineHeight: 1.15 },
  headline: { fontSize: 24, fontWeight: 700, lineHeight: 1.25 },
  title:    { fontSize: 17, fontWeight: 600, lineHeight: 1.35 },
  bodyLg:   { fontSize: 15, fontWeight: 400, lineHeight: 1.5  },
  bodyMd:   { fontSize: 13, fontWeight: 400, lineHeight: 1.5  },
  label:    { fontSize: 11, fontWeight: 500, lineHeight: 1.4, letterSpacing: '0.05em', textTransform: 'uppercase' as const },
} as const;

export const radii = {
  card: '12px',
  chip: '6px',
  full: '9999px',
} as const;

export const spacing = {
  /** Default horizontal page padding */
  pagePx: '1.25rem',   // 20px
  /** Vertical gap between sections */
  section: '1.5rem',   // 24px
} as const;
