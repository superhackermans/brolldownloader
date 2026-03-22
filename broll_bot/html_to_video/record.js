const { chromium } = require('playwright');
const path = require('path');
const { execSync } = require('child_process');
const fs = require('fs');

const DIR = __dirname;
const HTML_DIR = path.join(DIR, 'HTML Files');
const OUTPUT_DIR = path.join(HTML_DIR, 'Output');
const FPS = 30;
const durationIdx = process.argv.indexOf('--duration');
const DURATION_SEC = durationIdx !== -1 && process.argv[durationIdx + 1]
  ? parseInt(process.argv[durationIdx + 1], 10)
  : 15;
const TOTAL_FRAMES = FPS * DURATION_SEC;
const FRAME_MS = 1000 / FPS;

const VIEWPORT_WIDTH = 1920;
const VIEWPORT_HEIGHT = 1080;
const SCALE_FACTOR = 2;
const OUTPUT_WIDTH = VIEWPORT_WIDTH * SCALE_FACTOR;
const OUTPUT_HEIGHT = VIEWPORT_HEIGHT * SCALE_FACTOR;

const WITH_BACKGROUND = process.argv.includes('--with-background');

// --files p1,p3,p7  or  --files p1_99_percent  (comma-separated prefixes/names, no .html)
const filesIdx = process.argv.indexOf('--files');
const filesFilter = filesIdx !== -1 && process.argv[filesIdx + 1]
  ? process.argv[filesIdx + 1].split(',').map(s => s.trim())
  : null;

const ALL_FILES = fs.readdirSync(HTML_DIR)
  .filter(f => f.endsWith('.html'))
  .map(f => f.replace(/\.html$/, ''))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

const FILES = filesFilter
  ? ALL_FILES.filter(f => filesFilter.some(prefix => f === prefix || f.startsWith(prefix + '_')))
  : ALL_FILES;

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// ============================================================
// INIT SCRIPT: Hijacks ALL timing functions before page loads.
//
// This gives us frame-perfect control. The browser's clock is
// frozen at t=0. We advance it manually via __advanceTime(ms),
// which fires setTimeout/setInterval/rAF callbacks in the
// correct chronological order.
//
// Why this works: the HTML animations are 100% JS-driven
// (setInterval at 16ms, setTimeout for sequencing, Chart.js
// uses rAF internally). By controlling these functions, we
// control exactly when each animation tick fires — regardless
// of how long screenshots take in wall-clock time.
// ============================================================
const INIT_SCRIPT = () => {
  let now = 0;
  const epoch = Date.now();
  let idCounter = 1;
  const timers = new Map();
  const rafs = [];

  performance.now = () => now;
  Date.now = () => epoch + now;

  window.setTimeout = (fn, delay = 0, ...args) => {
    const id = idCounter++;
    timers.set(id, {
      fn: typeof fn === 'function' ? () => fn(...args) : () => {},
      time: now + Math.max(0, delay),
      repeat: 0,
    });
    return id;
  };
  window.clearTimeout = id => timers.delete(id);

  window.setInterval = (fn, interval = 16, ...args) => {
    const id = idCounter++;
    timers.set(id, {
      fn: typeof fn === 'function' ? () => fn(...args) : () => {},
      time: now + Math.max(1, interval),
      repeat: Math.max(1, interval),
    });
    return id;
  };
  window.clearInterval = id => timers.delete(id);

  window.requestAnimationFrame = cb => {
    const id = idCounter++;
    rafs.push({ id, cb });
    return id;
  };
  window.cancelAnimationFrame = id => {
    const i = rafs.findIndex(r => r.id === id);
    if (i >= 0) rafs.splice(i, 1);
  };

  window.__advanceTime = ms => {
    const target = now + ms;
    let loops = 0;

    while (loops++ < 100000) {
      let earliest = null;
      let earliestId = null;

      for (const [id, t] of timers) {
        if (t.time <= target && (!earliest || t.time < earliest.time)) {
          earliest = t;
          earliestId = id;
        }
      }

      if (!earliest) break;

      now = earliest.time;
      if (earliest.repeat > 0) {
        earliest.time = now + earliest.repeat;
      } else {
        timers.delete(earliestId);
      }

      try { earliest.fn(); } catch (e) { console.error(e); }
    }

    now = target;

    // Fire all pending rAF callbacks at the new time
    const pending = rafs.splice(0);
    pending.forEach(({ cb }) => {
      try { cb(now); } catch (e) { console.error(e); }
    });
  };

  window.__getTime = () => now;
};

