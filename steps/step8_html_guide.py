"""
HTML Editing Guide Generator -- Builds a self-contained interactive HTML file
that the editor uses as a visual reference for the entire video.
"""
import json
import html as html_lib


def generate_html_guide(
    script_text: str,
    assignment_map: list[dict],
    broll_candidates: list,
    image_assets: list,
    custom_visuals: list[str],
    quality_report: dict,
    output_path: str,
    images_dir: str
):
    """Generate the interactive HTML editing guide."""

    image_map = {}
    for img in image_assets:
        img_num = img.filename.replace('.png', '')
        image_map[img_num] = {
            "filename": img.filename,
            "entity": img.entity_name,
            "type": img.type,
            "description": img.description,
            "source_url": img.source_url,
            "search_query": img.search_query,
            "match_reasoning": img.match_reasoning,
            "width": img.width,
            "height": img.height,
            "relative_path": f"pictures/{img.filename}"
        }

    broll_lookup = {}
    for c in broll_candidates:
        key = f"{c.url}_{c.start_time}_{c.end_time}"
        broll_lookup[key] = {
            "video_title": c.video_title,
            "channel": c.channel,
            "description": c.description,
            "relevance_score": c.relevance_score,
            "era_appropriate": c.era_appropriate,
            "with_audio": c.with_audio,
            "source_type": c.source_type,
            "transcript_excerpt": c.transcript_excerpt,
            "match_reasoning": c.match_reasoning
        }

    metrics = quality_report.get("metrics", {})
    verdict = quality_report.get("verdict", "UNKNOWN")

    line_cards_json = json.dumps(assignment_map, ensure_ascii=False)
    image_map_json = json.dumps(image_map, ensure_ascii=False)
    broll_lookup_json = json.dumps(broll_lookup, ensure_ascii=False)
    metrics_json = json.dumps(metrics, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>rareliquid B-Roll Editing Guide</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #0f172a;
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  line-height: 1.6;
  scroll-behavior: smooth;
}}

