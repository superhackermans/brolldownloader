# Animated HTML Video Template — Design Guide

This document defines the exact design system, animation rules, and coding patterns used to create animated HTML files that get recorded as 4K video overlays. Follow these rules to produce new HTML files that match the existing style and work with the recording pipeline.

---

## 1. Canvas & Layout

| Property | Value |
|---|---|
| Target resolution | 1920 x 1080 viewport (rendered at 2x = 3840 x 2160 4K) |
| Duration | 15 seconds total animation (default) |
| Frame rate | 30 fps |
| Body background | `#0a0e1a` (deep navy — replaced with transparency during recording) |
| Content centering | Flexbox: `display: flex; justify-content: center; align-items: center; min-height: 100vh` |
| Overflow | `overflow: hidden` on body — nothing should scroll |
| Padding | `48px` to `60px` on body |
| Max content width | `960px` to `1200px` depending on layout density |
| Size scale | **All dimensions 30% larger than "standard" web sizes.** This compensates for 4K output viewed at typical distances. Apply 1.3x to all font sizes, paddings, margins, gaps, border-radii, and container widths when designing. |
| Animation start | First animation event at `100ms` (not 0, not 2000ms) |

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0a0e1a;
  font-family: 'DM Sans', sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 48px;
  overflow: hidden;
}
```

> **30% Scale Rule:** All dimensional values in new animations should be 30% larger than standard web sizes. For example: a typical `12px` font becomes `16px`, `20px` padding becomes `26px`, `800px` container becomes `1040px`. This ensures content reads well at 4K resolution.

---

## 2. Background Video Element

Every file includes a looping background video element. This gets hidden during recording and composited via FFmpeg instead.

```html
<video autoplay muted loop playsinline id="bg-video">
  <source src="Wavy Grid Background.mp4" type="video/mp4">
</video>
```

```css
#bg-video {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  object-fit: cover;
  z-index: 0;
}
```

All content sits in a wrapper with `position: relative; z-index: 1`.

---

## 3. Color Palette

| Role | Color | Hex |
|---|---|---|
| Background (body) | Deep navy | `#0a0e1a` |
| Card/panel background | Deep navy, high opacity | `rgba(8, 10, 22, 0.85)` |
| Primary accent (blue) | Light blue | `#4A9EF7` |
| Primary accent (bright) | Bright blue | `#5BAAFF` |
| Secondary accent (coral) | Coral/red | `#FF6B7A` |
| Tertiary accent (green) | Teal green | `#2DD4A8` |
| Tertiary accent (gold) | Warm yellow | `#F7C948` |
| Muted/neutral line | Dim white | `rgba(255, 255, 255, 0.5)` |
| Subtle borders | Visible white | `rgba(255, 255, 255, 0.25)` |
| Blue-tinted border | Accent border | `rgba(74, 158, 247, 0.55)` |
| Coral-tinted border | Accent border | `rgba(255, 107, 122, 0.55)` |

### Text Color Rules

**All readable text must be pure `#ffffff`.** This applies to:
- Headings, subtitles, body text, labels
- Chart axis numbers (y-axis: 0, 100, 200, etc.)
- Chart axis date/category labels (x-axis)
- Scorecard names, percentages, price labels
- Legend text, footer text
- End-of-line chart labels

Never use reduced-opacity white (`rgba(255,255,255,0.4)`, etc.) for any text that needs to be read. On the dark `#0a0e1a` background, anything below full white is too faint at 4K.

### Grid & Axis Line Colors

Chart grid lines must be visible against the dark background:

| Element | Color |
|---|---|
| Standard grid line | `rgba(255, 255, 255, 0.15)` |
| Baseline / reference line (e.g. "100" index) | `rgba(255, 255, 255, 0.35)` |
| X-axis tick marks | `rgba(255, 255, 255, 0.3)` |
| Chart area border | `rgba(255, 255, 255, 0.15)` |

**Never use `rgba(255, 255, 255, 0.06)` for grid lines** — this is effectively invisible on the dark background.

### Multi-Line Chart Colors

When showing multiple data series (e.g. comparing companies), use these colors in order:

| Series | Color | Stroke Width | Opacity |
|---|---|---|---|
| Primary / featured | `#F7C948` (gold) | `2.8px` | `1.0` |
| Series 2 | `#4A9EF7` (blue) | `1.6px` | `0.7` |
| Series 3 | `#5BAAFF` (bright blue) | `1.6px` | `0.7` |
| Series 4 | `#2DD4A8` (green) | `1.6px` | `0.7` |
| Series 5 | `#FF6B7A` (coral) | `1.6px` | `0.7` |
| Series 6 / neutral | `rgba(255,255,255,0.5)` | `1.6px` | `0.7` |

The featured/primary series should be drawn last (on top) and can have glow layers for emphasis. Glow layers must be hidden (`opacity: 0`) until their parent line animates in — no pre-animation ghost outlines.

### Bar Chart Color Pattern
- **Blue (#4A9EF7 / #5BAAFF)** is the dominant data color — used for chart bars, stat values, primary highlights
- **Coral (#FF6B7A)** is the contrast/callout color — used for rank badges, warnings, "X" marks, secondary highlights
- The **primary/leading bar** uses solid `#4A9EF7`; all other bars use `rgba(74, 158, 247, 0.35)` (same hue, lower opacity)

### Accent-Tinted Backgrounds

For scorecard or stat boxes that highlight the primary series:

| Variant | Border | Background |
|---|---|---|
| Gold-accent (featured) | `rgba(247, 201, 72, 0.55)` | `rgba(247, 201, 72, 0.06)` |
| Blue-accent | `rgba(74, 158, 247, 0.55)` | `rgba(74, 158, 247, 0.06)` |
| Standard | `rgba(255, 255, 255, 0.25)` | `rgba(8, 10, 22, 0.85)` |

---

## 4. Typography

### Font Stack

| Font | Usage | Import |
|---|---|---|
| **DM Sans** | All body text, labels, data values, chart text | Google Fonts |
| **Playfair Display** | Large serif headlines (special/dramatic layouts) | Google Fonts |
| **Instrument Serif** | Section titles for diagram/conceptual layouts | Google Fonts |

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap" rel="stylesheet">
```

### Type Scale

| Element | Size | Weight | Color |
|---|---|---|---|
| Page title (h1) | `26px` | `800` | `#ffffff` |
| Chart/card title (h2) | `13px` | `700` | `#ffffff` |
| Subtitle / card-sub | `13px` | `400` | `#ffffff` |
| Stat value (hero number) | `28px` | `800` | `#5BAAFF` |
| Stat label | `13px` | `400` | `#ffffff` |
| Stat rank badge | `13px` | `700` | `#FF6B7A` |
| Chart axis labels | `12-14px` | `400` | `#ffffff` |
| Chart data labels | `12px` | `bold` | `#ffffff` |
| Narrative counter | `28px` | `bold` | `#5BAAFF` |
| Footer text | `13px` | `400` | `#ffffff` |
| Section labels (uppercase) | `11px` | `600-700` | varies (accent color), `letter-spacing: 1.5-3px`, `text-transform: uppercase` |

### Label Content Rules
- **Always use full company/entity names** in legends, scorecards, end labels, and axis labels — never ticker symbols or abbreviations (e.g. "Goldman Sachs" not "GS", "JP Morgan Chase" not "JPM")
- Ticker symbols may be used as internal data keys but should never appear in the rendered output

### For Serif Title Layouts (Instrument Serif)
| Element | Size | Weight |
|---|---|---|
| Title | `clamp(28px, 4vw, 42px)` | `400` |
| Content is lighter, more editorial feel | | |

### For Dramatic Layouts (Playfair Display)
| Element | Size | Weight |
|---|---|---|
| Hero title | `38px` | `900` |
| Card title | `24px` | `700` |

---

## 5. Card / Panel System (Glassmorphism)

All cards and panels use this consistent glassmorphism treatment:

```css
.card {
  background: rgba(8, 10, 22, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 15px;         /* 15px for cards, 24px for hero/dramatic cards */
  padding: 30px;               /* 30-45px depending on card type */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);  /* or 0 4px 30px rgba(0,0,0,0.4) */
}
```

### Card Variants

| Type | Border Radius | Border | Padding | Notes |
|---|---|---|---|---|
| Data card (chart) | `10px` | `rgba(255,255,255,0.25)` | `20px` | Standard |
| Stat box | `10px` | `rgba(255,255,255,0.25)` + `border-left: 4px solid #4A9EF7` | `18px 14px` | Left accent stripe |
| Wrapper card | `12px` | `rgba(255,255,255,0.25)` | `30px 30px 20px` | Full-width content holder |
| Hero/dramatic card | `20px` | `rgba(255,255,255,0.25)` or accent-tinted | `30px 60px` | Larger, more prominent |
| Blue-accent card | `10px` | `rgba(74, 158, 247, 0.55)` | `28px 32px` | Blue-tinted border |
| Coral-accent card | `10px` | `rgba(255, 107, 122, 0.55)` | `28px 32px` | Coral-tinted border |

---

## 6. Grid Layouts

### Dashboard Layout (17.html style — multi-element)

```
┌──────────────────────────────────────────────┐
│                  HEADER (h1 + subtitle)       │
├──────────┬──────────┬──────────┬─────────────┤
│  Stat 1  │  Stat 2  │  Stat 3  │   Stat 4   │  ← stat-grid: 4 columns
├──────────┴──────────┼──────────┴─────────────┤
│     Chart Card 1    │      Chart Card 2      │  ← charts-grid: 2 columns
├─────────────────────┼────────────────────────┤
│     Chart Card 3    │      Chart Card 4      │
└─────────────────────┴────────────────────────┘
```

```css
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
```

### Single Chart Layout (18/19/20.html style)

```
┌────────────────────────────────────────────┐
│  .wrapper (960px wide)                     │
│  ┌──────────────────────────────────────┐  │
│  │  h1 title                            │  │
│  │  h2 subtitle (optional)              │  │
│  │  ┌──────────────────────────────┐    │  │
│  │  │  Chart Canvas (460px height) │    │  │
│  │  │                    [counter] │    │  │
│  │  └──────────────────────────────┘    │  │
│  │  footer (source, additional info)    │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

### Split / Two-Column Layout (20.2.html style)

```
         ┌──────────────────┐
         │   Top Card       │
         └────────┬─────────┘
              ╱         ╲          ← SVG split lines
         ╱                   ╲
┌─────────────┐    ┌─────────────┐
│  Left Card  │    │  Right Card │
└─────────────┘    └─────────────┘
```

### Comparison Layout (banking-accelerator-diagram2.html)

```css
.columns {
  display: grid;
  grid-template-columns: 1fr auto 1fr;  /* left | divider | right */
  align-items: center;
}
```

### Flow Diagram Layout (banking-accelerator-diagram.html)

```
[Top Block]
    ↓
[Node] → [Node] → [Node] → [Node]
```

Horizontal flow with arrows between nodes using flexbox.

---

## 7. Chart.js Configuration

All charts use **Chart.js v4.4.1** loaded from CDN:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
```

### Standard Bar Chart Config

```javascript
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: [...],
    datasets: [{
      data: [...],
      backgroundColor: '#4A9EF7',        // or array for per-bar colors
      borderWidth: 0,
      borderRadius: 2,                    // subtle rounding on bars (2-3px)
      barPercentage: 0.7,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,                     // IMPORTANT: disable built-in animation
    plugins: {
      legend: { display: false },
      tooltip: { enabled: true }
    },
    scales: {
      x: {
        grid: { display: false },
        border: { color: 'rgba(255,255,255,0.15)' },
        ticks: {
          color: '#ffffff',
          font: { size: 12, family: 'DM Sans' }
        }
      },
      y: {
        min: 0,
        max: ...,                         // set explicit max
        grid: { color: 'rgba(255,255,255,0.15)', lineWidth: 0.8 },
        border: { display: false },
        ticks: {
          color: '#ffffff',
          font: { size: 12, family: 'DM Sans' }
        }
      }
    },
    layout: { padding: { top: 22-30 } }  // space for data labels above bars
  }
});
```

### Per-Bar Color Pattern

The lead/primary data point uses solid blue; others use transparent blue:

```javascript
backgroundColor: [
  '#4A9EF7',                    // primary (leader)
  'rgba(74,158,247,0.35)',      // secondary
  'rgba(74,158,247,0.35)',
  'rgba(74,158,247,0.35)',
  'rgba(74,158,247,0.35)',
]
```

### Data Label Plugin (Above Bars)

```javascript
plugins: [{
  id: 'labels',
  afterDatasetDraw(chart) {
    const { ctx } = chart;
    chart.getDatasetMeta(0).data.forEach((bar, i) => {
      const val = chart.data.datasets[0].data[i];
      if (val < 0.5) return;           // skip zero bars
      ctx.save();
      ctx.font = `bold 12px DM Sans`;
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.fillText(formattedLabel, bar.x, bar.y - 5);
      ctx.restore();
    });
  }
}]
```

### Doughnut Chart Config

```javascript
new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: [...],
    datasets: [{
      data: [...],
      backgroundColor: ['#4A9EF7', '#FF6B7A', '#2DD4A8', '#F7C948'],
      borderWidth: 2,
      borderColor: 'rgba(8,10,22,0.85)',  // match card background
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 900, easing: 'easeOutQuart' },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          font: { size: 10, family: 'DM Sans' },
          padding: 10,
          boxWidth: 12,
          color: '#ffffff'
        }
      }
    }
  }
});
```

---

## 8. Animation System

### CRITICAL: All Animations Must Be JavaScript-Driven

**Do NOT use CSS `animation` or `transition` properties.** The recording pipeline hijacks JavaScript timing functions (`setTimeout`, `setInterval`, `requestAnimationFrame`) to control time precisely. CSS animations run on the browser's compositor thread and cannot be controlled by the pipeline.

### The Core `jsFadeIn` Function

Every file uses this same animation helper:

```javascript
function jsFadeIn(el, duration, translateFrom) {
  if (!el) return;
  let step = 0;
  const steps = Math.round(duration / 16);
  const iv = setInterval(() => {
    step++;
    const p = Math.min(step / steps, 1);
    const e = 1 - Math.pow(1 - p, 3);  // cubic ease-out
    el.style.opacity = String(e);
    if (translateFrom !== undefined) {
      el.style.transform = 'translateY(' + (translateFrom * (1 - e)) + 'px)';
    }
    if (p >= 1) {
      clearInterval(iv);
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }
  }, 16);  // ~60fps tick rate
}
```

### Easing Function

All animations use **cubic ease-out**: `1 - Math.pow(1 - progress, 3)`

This creates a fast start that decelerates smoothly.

### Count-Up Animation (for stat values)

```javascript
function countUp(el, target, suffix, prefix, duration, decimals = 0) {
  const steps = Math.round(duration / 16);
  let step = 0;
  const interval = setInterval(() => {
    step++;
    const progress = step / steps;
    const eased = 1 - Math.pow(1 - progress, 3);
    const val = target * eased;
    el.textContent = prefix + (decimals ? val.toFixed(decimals) : Math.round(val)) + suffix;
    if (step >= steps) {
      clearInterval(interval);
      el.textContent = prefix + (decimals ? target.toFixed(decimals) : target) + suffix;
    }
  }, 16);
}
```

### Chart Bar Rise Animation

Bars grow from 0 to their final value over ~800ms with cubic ease-out:

```javascript
function animateBar(chart, data, delay) {
  setTimeout(() => {
    const steps = 50;
    let step = 0;
    const iv = setInterval(() => {
      step++;
      const eased = 1 - Math.pow(1 - step / steps, 3);
      chart.data.datasets[0].data = data.map(v => v * eased);
      chart.update('none');  // 'none' disables Chart.js built-in animation
      if (step >= steps) {
        clearInterval(iv);
        chart.data.datasets[0].data = data;
        chart.update('none');
      }
    }, 16);
  }, delay);
}
```

### Sequential Bar-by-Bar Animation (18/19/20.html pattern)

Bars rise one at a time, left to right, with a running counter:

```javascript
function animateBar(barIndex) {
  if (barIndex >= totalBars) return;
  const targetVal = finalData[barIndex];
  const steps = Math.round((160 / 1000) * 60);  // 160ms rise per bar
  let step = 0;
  const interval = setInterval(() => {
    step++;
    const eased = 1 - Math.pow(1 - step / steps, 3);
    chart.data.datasets[0].data[barIndex] = targetVal * eased;
    chart.update('none');
    counter.textContent = `$${Math.round(Math.max(...chart.data.datasets[0].data))}B`;
    if (step >= steps) {
      clearInterval(interval);
      setTimeout(() => animateBar(barIndex + 1), 50);  // 50ms pause between bars
    }
  }, 1000 / 60);
}
```

---

## 9. Animation Timeline

### Standard Timing Pattern

All elements start invisible (`opacity: 0`) in CSS and are animated in via JavaScript `setTimeout` chains:

| Time (ms) | Event | Animation |
|---|---|---|
| **100** | First element appears (title/header) | `jsFadeIn(header, 700, -16)` — starts immediately |
| **500 - 900** | Primary content fades in | Nodes, cards, wrapper elements with 80-100ms stagger |
| **900 - 1600** | Secondary content + connectors | Arrows, stat boxes, chart cards with stagger |
| **1600 - 2500** | Data animations | Bar rises, count-ups, labels |
| **2500 - 3500** | Tertiary elements | Footers, supplementary labels |
| **3500 - 15000** | Hold — everything fully visible | Animation complete, hold for viewer to absorb |

### Key Rules:

1. **Animation starts at 100ms** — first element appears almost immediately, no blank lead-in
2. **Elements always start with `opacity: 0` in CSS** — they are invisible until JS animates them
3. **Stagger between related elements is 80-100ms** — fast enough to feel cohesive, slow enough to register
4. **Individual element fade-in duration is 400-800ms**
5. **Count-up duration is 700ms** for stat numbers
6. **Last several seconds should be a hold** — all elements fully visible, no movement

### Direction Convention:

| Element Type | Translate Direction |
|---|---|
| Headers/titles | Slide DOWN from above: `translateY(-16px)` to `0` |
| Cards, stat boxes, content | Slide UP from below: `translateY(16-30px)` to `0` |
| Footers, subtle elements | No translate, opacity only |

---

## 10. Initial CSS State for Animated Elements

Every element that will be animated MUST start invisible:

```css
.header {
  opacity: 0;
  transform: translateY(-16px);  /* starting position */
}

.stat-box {
  opacity: 0;
  transform: translateY(16px);
}

.card {
  opacity: 0;
  transform: translateY(20px);
}

.wrapper {
  opacity: 0;  /* for single-chart layouts */
}
```

---

## 11. Narrative Counter (Single-Chart Layouts)

For time-series bar charts, include a live counter in the top-right of the chart area:

```html
<div class="narrative" id="narrative">
  <div class="counter" id="counter">$0B</div>
  <div class="counter-label">Total Assets</div>
</div>
```

```css
.narrative {
  position: absolute;
  top: 10px;
  right: 10px;
  text-align: right;
  opacity: 0;
}
.narrative .counter {
  font-size: 28px;
  font-weight: bold;
  color: #5BAAFF;
}
.narrative .counter-label {
  font-size: 13px;
  color: #ffffff;
  letter-spacing: 1px;
  text-transform: uppercase;
}
```

This counter updates in real-time as bars animate, showing the current maximum value.

---

## 12. Footer Pattern

```html
<div class="footer">
  <div class="footer-col">
    <p>Source</p>
    <p>JPMorgan Chase</p>
  </div>
  <div class="footer-col">
    <p>Additional Information:</p>
    <p>Worldwide; JPMorgan Chase; 2007 to 2025</p>
  </div>
</div>
```

```css
.footer {
  display: flex;
  gap: 60px;
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.25);
  opacity: 0;  /* animated in late */
}
.footer-col p {
  font-size: 13px;
  color: #ffffff;
  line-height: 1.6;
}
.footer-col p:first-child {
  font-weight: bold;
  color: #ffffff;
}
```

---

## 13. Special Effects (Advanced)

### Flash Overlay (for dramatic moments like 20.2.html)

```javascript
function doFlash() {
  flash.style.opacity = '0.25';
  setTimeout(() => {
    let step = 0;
    const steps = Math.round(120 / 16);
    const iv = setInterval(() => {
      step++;
      const p = Math.min(step / steps, 1);
      flash.style.opacity = String(0.25 * (1 - p));
      if (p >= 1) { clearInterval(iv); flash.style.opacity = '0'; }
    }, 16);
  }, 120);
}
```

### Particle Burst

Spawn 24 small colored dots that fly outward from a center point:

```javascript
function spawnParticles() {
  const colors = ['#FF6B7A', '#4A9EF7', '#ffffff', '#5BAAFF'];
  for (let i = 0; i < 24; i++) {
    // Create div, animate outward with fading opacity
    // Duration: 500-1000ms, random angles, eased movement
  }
}
```

### SVG Arrows — Group-Opacity Convention

**Never use stroke-dasharray/dashoffset animation on lines with `marker-end` arrowheads.** The arrowhead renders at the mathematical endpoint regardless of dash offset, causing the arrowhead to appear before the line reaches it. Also avoid individually semi-transparent stroke/fill colors on arrows — overlapping regions cause double-alpha bleed-through.

**Correct pattern:** Use solid colors on strokes and arrowhead fills. Wrap each arrow (line + marker) in a `<g>` group. Control transparency by fading the group's opacity.

```css
/* Solid colors — transparency controlled at <g> group level */
.flow-svg line, .flow-svg path {
  stroke: #ffffff;
  stroke-width: 1.8;
  fill: none;
}

.flow-svg .arrowhead {
  fill: #ffffff;
  stroke: none;
}
```

```html
<svg class="flow-svg" viewBox="0 0 1200 384">
  <defs>
    <marker id="ah1" markerWidth="10" markerHeight="7" refX="10" refY="4" orient="auto">
      <polygon points="0 0, 10 4, 0 7" class="arrowhead"/>
    </marker>
  </defs>

  <!-- Each arrow wrapped in a <g> with opacity="0" -->
  <g id="arrow1" opacity="0">
    <line x1="198" y1="192" x2="270" y2="192" marker-end="url(#ah1)"/>
  </g>
</svg>
```

```javascript
// Fade the GROUP to 0.25 — line + arrowhead composite as a single unit
jsFadeOpacity(document.getElementById('arrow1'), 400, 0, 0.25);
```

**For colored arrows** (gold, teal, etc.), use solid accent colors with per-class overrides, still controlling transparency at the group level:

```css
.flow-svg .arrow-gold line, .flow-svg .arrow-gold path { stroke: #F7C948; }
.flow-svg .arrowhead-gold { fill: #F7C948; stroke: none; }
```

```html
<g id="arrow-gold" class="arrow-gold" opacity="0">
  <path d="M 720 190 Q 744 72, 576 50" marker-end="url(#ah-gold)"/>
</g>
```

**Decorative dashed/dotted lines** (visual style, not animation) can still use `stroke-dasharray: 6,4` on the line element itself — this is a visual pattern, not an animation technique.

### SVG Line Draw (stroke-dashoffset) — Decorative Lines Only

Use stroke-dashoffset animation **only for decorative lines without arrowheads** (e.g., split dividers, connecting lines):

```javascript
function jsStrokeDash(el, duration, from, to) {
  let step = 0;
  const steps = Math.round(duration / 16);
  const iv = setInterval(() => {
    step++;
    const p = Math.min(step / steps, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.style.strokeDashoffset = String(from + (to - from) * e);
    if (p >= 1) { clearInterval(iv); }
  }, 16);
}
```

**Do NOT use this for arrows with `marker-end`.** Use the group-opacity pattern above instead.

### Glow Pulse (continuous)

```javascript
function jsGlowPulse(el) {
  let t = 0;
  setInterval(() => {
    t += 16;
    const p = (Math.sin(t / 1000 * Math.PI) + 1) / 2;
    const spread = 4 + 26 * p;
    const alpha = 0.3 + 0.15 * p;
    el.style.boxShadow = `0 0 ${spread}px rgba(74,158,247,${alpha})`;
  }, 16);
}
```

---

## 14. Complete HTML Template

Use this as a starting point for new files:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your Title Here</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0a0e1a;
    font-family: 'DM Sans', sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 40px;
    overflow: hidden;
  }

  #bg-video {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    object-fit: cover;
    z-index: 0;
  }

  .page {
    position: relative;
    z-index: 1;
    max-width: 1200px;
    margin: 0 auto;
  }

  /* --- Add your element styles here --- */
  /* Remember: every animated element needs opacity: 0 in CSS */

