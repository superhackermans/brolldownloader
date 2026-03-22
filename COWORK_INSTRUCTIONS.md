# COWORK EXECUTION GUIDE: B-Roll Bot

## Overview

You are running the rareliquid B-Roll Bot in cowork mode. YOU are the LLM runtime -- no subprocess calls needed. You do entity extraction, transcript analysis, and annotation directly. Python scripts handle only API calls (YouTube search, image download).

The input script is at: `broll_bot/input_script.txt`
Output goes to: `broll_bot/output/`

## STEP-BY-STEP EXECUTION (follow in exact order)

---

### STEP 0: Setup output directories

```bash
mkdir -p broll_bot/output/pictures broll_bot/output/videos broll_bot/output/custom_visuals
```

---

### STEP 1: Entity Extraction

Read `broll_bot/input_script.txt`. For EVERY entity that needs a visual, produce a JSON array.

Extract every: person, company, event, product, location, concept, quote, metaphor.

For each entity output:
```json
{
  "name": "Frank Quattrone",
  "type": "person",
  "era": "1977-2008",
  "script_lines": [6, 7, 8, ...],
  "youtube_queries": ["Frank Quattrone interview", "Frank Quattrone CNBC", "Frank Quattrone documentary", "Frank Quattrone Silicon Valley"],
  "image_queries": ["Frank Quattrone photo", "Frank Quattrone banker"],
  "notes": ""
}
```

Rules:
- Every person by name gets their own entity
- Every company gets its own entity
- Every metaphor/analogy gets a "metaphor" entity
- If a person spans multiple eras, create SEPARATE entities per era
- youtube_queries: 3-5 specific queries per entity
- image_queries: 2-3 queries per entity

Save the result to: `broll_bot/output/entities.json`

---

### STEP 2: YouTube Search (API)

Take the entities JSON and build a search queries file, then run:

```bash
cd /workspace/broll_bot && python3 api_tools.py batch_youtube_search output/youtube_queries.json output/youtube_results.json
```

The queries file should be:
```json
[
  {"entity": "Frank Quattrone", "query": "Frank Quattrone interview"},
  {"entity": "Frank Quattrone", "query": "Frank Quattrone CNBC"},
  ...
]
```

First write `output/youtube_queries.json` from the entities, then run the command.

---

### STEP 3: Fetch Transcripts (API)

```bash
cd /workspace/broll_bot && python3 api_tools.py batch_transcripts output/youtube_results.json output/videos_with_transcripts.json
```

This fetches transcripts for all found videos.

---

### STEP 4: Transcript Analysis (YOU do this)

Read `output/videos_with_transcripts.json`. For each video that has a transcript, identify relevant B-roll moments.

