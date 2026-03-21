# Animation Proposal Generator

Generate an HTML report proposing diagram/animation overlays for each a-roll clip. The user will review the report and choose which ones to build as HTML animations using the `html_to_video/` pipeline.

## When to Run

Only when the user explicitly asks (e.g., "propose animations", "suggest diagrams", "run the animation proposals").

## Input Files

All paths relative to project root (`/Users/danielko/dev/rareliquid-editor/`).

| File | Purpose |
|------|---------|
| `files/input/script.txt` | Full video script — provides overall context, section structure, narrative arc |
| `files/output/aroll/edit_points.json` | Clip list with `source_file`, `source_start`, `source_end`, `tight_duration_seconds` |
| `files/output/cache/{FILE_ID}.transcript.json` | Whisper transcripts with word-level timing per source file |

## Step-by-Step Process

### 1. Read the full script

Read `files/input/script.txt` to understand:
- The video topic and thesis
- Section structure (HOOK, PROMISE, sections, OUTRO)
- What data, statistics, processes, comparisons, or concepts are discussed
- Where b-roll references already exist (these clips already have visuals)

### 2. Build the clip manifest

Read `files/output/aroll/edit_points.json`. For each clip, extract:
- `filename` (clip identifier)
- `order` (sequence position)
- `source_file` (e.g., `C1381.MP4`)
- `source_start` / `source_end` (timecodes in the source)
- `tight_duration_seconds` (how long the clip actually is)

### 3. Extract transcript text per clip

For each clip, read `files/output/cache/{FILE_ID}.transcript.json` where `FILE_ID` is `source_file` without extension (e.g., `C1381`).

From the transcript's `segments` array, find all segments that overlap with `[source_start, source_end]` and concatenate their text. This is the **clip transcript** — the exact words spoken in that clip.

### 4. Evaluate each clip for animation potential

For each clip, decide: **does this clip benefit from a visual overlay?**

**GOOD candidates** (propose an animation):
- Statistics, numbers, percentages, financial figures
- Comparisons (A vs B, before/after, two groups)
- Processes or sequences (step 1 → step 2 → step 3)
- Lists of items (top 5 banks, 3 strategies, etc.)
- Timelines or historical progressions
- Hierarchies or organizational structures
- Geographic or categorical breakdowns

**SKIP these** (no animation needed):
- Pure narrative/storytelling with no data
- Emotional/personal anecdotes
- Clips shorter than 4 seconds (not enough time for an animation to land)
- Clips where b-roll is already referenced in the script for that section
- Introductions, transitions, outros that are purely verbal
- Clips that repeat information already visualized in a prior proposal

### 5. For each good candidate, write a proposal

Each proposal must include:
- **Clip reference**: filename and order number
- **Transcript excerpt**: the exact words spoken
- **Animation type**: one of the design system layouts (see below)
- **What to show**: specific data points, labels, numbers to display
- **Brief description**: 1-2 sentences on how the animation plays out
- **Why it helps**: what this visual adds that the speaker's words alone don't convey

### 6. Animation Types (from the design system)

Reference `html_to_video/DESIGN_GUIDE.md` for full specs. Available types:

| Type | Best For | Example |
|------|----------|---------|
| **Dashboard** | Multiple stats at once (3-6 numbers) | 4-column stat grid with count-up |
| **Single Chart** | One key data comparison | Bar chart with sequential rise, narrative counter |
| **Split Layout** | A vs B comparison | Two-column with SVG divider |
| **Flow Diagram** | Processes, sequences | Horizontal nodes with connecting arrows |
| **Comparison Grid** | Categories side by side | Left/right cards with center divider |
| **Simple Counter** | One big number | Hero stat with supporting context |
| **Timeline** | Chronological progression | Horizontal timeline with milestone dots |
| **List Reveal** | Enumerating items | Staggered card fade-in |

Keep it simple. Prefer the simplest type that communicates the point. A single counter is better than a dashboard if there's only one number.

### 7. Generate the HTML report

Write the report to `html_to_video/animation_proposals.html`.

The HTML document must be:
- Clean, readable, dark-themed (matches the design system aesthetic)
- Two-column layout per proposal: **left = clip info**, **right = animation idea**
- Clips that are skipped should NOT appear
- Include the full video title/topic at the top for context
- Number each proposal for easy reference

**HTML structure:**

```
┌─────────────────────────────────────────────────────┐
│  Animation Proposals: [Video Title]                 │
│  [X] clips analyzed · [Y] proposals generated       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─── Proposal 1 ──────────────────────────────┐   │
│  │ LEFT COLUMN          │ RIGHT COLUMN          │   │
│  │                      │                       │   │
│  │ Clip: 004_C1384...   │ Type: Single Chart    │   │
│  │ Order: #4             │                       │   │
│  │ Duration: 5.2s       │ Show: Bar chart of    │   │
│  │                      │ top 5 banks by assets │   │
│  │ Transcript:          │                       │   │
│  │ "JPMorgan alone      │ Description: Bars     │   │
│  │  holds 3.4 trillion  │ rise sequentially,    │   │
│  │  in assets..."       │ JPM highlighted in    │   │
│  │                      │ blue, others dimmed.  │   │
│  │                      │ Counter shows total.  │   │
│  │                      │                       │   │
│  │                      │ Why: Gives scale to   │   │
│  │                      │ the "3.4 trillion"    │   │
│  │                      │ number the viewer     │   │
│  │                      │ just heard.           │   │
│  └──────────────────────┴───────────────────────┘   │
│                                                     │
│  ┌─── Proposal 2 ──────────────────────────────┐   │
│  │ ...                                          │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Styling requirements:**
- Background: `#0a0e1a` (matches design system)
- Cards: glassmorphism (`rgba(15, 20, 40, 0.7)`, `backdrop-filter: blur(16px)`, `border: 1px solid rgba(255,255,255,0.08)`)
- Text: `#e0e0e0` body, `#4A9EF7` for accents/labels, `#FF6B7A` for animation type badges
- Font: system sans-serif is fine for the report itself
- Responsive: should look good at 1200px+ width
- Each proposal card is visually distinct and easy to scan

## Important Notes

- Read the ENTIRE script first for context before evaluating any clip. A clip about "the merger" only makes sense if you know what merger the video is about.
- Be selective. Not every clip needs an animation. A video with 38 clips might only have 8-15 good animation candidates. Quality over quantity.
- Think about what the VIEWER needs to see. If the speaker says "there are three steps," the viewer benefits from seeing those three steps. If the speaker says "I was nervous," no visual needed.
- Each animation will be 15 seconds and overlaid on the speaker footage. Keep designs that work as transparent overlays — they'll share screen space with the talking head.
- **Sizing:** All dimensions must be 30% larger than standard web sizes (see DESIGN_GUIDE.md "Size scale" rule). This is critical for 4K readability.
- **Timing:** First animation event starts at 100ms. No 2-second blank lead-in.
- **Naming:** HTML files must be named `{NNN}_{description}.html` where `{NNN}` is the 3-digit a-roll clip number (e.g. `001_99_percent.html`, `023_recruiting_funnel.html`).
- Reference the previous examples in `html_to_video/HTML Files/Previous Examples/` to understand the quality and complexity bar.