/* Dashboard */
.dashboard {{
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 24px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}}
.dashboard-title {{
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}}
.verdict {{
  display: inline-block;
  padding: 4px 14px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.verdict-pass {{ background: #065f46; color: #6ee7b7; }}
.verdict-fail {{ background: #7f1d1d; color: #fca5a5; }}
.verdict-warn {{ background: #78350f; color: #fcd34d; }}

.stats-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}}
.stat-card {{
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px 16px;
}}
.stat-value {{
  font-size: 28px;
  font-weight: 700;
  color: #60a5fa;
}}
.stat-label {{
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

/* Progress bar */
.progress-wrap {{
  margin-bottom: 16px;
}}
.progress-label {{
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
}}
.progress-bar {{
  height: 8px;
  background: #334155;
  border-radius: 4px;
  overflow: hidden;
}}
.progress-fill {{
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}}
.progress-green {{ background: #22c55e; }}
.progress-yellow {{ background: #eab308; }}
.progress-red {{ background: #ef4444; }}

/* Controls */
.controls {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}}
.search-box {{
  flex: 1;
  min-width: 200px;
  padding: 8px 14px;
  border-radius: 6px;
  border: 1px solid #475569;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 14px;
  outline: none;
}}
.search-box:focus {{ border-color: #60a5fa; }}
.filter-btn {{
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #475569;
  background: #0f172a;
  color: #94a3b8;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}}
.filter-btn:hover {{ border-color: #60a5fa; color: #e2e8f0; }}
.filter-btn.active {{ background: #1d4ed8; border-color: #1d4ed8; color: #fff; }}
.line-count {{
  font-size: 13px;
  color: #64748b;
  margin-left: auto;
}}

/* Cards container */
.cards {{
  max-width: 1100px;
  margin: 24px auto;
  padding: 0 24px;
}}

/* Line card */
.line-card {{
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  margin-bottom: 16px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}}
.line-card:hover {{ box-shadow: 0 0 20px rgba(96, 165, 250, 0.1); }}

.line-header {{
  padding: 16px 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  cursor: pointer;
}}
.line-num {{
  background: #334155;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}}
.line-text {{
  flex: 1;
  font-size: 15px;
  color: #f1f5f9;
}}
.asset-count {{
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  flex-shrink: 0;
}}

.line-body {{
  padding: 0 20px 16px 20px;
}}

/* Asset panel */
.asset-panel {{
  border-left: 4px solid #475569;
  margin: 10px 0;
  padding: 14px 18px;
  background: #0f172a;
  border-radius: 0 8px 8px 0;
}}
.asset-panel.type-broll {{ border-left-color: #3498db; }}
.asset-panel.type-audio {{ border-left-color: #9b59b6; }}
.asset-panel.type-image {{ border-left-color: #27ae60; }}
.asset-panel.type-custom {{ border-left-color: #e67e22; }}
.asset-panel.type-gap {{ border-left-color: #e74c3c; }}

.asset-badge {{
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}}
.badge-broll {{ background: #1e3a5f; color: #60a5fa; }}
.badge-audio {{ background: #3b1f5e; color: #c084fc; }}
.badge-image {{ background: #14532d; color: #6ee7b7; }}
.badge-custom {{ background: #431407; color: #fdba74; }}
.badge-gap {{ background: #450a0a; color: #fca5a5; }}

.asset-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  align-items: center;
}}
.meta-tag {{
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #1e293b;
  color: #94a3b8;
  border: 1px solid #334155;
}}
.meta-tag.era-ok {{ border-color: #065f46; color: #6ee7b7; }}
.meta-tag.era-bad {{ border-color: #7f1d1d; color: #fca5a5; }}

.relevance-bar {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}}
.relevance-track {{
  width: 60px;
  height: 6px;
  background: #334155;
  border-radius: 3px;
  overflow: hidden;
}}
.relevance-fill {{
  height: 100%;
  border-radius: 3px;
}}

.video-link {{
  display: inline-block;
  margin-bottom: 10px;
}}
.video-link a {{
  color: #60a5fa;
  text-decoration: none;
  font-size: 14px;
  word-break: break-all;
}}
.video-link a:hover {{ text-decoration: underline; }}
.video-info {{
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 6px;
}}

.section-label {{
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 12px 0 6px 0;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}}
.section-label .arrow {{
  transition: transform 0.2s;
  font-size: 10px;
}}
.section-label .arrow.collapsed {{ transform: rotate(-90deg); }}

.transcript-box {{
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 10px 14px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}}
.reasoning-box {{
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.6;
  padding: 4px 0;
}}

.image-preview {{
  margin: 10px 0;
}}
.image-preview img {{
  max-width: 400px;
  max-height: 250px;
  border-radius: 6px;
  border: 1px solid #334155;
}}
.image-info {{
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}}

/* Scroll to top */
.scroll-top {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #1d4ed8;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 20px;
  display: none;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  z-index: 200;
}}
.scroll-top:hover {{ background: #2563eb; }}

/* Copy toast */
.toast {{
  position: fixed;
  bottom: 80px;
  right: 24px;
  background: #065f46;
  color: #6ee7b7;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 200;
  pointer-events: none;
}}
.toast.show {{ opacity: 1; }}

/* Hidden */
.hidden {{ display: none !important; }}
</style>
</head>
<body>

<div class="dashboard" id="dashboard">
  <div class="dashboard-title">
    rareliquid B-Roll Editing Guide
    <span class="verdict" id="verdict-badge"></span>
  </div>
  <div class="progress-wrap" id="progress-wrap"></div>
  <div class="stats-grid" id="stats-grid"></div>
  <div class="controls">
    <input type="text" class="search-box" id="search-box" placeholder="Search script lines...">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="broll">B-Roll</button>
    <button class="filter-btn" data-filter="image">Images</button>
    <button class="filter-btn" data-filter="audio">Audio</button>
    <button class="filter-btn" data-filter="custom">Custom</button>
    <button class="filter-btn" data-filter="gap">Gaps</button>
    <span class="line-count" id="line-count"></span>
  </div>
</div>

<div class="cards" id="cards"></div>

<button class="scroll-top" id="scroll-top">&#8593;</button>
<div class="toast" id="toast">URL copied!</div>

<script>
const LINE_CARDS = {line_cards_json};
const IMAGE_MAP = {image_map_json};
const BROLL_LOOKUP = {broll_lookup_json};
const METRICS = {metrics_json};
const VERDICT = "{verdict}";

function init() {{
  renderDashboard();
  renderCards();
  bindEvents();
}}

function renderDashboard() {{
  // Verdict badge
  const badge = document.getElementById('verdict-badge');
  badge.textContent = VERDICT.replace(/_/g, ' ');
  if (VERDICT === 'PASS') {{
    badge.className = 'verdict verdict-pass';
  }} else if (VERDICT === 'FAIL') {{
    badge.className = 'verdict verdict-fail';
  }} else {{
    badge.className = 'verdict verdict-warn';
  }}

  // Coverage progress
  const cov = METRICS.coverage_percentage || 0;
  const pw = document.getElementById('progress-wrap');
  let pClass = cov >= 90 ? 'progress-green' : cov >= 70 ? 'progress-yellow' : 'progress-red';
  pw.innerHTML = `
    <div class="progress-label">
      <span>Script Coverage</span><span>${{cov}}%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill ${{pClass}}" style="width:${{Math.min(cov, 100)}}%"></div>
    </div>
  `;

  // Stats
  const sg = document.getElementById('stats-grid');
  const stats = [
    ['unique_broll_sources', 'Unique B-Roll'],
    ['total_broll_placements', 'B-Roll Placed'],
    ['unique_still_images', 'Unique Images'],
    ['total_image_placements', 'Images Placed'],
    ['broll_with_audio', 'With Audio'],
    ['custom_visuals_generated', 'Custom Visuals'],
    ['lines_with_no_visual', 'Gaps'],
    ['avg_relevance_score', 'Avg Relevance'],
    ['estimated_script_duration_min', 'Est. Duration (min)'],
    ['era_mismatches', 'Era Mismatches'],
  ];
  sg.innerHTML = stats.map(([k, label]) => `
    <div class="stat-card">
      <div class="stat-value">${{METRICS[k] !== undefined ? METRICS[k] : '-'}}</div>
      <div class="stat-label">${{label}}</div>
    </div>
  `).join('');
}}

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}}

function tsToSeconds(ts) {{
  if (!ts) return 0;
  const p = ts.split(':');
  return p.length === 2 ? parseInt(p[0]) * 60 + parseInt(p[1]) : 0;
}}

function relevanceColor(score) {{
  if (score >= 8) return '#22c55e';
  if (score >= 6) return '#eab308';
  return '#ef4444';
}}

function renderAssetPanel(asset) {{
  let typeClass = 'type-broll';
  let badgeClass = 'badge-broll';
  let badgeText = 'B-ROLL';

  if (asset.type === 'broll_with_audio') {{
    typeClass = 'type-audio';
    badgeClass = 'badge-audio';
    badgeText = 'B-ROLL + AUDIO';
  }} else if (asset.type === 'image') {{
    typeClass = 'type-image';
    badgeClass = 'badge-image';
    badgeText = 'STILL IMAGE';
  }} else if (asset.type === 'custom_visual') {{
    typeClass = 'type-custom';
    badgeClass = 'badge-custom';
    badgeText = 'CUSTOM VISUAL';
  }} else if (asset.type === 'gap') {{
    typeClass = 'type-gap';
    badgeClass = 'badge-gap';
    badgeText = 'NO ASSET FOUND';
  }}

  let content = `<span class="asset-badge ${{badgeClass}}">${{badgeText}}</span>`;

  if (asset.type === 'broll' || asset.type === 'broll_with_audio') {{
    const startSec = tsToSeconds(asset.start_time);
    const ytUrl = asset.url ? asset.url + '&t=' + startSec : '#';

    content += `
      <div class="video-info">${{esc(asset.video_title || '')}} &mdash; ${{esc(asset.channel || '')}}</div>
      <div class="video-link">
        <a href="${{esc(ytUrl)}}" target="_blank" onclick="event.stopPropagation()">${{esc(asset.url || '')}}</a>
        <button style="margin-left:8px;padding:2px 8px;font-size:11px;cursor:pointer;background:#1e293b;color:#94a3b8;border:1px solid #475569;border-radius:4px;" onclick="event.stopPropagation();copyUrl('${{esc(ytUrl)}}')">Copy</button>
      </div>
      <div class="asset-meta">
        <span class="meta-tag">${{esc(asset.start_time)}} - ${{esc(asset.end_time)}}</span>
        <span class="meta-tag">${{esc(asset.source_type || 'unknown')}}</span>
        <span class="meta-tag ${{asset.era_appropriate !== false ? 'era-ok' : 'era-bad'}}">
          ${{asset.era_appropriate !== false ? 'Era OK' : 'ERA MISMATCH'}}
        </span>
        <span class="relevance-bar">
          Relevance:
          <span class="relevance-track">
            <span class="relevance-fill" style="width:${{(asset.relevance_score || 0) * 10}}%;background:${{relevanceColor(asset.relevance_score || 0)}}"></span>
          </span>
          ${{asset.relevance_score || 0}}/10
        </span>
      </div>
    `;

    if (asset.transcript_excerpt) {{
      const uid = 'tr_' + Math.random().toString(36).substr(2, 9);
      content += `
        <div class="section-label" onclick="toggleSection('${{uid}}')">
          <span class="arrow" id="arrow_${{uid}}">&#9660;</span> What's being said
        </div>
        <div class="transcript-box" id="${{uid}}">${{esc(asset.transcript_excerpt)}}</div>
      `;
    }}

    if (asset.match_reasoning) {{
      const uid2 = 'mr_' + Math.random().toString(36).substr(2, 9);
      content += `
        <div class="section-label" onclick="toggleSection('${{uid2}}')">
          <span class="arrow" id="arrow_${{uid2}}">&#9660;</span> Why this fits
        </div>
        <div class="reasoning-box" id="${{uid2}}">${{esc(asset.match_reasoning)}}</div>
      `;
    }}
  }} else if (asset.type === 'image') {{
    const picNum = asset.pic_number;
    const imgData = picNum !== null && picNum !== undefined ? IMAGE_MAP[String(picNum)] : null;

    if (imgData) {{
      content += `
        <div class="image-preview">
          <img src="${{esc(imgData.relative_path)}}" alt="pic ${{picNum}}" onerror="this.style.display='none'">
          <div class="image-info">pic ${{picNum}} &bull; ${{esc(imgData.type)}} &bull; ${{imgData.width}}x${{imgData.height}} &bull; ${{esc(imgData.entity)}}</div>
        </div>
      `;
      if (imgData.source_url) {{
        content += `<div class="video-link"><a href="${{esc(imgData.source_url)}}" target="_blank" onclick="event.stopPropagation()">Source</a></div>`;
      }}
      if (imgData.match_reasoning) {{
        const uid3 = 'ir_' + Math.random().toString(36).substr(2, 9);
        content += `
          <div class="section-label" onclick="toggleSection('${{uid3}}')">
            <span class="arrow" id="arrow_${{uid3}}">&#9660;</span> Why this fits
          </div>
          <div class="reasoning-box" id="${{uid3}}">${{esc(imgData.match_reasoning)}}</div>
        `;
      }}
    }} else {{
      content += `<div class="video-info">pic ${{picNum || '?'}}</div>`;
      if (asset.match_reasoning) {{
        content += `<div class="reasoning-box">${{esc(asset.match_reasoning)}}</div>`;
      }}
    }}
  }} else if (asset.type === 'custom_visual') {{
    content += `<div class="reasoning-box">${{esc(asset.description || 'Custom visual needed')}}</div>`;
  }} else {{
    content += `<div class="reasoning-box">No matching asset was found for this line. Manual research needed.</div>`;
  }}

  return `<div class="asset-panel ${{typeClass}}">${{content}}</div>`;
}}

function renderCards() {{
  const container = document.getElementById('cards');
  if (!LINE_CARDS || LINE_CARDS.length === 0) {{
    container.innerHTML = '<p style="text-align:center;color:#64748b;padding:40px;">No assignment data available. The annotation step may not have produced a structured map.</p>';
    return;
  }}

  container.innerHTML = LINE_CARDS.map((card, idx) => {{
    const assets = card.assets || [];
    const assetCount = assets.length;
    const hasGap = card.has_gap || assets.length === 0;

    let types = assets.map(a => a.type || 'gap');
    if (hasGap && types.length === 0) types = ['gap'];

    const panels = assets.length > 0
      ? assets.map(a => renderAssetPanel(a)).join('')
      : renderAssetPanel({{type: 'gap'}});

    return `
      <div class="line-card" data-types="${{types.join(',')}}" data-text="${{esc(card.line_text || '').toLowerCase()}}">
        <div class="line-header" onclick="toggleBody(this)">
          <span class="line-num">L${{card.line_number || idx + 1}}</span>
          <span class="line-text">${{esc(card.line_text || '')}}</span>
          <span class="asset-count">${{assetCount}} asset${{assetCount !== 1 ? 's' : ''}}</span>
        </div>
        <div class="line-body">
          ${{panels}}
        </div>
      </div>
    `;
  }}).join('');

  updateCount();
}}

function toggleBody(header) {{
  const body = header.nextElementSibling;
  body.classList.toggle('hidden');
}}

function toggleSection(id) {{
  const el = document.getElementById(id);
  const arrow = document.getElementById('arrow_' + id);
  if (el) el.classList.toggle('hidden');
  if (arrow) arrow.classList.toggle('collapsed');
}}

function copyUrl(url) {{
  navigator.clipboard.writeText(url).then(() => {{
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 1500);
  }});
}}

function updateCount() {{
  const cards = document.querySelectorAll('.line-card');
  let visible = 0;
  cards.forEach(c => {{ if (!c.classList.contains('hidden')) visible++; }});
  document.getElementById('line-count').textContent = visible + ' / ' + cards.length + ' lines';
}}

function filterCards(type) {{
  const cards = document.querySelectorAll('.line-card');
  cards.forEach(card => {{
    if (type === 'all') {{
      card.classList.remove('hidden');
    }} else {{
      const types = card.getAttribute('data-types') || '';
      const match = type === 'gap'
        ? types.includes('gap')
        : type === 'audio'
          ? types.includes('broll_with_audio')
          : type === 'broll'
            ? (types.includes('broll') && !types.includes('broll_with_audio'))
            : types.includes(type);
      card.classList.toggle('hidden', !match);
    }}
  }});
  updateCount();
}}

function searchCards(query) {{
  const cards = document.querySelectorAll('.line-card');
  const q = query.toLowerCase();
  cards.forEach(card => {{
    const text = card.getAttribute('data-text') || '';
    card.classList.toggle('hidden', q && !text.includes(q));
  }});
  updateCount();
}}

function bindEvents() {{
  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('search-box').value = '';
      filterCards(btn.getAttribute('data-filter'));
    }});
  }});

  // Search
  document.getElementById('search-box').addEventListener('input', (e) => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-filter="all"]').classList.add('active');
    searchCards(e.target.value);
  }});

  // Scroll to top
  const stb = document.getElementById('scroll-top');
  window.addEventListener('scroll', () => {{
    stb.style.display = window.scrollY > 400 ? 'flex' : 'none';
  }});
  stb.addEventListener('click', () => {{
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }});
}}

document.addEventListener('DOMContentLoaded', init);
</script>

</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