(async () => {
  console.log(`\nHTML → 4K Video Pipeline`);
  console.log(`Resolution: ${OUTPUT_WIDTH}×${OUTPUT_HEIGHT}`);
  console.log(`${TOTAL_FRAMES} frames @ ${FPS}fps = ${DURATION_SEC}s`);
  console.log(`Mode: transparent${WITH_BACKGROUND ? ' + background' : ' only'}`);
  console.log(`Files: ${FILES.join(', ')}`);
  console.log(`Output: ${OUTPUT_DIR}\n`);

  const browser = await chromium.launch({
    args: [
      '--autoplay-policy=no-user-gesture-required',
      '--disable-web-security',
      '--allow-file-access-from-files',
    ],
  });

  for (const file of FILES) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`  ${file}.html`);
    console.log(`${'='.repeat(60)}`);

    const framesDir = path.join(DIR, `frames_${file}`);
    fs.mkdirSync(framesDir, { recursive: true });

    const context = await browser.newContext({
      viewport: { width: VIEWPORT_WIDTH, height: VIEWPORT_HEIGHT },
      deviceScaleFactor: SCALE_FACTOR,
    });
    const page = await context.newPage();

    // Inject time control BEFORE page loads
    await page.addInitScript(INIT_SCRIPT);

    const filePath = path.join(HTML_DIR, `${file}.html`);
    if (!fs.existsSync(filePath)) {
      console.error(`  ERROR: ${filePath} not found. Skipping.`);
      await context.close();
      continue;
    }

    console.log(`  Loading...`);
    await page.goto(`file://${filePath}`, { waitUntil: 'load' });

    // Real-time pause for browser to finish layout/paint after resource load
    await new Promise(r => setTimeout(r, 1000));

    // Flush any t=0 initialization timers (rAF, setTimeout(fn, 0), etc.)
    await page.evaluate(() => window.__advanceTime(0));

    // --- TRANSPARENCY SETUP ---
    await page.evaluate(() => {
      const v = document.getElementById('bg-video');
      if (v) {
        v.pause();
        v.removeAttribute('autoplay');
        v.style.setProperty('display', 'none', 'important');
      }
    });

    await page.addStyleTag({
      content: `
        html, body {
          background: transparent !important;
          background-color: transparent !important;
          background-image: none !important;
        }
        #bg-video, video { display: none !important; }
      `
    });

    await page.evaluate(() => {
      document.documentElement.style.setProperty('background', 'transparent', 'important');
      document.documentElement.style.setProperty('background-color', 'transparent', 'important');
      document.body.style.setProperty('background', 'transparent', 'important');
      document.body.style.setProperty('background-color', 'transparent', 'important');

      document.querySelectorAll('body > div, body > section, body > main, .container, .wrapper, #app, .page, .content')
        .forEach(el => {
          const bg = window.getComputedStyle(el).backgroundColor;
          if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
            const r = el.getBoundingClientRect();
            if (r.width >= window.innerWidth * 0.9 && r.height >= window.innerHeight * 0.9) {
              el.style.setProperty('background', 'transparent', 'important');
              el.style.setProperty('background-color', 'transparent', 'important');
            }
          }
        });
    });

    // Verify clock is at 0
    const t0 = await page.evaluate(() => window.__getTime());
    console.log(`  Clock at t=${t0}ms (should be 0)`);

    // --- FRAME-BY-FRAME CAPTURE ---
    console.log(`  Capturing ${TOTAL_FRAMES} frames...`);
    const captureStart = Date.now();

    for (let i = 0; i < TOTAL_FRAMES; i++) {
      // Advance animation clock by exactly one frame duration
      await page.evaluate((ms) => window.__advanceTime(ms), FRAME_MS);

      // Brief real-time pause to let browser repaint after timer callbacks
      await page.waitForTimeout(5);

      const framePath = path.join(framesDir, `${String(i).padStart(5, '0')}.png`);
      await page.screenshot({
        path: framePath,
        type: 'png',
        omitBackground: true,
      });

      if ((i + 1) % FPS === 0) {
        const wallSec = ((Date.now() - captureStart) / 1000).toFixed(1);
        const animSec = ((i + 1) * FRAME_MS / 1000).toFixed(1);
        console.log(`    ${i + 1}/${TOTAL_FRAMES} | anim: ${animSec}s | wall: ${wallSec}s`);
      }
    }

    const wallSec = ((Date.now() - captureStart) / 1000).toFixed(1);
    console.log(`  Done: ${TOTAL_FRAMES} frames in ${wallSec}s`);

    await context.close();

    // --- ENCODE: Transparent ProRes 4444 ---
    const alphaOutput = path.join(OUTPUT_DIR, `${file}_alpha.mov`);
    const alphaTmp = path.join(OUTPUT_DIR, `${file}_alpha_tmp.mov`);
    console.log(`  Encoding ${file}_alpha.mov...`);
    execSync(
      `ffmpeg -y -framerate ${FPS} -i "${framesDir}/%05d.png" ` +
      `-c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le ` +
      `-alpha_bits 16 -vendor apl0 -threads 1 "${alphaTmp}"`,
      { stdio: 'inherit' }
    );

    // --- ALPHAFIX: Re-encode so Apple Silicon Resolve recognizes alpha ---
    // prores_ks initial encode from PNGs can produce container atoms that
    // macOS Sonoma 14.4+ hardware ProRes decoder ignores. A second pass
    // with explicit vendor/alpha flags fixes the container metadata.
    // On Mac, prores_videotoolbox is preferred; on Linux, prores_ks re-encode works.
    console.log(`  Alphafix: re-encoding ${file}_alpha.mov...`);
    try {
      const vtEncoder = execSync('ffmpeg -hide_banner -encoders 2>/dev/null | grep prores_videotoolbox', { encoding: 'utf8' });
      // macOS: use Apple's hardware encoder (guaranteed Resolve compatibility)
      execSync(
        `ffmpeg -y -i "${alphaTmp}" -c:v prores_videotoolbox -profile:v 4 ` +
        `-pix_fmt yuva444p10le "${alphaOutput}"`,
        { stdio: 'inherit' }
      );
    } catch {
      // Linux: re-encode with prores_ks + explicit flags
      execSync(
        `ffmpeg -y -i "${alphaTmp}" -c:v prores_ks -profile:v 4 ` +
        `-pix_fmt yuva444p10le -alpha_bits 16 -vendor apl0 "${alphaOutput}"`,
        { stdio: 'inherit' }
      );
    }
    fs.unlinkSync(alphaTmp);

    // --- ENCODE: Composited (only with --with-background) ---
    if (WITH_BACKGROUND) {
      const bgVideo = path.join(DIR, 'Wavy Grid Background.mp4');
      const compOutput = path.join(OUTPUT_DIR, `${file}.mov`);
      console.log(`  Encoding ${file}.mov...`);
      execSync(
        `ffmpeg -y ` +
        `-ss 0 -t ${DURATION_SEC} -i "${bgVideo}" ` +
        `-framerate ${FPS} -i "${framesDir}/%05d.png" ` +
        `-filter_complex "` +
          `[0:v]scale=${OUTPUT_WIDTH}:${OUTPUT_HEIGHT}:flags=lanczos[bg];` +
          `[1:v]scale=${OUTPUT_WIDTH}:${OUTPUT_HEIGHT}:flags=lanczos[fg];` +
          `[bg][fg]overlay=0:0:format=auto" ` +
        `-r ${FPS} -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 ` +
        `-t ${DURATION_SEC} "${compOutput}"`,
        { stdio: 'inherit' }
      );
    }

    // --- CLEANUP & VERIFY ---
    fs.rmSync(framesDir, { recursive: true });

    const outputs = [alphaOutput];
    if (WITH_BACKGROUND) outputs.push(path.join(OUTPUT_DIR, `${file}.mov`));

    for (const f of outputs) {
      if (fs.existsSync(f)) {
        const mb = (fs.statSync(f).size / 1024 / 1024).toFixed(0);
        const pix = execSync(
          `ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt -of csv=p=0 "${f}"`
        ).toString().trim();
        const rate = execSync(
          `ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "${f}"`
        ).toString().trim();
        console.log(`  ✓ ${path.basename(f)} — ${mb}MB, ${pix}, ${rate}`);
      } else {
        console.error(`  ✗ ${path.basename(f)} MISSING`);
      }
    }
  }

  await browser.close();
  console.log(`\nDone. Output: ${OUTPUT_DIR}`);
})();
