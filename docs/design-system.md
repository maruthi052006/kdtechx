# Design System Specification: KDTechX Enterprise UI
**Document ID:** `DS-KDTECHX-2026-01`  
**Brand Identity:** Technical, Intelligent, Modern, Precise, Premium, Confident, Minimal  
**Tagline:** *Learn. Practice. Assess. Grow.*  

---

## 1. Design Philosophy & Aesthetic Standard

The KDTechX portal is crafted to embody the polish of top-tier developer platforms and enterprise SaaS systems (Linear, Vercel, Stripe). It strictly avoids generic LMS tropes, raw Bootstrap appearances, or juvenile educational styling.

### The 80-15-5 Color Distribution
* **80% Neutral Canvas:** Deep rich slates, dark surface layers, subtle borders, and precise white/light-gray typography.
* **15% Secondary Structure:** Subtle container fills, subdued badges, table zebra stripes, and muted icon highlights.
* **5% Vibrant Accent:** Purposeful application of KDTechX Blue (`#4f8cff`), Electric Cyan (`#2bd8ff`), and Status Emerald (`#2ddf91`) reserved strictly for primary actions, active navigation indicators, and critical metrics.

---

## 2. Core Token Definitions (`static/css/tokens.css`)

### 2.1 Color Tokens: Dark Mode (Default)
```css
:root, [data-theme="dark"] {
  /* Surfaces & Backgrounds */
  --kd-bg: #070a0f;
  --kd-surface: #0c1118;
  --kd-surface-2: #111823;
  --kd-surface-3: #16202e;
  --kd-surface-hover: #1c2738;
  
  /* Borders */
  --kd-border: rgba(255, 255, 255, 0.08);
  --kd-border-strong: rgba(255, 255, 255, 0.15);
  --kd-border-focus: rgba(79, 140, 255, 0.5);

  /* Typography */
  --kd-text: #f7f9fc;
  --kd-text-secondary: #aab4c3;
  --kd-text-muted: #6f7b8c;
  --kd-text-disabled: #414b5c;

  /* Brand Accents */
  --kd-primary: #4f8cff;
  --kd-primary-hover: #6a9cff;
  --kd-primary-tint: rgba(79, 140, 255, 0.12);
  --kd-cyan: #2bd8ff;
  --kd-cyan-tint: rgba(43, 216, 255, 0.12);
  --kd-indigo: #746cff;

  /* Semantic Feedback */
  --kd-success: #2ddf91;
  --kd-success-tint: rgba(45, 223, 145, 0.12);
  --kd-warning: #f4b740;
  --kd-warning-tint: rgba(244, 183, 64, 0.12);
  --kd-danger: #ff5f6d;
  --kd-danger-tint: rgba(255, 95, 109, 0.12);

  /* Elevation Shadows */
  --kd-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.35);
  --kd-shadow-md: 0 4px 12px rgba(0, 0, 0, 0.45);
  --kd-shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.6);
  --kd-shadow-card: 0 0 0 1px var(--kd-border), 0 4px 16px rgba(0, 0, 0, 0.3);
}
```

### 2.2 Color Tokens: Light Mode (Independently Crafted)
```css
[data-theme="light"] {
  /* Surfaces & Backgrounds */
  --kd-bg: #f8fafc;
  --kd-surface: #ffffff;
  --kd-surface-2: #f1f5f9;
  --kd-surface-3: #e2e8f0;
  --kd-surface-hover: #f8fafc;

  /* Borders */
  --kd-border: rgba(0, 0, 0, 0.08);
  --kd-border-strong: rgba(0, 0, 0, 0.16);
  --kd-border-focus: rgba(37, 99, 235, 0.4);

  /* Typography */
  --kd-text: #0f172a;
  --kd-text-secondary: #475569;
  --kd-text-muted: #64748b;
  --kd-text-disabled: #94a3b8;

  /* Brand Accents */
  --kd-primary: #2563eb;
  --kd-primary-hover: #1d4ed8;
  --kd-primary-tint: rgba(37, 99, 235, 0.08);
  --kd-cyan: #0284c7;
  --kd-cyan-tint: rgba(2, 132, 199, 0.08);
  --kd-indigo: #4f46e5;

  /* Semantic Feedback */
  --kd-success: #16a34a;
  --kd-success-tint: rgba(22, 163, 74, 0.08);
  --kd-warning: #d97706;
  --kd-warning-tint: rgba(217, 119, 6, 0.08);
  --kd-danger: #dc2626;
  --kd-danger-tint: rgba(220, 38, 38, 0.08);

  /* Elevation Shadows */
  --kd-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
  --kd-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
  --kd-shadow-lg: 0 10px 25px -3px rgba(0, 0, 0, 0.1);
  --kd-shadow-card: 0 0 0 1px var(--kd-border), 0 2px 8px rgba(0, 0, 0, 0.04);
}
```