For EVERY relevant moment, record:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_title": "exact title",
  "channel": "channel name",
  "start_time": "MM:SS",
  "end_time": "MM:SS",
  "entity_name": "which entity this serves",
  "description": "what is visually happening (1 sentence)",
  "relevance_score": 8,
  "era_appropriate": true,
  "with_audio": false,
  "source_type": "interview",
  "transcript_excerpt": "exact words spoken at this timestamp",
  "match_reasoning": "WHY this clip fits the script line -- be specific"
}
```

Rules:
- Clips must be 3-10 seconds
- Only include relevance_score >= 5
- transcript_excerpt is MANDATORY
- match_reasoning is MANDATORY and must be SPECIFIC (not "relevant to topic")
- with_audio = true only for genuinely powerful statements (very rare)

Save to: `broll_bot/output/broll_candidates.json`

---

### STEP 5: Image Search (API)

Build image queries from entities, then run:

```bash
cd /workspace/broll_bot && python3 api_tools.py batch_image_search output/image_queries.json output/pictures/ output/image_assets.json
```

The queries file:
```json
[
  {"entity": "Frank Quattrone", "query": "Frank Quattrone photo"},
  {"entity": "Qatalyst Partners", "query": "Qatalyst Partners logo"},
  ...
]
```

Write `output/image_queries.json` first, then run the command.

---

### STEP 6: Script Annotation (YOU do this)

Read:
- `broll_bot/input_script.txt` (the script)
- `broll_bot/output/broll_candidates.json` (available B-roll clips)
- `broll_bot/output/image_assets.json` (available images)

For EVERY script line, assign the best matching asset. Output TWO files:

**File 1: `output/annotated_script.md`**

Every line with inline annotations:
```
Would you believe me if I said that the LARGEST and most FAMOUS tech M&A deals...
[https://www.youtube.com/watch?v=abc123, 2:15 - 2:22]

NXP to Qualcomm - $47 billion. Ansys to Synopsys - $32 billion...
[pic 3] [pic 7]
```

Rules:
- Every line gets at least one visual. If none: `[NO B-ROLL FOUND - need alternative]`
- B-roll: `[https://www.youtube.com/watch?v=VIDEO_ID, MM:SS - MM:SS]`
- B-roll with audio: `[https://www.youtube.com/watch?v=VIDEO_ID, MM:SS - MM:SS, WITH AUDIO]`
- Images: `[pic N]` or `[pic N, highlight "key phrase"]`
- Custom visual: `[CUSTOM VISUAL NEEDED: description]`
- Never 3+ consecutive stills without a video clip
- Never reuse same B-roll clip for different lines
- Preference: interview > news > documentary > conference > other

End with an Asset Summary section.

**File 2: `output/assignment_map.json`**

JSON array, one entry per script line:
```json
[
  {
    "line_number": 1,
    "line_text": "original line",
    "assets": [
      {
        "type": "broll",
        "url": "https://www.youtube.com/watch?v=...",
        "start_time": "2:15",
        "end_time": "2:22",
        "pic_number": null,
        "video_title": "...",
        "channel": "...",
        "description": "what this shows",
        "transcript_excerpt": "exact words at this timestamp",
        "match_reasoning": "WHY this fits -- specific",
        "relevance_score": 8,
        "era_appropriate": true,
        "source_type": "interview",
        "image_source_url": null,
        "image_type": null
      }
    ],
    "has_gap": false,
    "custom_visual_description": null
  }
]
```

---

### STEP 7: B-Roll Manifest (Videos Cache)

Create `output/videos/broll_manifest.json` from the broll_candidates and assignment data:
```json
{
  "description": "B-roll video cache manifest for editor",
  "total_clips": 45,
  "unique_sources": 30,
  "clips": [
    {
      "url": "...",
      "url_at_timestamp": "...&t=135",
      "video_title": "...",
      "channel": "...",
      "start_time": "2:15",
      "end_time": "2:22",
      "duration_seconds": 7,
      "entity": "...",
      "description": "...",
      "relevance_score": 8,
      "era_appropriate": true,
      "with_audio": false,
      "source_type": "interview",
      "transcript_excerpt": "...",
      "match_reasoning": "..."
    }
  ]
}
```

Sort clips by relevance_score descending.

---

### STEP 8: Custom Visuals (YOU do this)

Find any `[CUSTOM VISUAL NEEDED: ...]` flags in the annotated script. For each (max 3), generate a self-contained HTML file.

Style: dark background (#1B2A4A), sans-serif font, 16:9 aspect ratio, accent colors (#C0392B red, #27AE60 green, #3498DB blue).

Save to: `output/custom_visuals/custom_visual_1.html` etc.

---

### STEP 9: Quality Report

Count everything and write `output/quality_report.json`:
```json
{
  "metrics": {
    "unique_broll_sources": 0,
    "unique_still_images": 0,
    "total_broll_placements": 0,
    "total_image_placements": 0,
    "broll_with_audio": 0,
    "custom_visuals_generated": 0,
    "lines_with_no_visual": 0,
    "coverage_percentage": 0,
    "avg_relevance_score": 0,
    "era_mismatches": 0
  },
  "verdict": "PASS"
}
```

---

### STEP 10: HTML Editing Guide (YOU do this)

Generate a self-contained interactive HTML file at `output/editing_guide.html`.

Read `output/assignment_map.json`, `output/image_assets.json`, `output/broll_candidates.json`, `output/quality_report.json`.

The HTML must include:

**Dashboard header (sticky):**
- Quality verdict badge (PASS=green, FAIL=red)
- Coverage progress bar
- Stat cards: total B-roll, unique sources, images, audio clips, gaps, avg relevance

**Controls:**
- Search box (filters lines by text)
- Filter buttons: All, B-Roll, Images, Audio, Custom, Gaps
- Line count display

**Script line cards (one per line):**
Each card has:
- Line number badge + script text
- Asset panels with colored left border:
  - Blue = B-roll, Purple = audio, Green = image, Orange = custom, Red = gap
- For B-roll: clickable YouTube link at timestamp, video title, channel, start-end times, relevance bar, era badge, source type badge, "What's being said" transcript excerpt, "Why this fits" reasoning
- For images: inline `<img>` preview (src="pictures/N.png"), filename, type, source link, "Why this fits" reasoning
- For gaps: red "NO ASSET FOUND" badge

**Styling:** Dark theme (#0f172a bg, #1e293b cards), hover effects, responsive, monospace for timestamps/transcripts. ALL CSS inline in `<style>`. ALL JS inline. NO external dependencies.

---

## IMPORTANT RULES

1. Run steps in EXACT order. Do not skip steps.
2. Always write output files before proceeding to the next step.
3. For transcript analysis (Step 4), process ALL videos -- do not skip any.
4. For annotation (Step 6), EVERY script line must get at least one asset.
5. match_reasoning must be SPECIFIC. Not "relevant to Quattrone." Instead: "At 3:15 Quattrone describes being rejected by Goldman in his own words, matching the script line about his 1984 application."
6. transcript_excerpt must be the ACTUAL words from the video transcript. Never fabricate.
7. Never assign era_appropriate=false clips unless nothing else exists.
8. Alternate B-roll and stills -- never 3+ consecutive stills.
9. Never reuse the same clip for different lines.
10. If a step fails or produces insufficient results, note it and continue with what you have.
