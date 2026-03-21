# HTML → 4K ProRes Video Pipeline

## QUICK START

```bash
# First run only:
npm ci

# Then:
node record.js                    # transparent alpha videos only
node record.js --with-background  # also composite over background video
```

---

## WHAT THIS PROJECT DOES

Converts animated HTML files (JS-driven animations with optional `<video id="bg-video">`) into 4K ProRes videos.

For each `.html` file in `HTML Files/`, it produces in `HTML Files/Output/`:
1. `{name}_alpha.mov` — ProRes 4444 with transparent background (for compositing in DaVinci Resolve)
2. `{name}.mov` — ProRes HQ composited over `Wavy Grid Background.mp4` (only with `--with-background`)

---

## FILE STRUCTURE

```
/app/
├── record.js                    # Main pipeline script
├── CLAUDE.md                    # This file — READ IT FIRST
├── DESIGN_GUIDE.md              # Visual design system & animation patterns
├── alphafix.sh                  # Mac-side ProRes alpha re-encoder
├── Dockerfile
├── run.sh                       # Docker launcher
├── package.json
├── .gitignore
├── Wavy Grid Background.mp4     # Background video for composites
└── HTML Files/
    ├── 17.html
    ├── 18.html
    ├── 19.html
    ├── 20.html
    ├── 20.2.html
    ├── banking-accelerator-diagram.html
    ├── banking-accelerator-diagram2.html
    └── Output/                  # All .mov output goes here
        ├── 17_alpha.mov
        ├── 17.mov
        └── ...
```

---

## HOW THE CAPTURE WORKS: `addInitScript` Timer Hijacking

The HTML animations are 100% JS-driven (`setTimeout`, `setInterval`, `requestAnimationFrame`, Chart.js). The pipeline uses `page.addInitScript()` to hijack all JavaScript timing functions **before** the page loads:

- `setTimeout`, `setInterval`, `requestAnimationFrame` are replaced with custom implementations
- `performance.now()` and `Date.now()` return controlled virtual time
- `window.__advanceTime(ms)` advances the clock, firing all callbacks in chronological order
- Each frame: advance clock by `FRAME_MS` (33.33ms at 30fps), wait 5ms for repaint, take screenshot

This gives **frame-perfect deterministic capture** — animations play at exactly the right speed regardless of how long screenshots take. It works because these HTML files use only JS-based animation (no CSS `animation` or `transition`).

```javascript
// Per-frame capture loop (simplified)
for (let i = 0; i < TOTAL_FRAMES; i++) {
  await page.evaluate((ms) => window.__advanceTime(ms), FRAME_MS);
  await page.waitForTimeout(5);  // let browser repaint
  await page.screenshot({ path: framePath, type: 'png', omitBackground: true });
}
```

---

## DEFAULTS

| Setting | Value |
|---------|-------|
| FPS | 30 |
| Duration | 15 seconds |
| Total frames | 450 |
| Viewport | 1920×1080 |
| Scale factor | 2 (→ 3840×2160 4K) |
| Output dir | `HTML Files/Output/` |

---

## KNOWN BUGS AND THEIR FIXES

### BUG 1: Sped-Up Animations

**Root cause:** Playwright's `page.clock.install()` / `page.clock.runFor()` only controls JS timers partially — it doesn't integrate cleanly with `requestAnimationFrame` or `performance.now()` in all cases, and doesn't handle the interleaving of timer callbacks correctly for these animations.

**Also bad:** CSS `animation: none !important` or `transition: none !important` — kills animations entirely.

**Also bad:** Real-time wall-clock pacing (sleeping between screenshots) — screenshots take variable time, causing drift and speed inconsistencies.

**Fix:** The `addInitScript` timer-hijacking approach described above. All timing functions are replaced with controlled versions before the page loads. `__advanceTime(ms)` fires callbacks in exact chronological order, giving deterministic frame-perfect capture.

### BUG 2: Alpha Transparency (7-Layer Problem)

ALL of these must be correct simultaneously. If any layer fails, you get opaque black:

| Layer | What | How |
|-------|-------|-----|
| 1 | PNG format | `type: 'png'` (JPEG has no alpha) |
| 2 | Omit browser bg | `omitBackground: true` |
| 3 | HTML/body transparent | CSS `!important` + JS `.setProperty()` |
| 4 | Video element hidden | `display: none !important` (not just `.pause()`) |
| 5 | Wrapper divs transparent | Find full-viewport divs and clear their backgrounds |
| 6 | ProRes 4444 encode | `-profile:v 4 -pix_fmt yuva444p10le -alpha_bits 16` |
| 7 | No CSS gradients/pseudo-elements | Check for `::before`/`::after` creating opaque overlays |