</style>
</head>
<body>
<video autoplay muted loop playsinline id="bg-video">
  <source src="Wavy Grid Background.mp4" type="video/mp4">
</video>

<div class="page">
  <!-- Your content here -->
</div>

<script>
const fontFamily = 'DM Sans';

// === ANIMATION HELPERS (copy these exactly) ===

function jsFadeIn(el, duration, translateFrom) {
  if (!el) return;
  let step = 0;
  const steps = Math.round(duration / 16);
  const iv = setInterval(() => {
    step++;
    const p = Math.min(step / steps, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.style.opacity = String(e);
    if (translateFrom !== undefined) {
      el.style.transform = 'translateY(' + (translateFrom * (1 - e)) + 'px)';
    }
    if (p >= 1) {
      clearInterval(iv);
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }
  }, 16);
}

function countUp(el, target, suffix, prefix, duration, decimals = 0) {
  const steps = Math.round(duration / 16);
  let step = 0;
  const interval = setInterval(() => {
    step++;
    const progress = step / steps;
    const eased = 1 - Math.pow(1 - progress, 3);
    const val = target * eased;
    el.textContent = prefix + (decimals ? val.toFixed(decimals) : Math.round(val)) + suffix;
    if (step >= steps) {
      clearInterval(interval);
      el.textContent = prefix + (decimals ? target.toFixed(decimals) : target) + suffix;
    }
  }, 16);
}

// === ANIMATION TIMELINE ===
// 100ms: first element appears
// Stagger related elements by 80-100ms
// Hold final state for remaining seconds

setTimeout(() => {
  // Animate elements in...
}, 100);
</script>
</body>
</html>
```

---

## 15. Checklist: Before Submitting a New HTML File

- [ ] Body background is `#0a0e1a`
- [ ] Background video element with `id="bg-video"` is present
- [ ] All content is in a `z-index: 1` wrapper
- [ ] Font is DM Sans (loaded from Google Fonts)
- [ ] All animated elements have `opacity: 0` in CSS
- [ ] All animations use `setInterval` at 16ms — NO CSS `animation` or `transition`
- [ ] Easing is `1 - Math.pow(1 - p, 3)` (cubic ease-out)
- [ ] Animation starts at 100ms (no blank lead-in)
- [ ] Last 2-3 seconds are a hold (all elements fully visible)
- [ ] Cards use glassmorphism: `rgba(8,10,22,0.85)` + `backdrop-filter: blur(16px)`
- [ ] Blue accent: `#4A9EF7` / `#5BAAFF`
- [ ] Coral accent: `#FF6B7A`
- [ ] **All readable text is pure `#ffffff`** — no reduced-opacity white for text
- [ ] **Grid lines use `rgba(255,255,255,0.15)` minimum** — not 0.06
- [ ] **Labels use full names** — no ticker abbreviations in rendered output
- [ ] Glow/shadow layers hidden until parent element animates (no ghost outlines)
- [ ] Chart.js has `animation: false` (built-in animation disabled)
- [ ] Charts use the custom bar-rise animation via `setInterval`
- [ ] No CSS transitions or keyframes (exception: purely decorative non-timed effects)
- [ ] Works at 1920x1080 viewport — no scrolling, no overflow