---

## 3. Typography Hierarchy

Utilizing **Inter** or **Geist** with tabular figures enabled (`font-feature-settings: "cv02", "cv03", "cv04", "cv11", "tnum"`).

| Token | Size | Line Height | Weight | Letter Spacing | Purpose |
|---|---|---|---|---|---|
| `Display` | 2.500rem (40px) | 1.15 | 800 | -0.035em | Hero Landing Headlines |
| `H1` | 1.875rem (30px) | 1.25 | 700 | -0.025em | Main Page Titles |
| `H2` | 1.500rem (24px) | 1.30 | 600 | -0.020em | Section Headers |
| `H3` | 1.250rem (20px) | 1.35 | 600 | -0.015em | Card Titles, Modal Headers |
| `H4` | 1.000rem (16px) | 1.40 | 600 | -0.010em | Subheaders, Table Headers |
| `Body` | 0.9375rem (15px)| 1.55 | 400 | -0.005em | Default text, form labels |
| `Body Small` | 0.8125rem (13px)| 1.50 | 400 | 0.000em | Secondary metadata |
| `Caption` | 0.7500rem (12px)| 1.40 | 500 | +0.020em | Status badges, timestamps |
| `Metric` | 2.2500rem (36px)| 1.10 | 700 | -0.030em | Dashboard KPIs, timers |

---

## 4. Spacing Scale & Border Radii

### Spacing Scale
* `4px` (`--kd-space-1`): Inner icon gaps, micro tags
* `8px` (`--kd-space-2`): Button padding vertical, list spacing
* `12px` (`--kd-space-3`): Input vertical padding, compact table cells
* `16px` (`--kd-space-4`): Standard component gutters, button padding horizontal
* `20px` (`--kd-space-5`): Card internal padding
* `24px` (`--kd-space-6`): Section separation
* `32px` (`--kd-space-8`): Layout column gutters
* `48px` (`--kd-space-12`): Dashboard widget spacing
* `64px` (`--kd-space-16`): Hero sections and large breaks

### Border Radii
* `6px` (`--kd-radius-sm`): Badges, tooltips, small buttons
* `10px` (`--kd-radius-md`): Inputs, standard buttons, dropdown menus
* `14px` (`--kd-radius-lg`): Cards, table containers, exam option boxes
* `18px` (`--kd-radius-xl`): Dialogs, modal sheets, command palette
* `24px` (`--kd-radius-2xl`): Hero spotlight elements

---

## 5. Technical Grid & Atmospheric Surfaces

### Atmospheric Background
```css
.kd-bg-grid {
  background-image: 
    linear-gradient(to right, var(--kd-border) 1px, transparent 1px),
    linear-gradient(to bottom, var(--kd-border) 1px, transparent 1px);
  background-size: 32px 32px;
}
```

### Soft Radial Glow
```css
.kd-glow-radial {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  height: 500px;
  background: radial-gradient(circle, rgba(79, 140, 255, 0.08) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
```

---

## 6. Micro-Interactions & Animation Standards

* **Duration:** 120ms to 240ms.
* **Timing Function:** `cubic-bezier(0.16, 1, 0.3, 1)` (snappy ease-out).
* **Hover States:** Soft background shifts + subtle 1px border illumination. Never jarring transforms or neon glows.
* **Reduced Motion:** Fully honored via `@media (prefers-reduced-motion: reduce)`.