### BUG 3: Composited Video Wrong Framerate

**Root cause:** FFmpeg inherits the background video's framerate (23.98fps) instead of using 30fps.

**Fix:** Add `-r ${FPS}` to the composited FFmpeg command.

### BUG 4: ProRes Alpha Not Working in DaVinci Resolve on Apple Silicon

**Root cause:** FFmpeg `prores_ks` on Linux produces alpha files that macOS Sonoma 14.4+ hardware ProRes decoder on Apple Silicon ignores. The alpha data is correct but the container atoms aren't flagged the way Apple expects.

**Fix:** Run `alphafix.sh` on your Mac after Docker finishes — it re-encodes using `prores_videotoolbox` (Apple's hardware encoder).

---

## AUTO-DISCOVERY

The FILES array auto-discovers HTML files (not hardcoded):

```javascript
const FILES = fs.readdirSync(HTML_DIR)
  .filter(f => f.endsWith('.html'))
  .map(f => f.replace(/\.html$/, ''))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
```

---

## FFMPEG COMMANDS

### Alpha (ProRes 4444):
```bash
ffmpeg -y -framerate 30 -i "frames/%05d.png" \
  -c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le \
  -alpha_bits 16 -vendor apl0 \
  "output_alpha.mov"
```

### Composited (ProRes HQ):
```bash
ffmpeg -y \
  -ss 0 -t 10 -i "background.mp4" \
  -framerate 30 -i "frames/%05d.png" \
  -filter_complex "[0:v]scale=3840:2160:flags=lanczos[bg];[1:v]scale=3840:2160:flags=lanczos[fg];[bg][fg]overlay=0:0:format=auto" \
  -r 30 -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 \
  -t 10 "output.mov"
```

Note the `-r 30` on the composited command — without it, FFmpeg inherits 23.98fps from the background video.

---

## VERIFICATION CHECKLIST

After encoding, verify:

1. **Alpha pixel format:** `ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt -of csv=p=0 "file_alpha.mov"` → must contain `yuva`
2. **Frame rate:** `ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "file.mov"` → must be `30/1`
3. **Resolution:** must be `3840x2160`
4. **Frame count:** must be `300` (30fps × 10s)
5. **PNG frames have alpha:** `ffprobe ... "frame.png"` → must show `rgba`

---

## DOCKER ENVIRONMENT NOTES

- Run as host UID: `-u $(id -u):$(id -g)` so mounted files have correct ownership
- Mount entire repo: `-v "$(pwd):/app"` so edits sync both ways
- Playwright browsers: `ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers` (set in Dockerfile)
- FFmpeg: latest static build from BtbN/FFmpeg-Builds at `/usr/local/bin/ffmpeg`

---

## THINGS YOU MUST NEVER DO

1. `page.clock.install()` or `page.clock.runFor()` — doesn't handle rAF/performance.now correctly for these animations
2. CSS `animation: none !important` or `transition: none !important` — kills animations
3. Real-time wall-clock pacing (sleeping between screenshots) — drift and speed inconsistencies
4. `type: 'jpeg'` for screenshots — no alpha channel
5. Forget `omitBackground: true` — white background baked in
6. `deviceScaleFactor: 3.2` — that's 6K, use `2` for 4K
7. `-profile:v 3` for alpha output — ProRes HQ has no alpha, must use profile 4
8. `yuv422p10le` or `yuv444p10le` for alpha — needs the `a` in `yuva444p10le`
9. Just `v.pause()` without `display: none` — paused video still renders as opaque
10. `style.background = 'transparent'` without `!important` — won't override stylesheets
11. Skip the `-r 30` on composited encode — inherits wrong framerate from background video

---

## DESIGN GUIDE

See `DESIGN_GUIDE.md` for the complete visual design system: color palette, typography, card styles, Chart.js configuration, animation patterns, and HTML templates.

Key rule: **All animations must be JS-driven** (`setInterval`/`setTimeout`/`requestAnimationFrame`). No CSS `animation` or `transition`. This is required for the `addInitScript` timer hijacking to work.

---

## ITERATIVE DEBUG WORKFLOW

```
1. Clean: rm -rf frames_* && rm -f "HTML Files/Output/"*.mov
2. Run: node record.js
3. If crash → read error, fix, go to 1
4. Verify alpha: check pix_fmt contains "yuva"
5. Verify speed: extract frames at 0s, 5s, 10s — should show different animation states
6. Verify framerate: ffprobe shows 30/1, frame count is 300
7. If any check fails → diagnose, fix record.js, go to 1
8. If all pass → DONE
```
