# BUILD INSTRUCTIONS: rareliquid Automated B-Roll Research Bot

## Who You Are

You are an expert software engineer building an automated B-roll research pipeline for a YouTube channel called rareliquid. You will build this system, run it against a real test script, evaluate the output quality, and iterate until it meets all quality parameters. You do not stop until the quality gate passes.

---

## What You Are Building

A Python CLI tool that takes a documentary script as input and produces:

1. **An annotated script** — every line paired with `[YouTube URL, start - end]` or `[pic N]` references
2. **A pictures folder** — downloaded still images named `1.png, 2.png, 3.png...`
3. **A videos folder** — a cache/manifest of all B-roll clips (URLs, timestamps, metadata) so an editor can pull and cut from it
4. **Custom visual HTML files** — for data/timeline lines (1-3 per script)
5. **An interactive HTML editing guide** — a self-contained HTML file that shows every script line with its assigned assets, embedded YouTube previews at the right timestamps, inline pictures, and a written explanation of WHY each asset was chosen (what part of the transcript matched, why the image is relevant, era justification, etc.)
6. **A quality report** — counts, coverage %, and flagged gaps

The bot replaces a human research assistant who currently spends 5-7 hours per 15-minute script. The bot should complete the same work in under 15 minutes.

**IMPORTANT: This bot runs inside Claude Code (Max mode).** There is NO Anthropic API key. All LLM calls are made by invoking `claude` CLI subprocesses (which run for free under Max). The only paid API keys needed are:

1. **YouTube Data API v3** — for searching videos and getting metadata
2. **Google Custom Search API + Search Engine ID** — for finding images

---

## Context: What rareliquid Videos Look Like

Key facts:
- Documentary-style finance videos about Wall Street personalities and institutions
- For a 15-minute video, the editor needs: **75-90 unique B-roll clips**, **55-70 unique still images**, **1-3 custom visual HTML files**
- The host is on screen only ~13% of the time. The rest is B-roll, images, and graphics.
- Every script line must have at least one visual asset assigned to it
- B-roll clips must be 3-10 seconds, from YouTube (interviews, news coverage, documentaries)
- Still images are article screenshots, photos, documents — minimum 1280x720
- Annotation format: `[https://www.youtube.com/watch?v=VIDEO_ID, MM:SS - MM:SS]` for B-roll, `[pic N]` for images
- Historical accuracy matters — no 2024 footage for 1986 events

### The Four Asset Types

#### Type 03: B-Roll Video
Video footage that plays between host-on-camera segments while voiceover narrates. Makes up ~60% of screen time.

- **Duration:** 3-10 seconds per clip (ideal: 4-7 seconds); no isolated clips under 3 seconds
- **Quality:** Must match the era discussed. Passes mute test (topic guessable without sound). Never reuse same clip for different script lines. Stock footage capped at under 10%.
- **Annotation:** `[https://www.youtube.com/watch?v=QZ85VPgCOCM, 0:18 - 0:29]` — full YouTube URL + exact timestamps. No vague references.

#### Type 04: Still Images
Static images displayed 2-6 seconds; ~25% of screen time.

- **Preference order:** (1) News article screenshots with highlighted key phrases, (2) Official documents (SEC filings, court docs, press releases), (3) Data charts/graphs from reputable sources, (4) High-resolution photographs, (5) Social media screenshots (notable accounts only)
- **Technical:** Minimum 1280x720 resolution. No watermarks or compression artifacts. Crop to relevant content only.
- **Naming:** Sequential numbering: `1.png, 2.png, 3.png`
- **Annotation:** `[pic 1]` `[pic 7]` `[pic 12]`

#### Type 05: B-Roll with Audio
Same as B-roll but original audio plays instead of voiceover. Extremely rare: ~2% of total, only 3-5 uses per 15-minute video.

- **When justified:** CEO/public figure statement more powerful in their voice. News anchor breaking major story. Interview quote deserving direct hearing. Genuine emotion lost in paraphrasing.
- **Annotation:** `[https://www.youtube.com/watch?v=xyz, 4:05 - 4:09, WITH AUDIO]`

#### Type 06: Custom Visuals/HTML
Custom-built HTML graphics rendered on screen. Limited to 1-3 per entire video.

- **Uses:** Career timelines, financial data visualizations, comparison tables, organizational changes, key statistics
- **Technical:** 16:9 aspect ratio, all text legible at 1080p, self-contained HTML (no external dependencies), data sourced and cited
- **Annotation:** `[15.html]`

---

## Architecture

```
+-------------------------------------------------------------+
|                        CLI ENTRY POINT                       |
|  python broll_bot.py --script input.txt --output ./output/   |
+-----------------------------+-------------------------------+
                              |
               +--------------+-----------------+
               v              v                 v
       +---------------+ +---------------+ +---------------+
       |  Step 1        | |               | |               |
       |  Entity        | |  (parallel)   | |  (parallel)   |
       |  Extraction    | |               | |               |
       +-------+-------+ +---------------+ +---------------+
               |
               v
       +---------------+
       |  Step 2        |
       |  YouTube       |---> Search API -> Get video IDs
       |  Search        |---> Transcript API -> Get transcripts
       +-------+-------+
               |
               v
       +---------------+
       |  Step 3        |
       |  Transcript    |---> Claude Code: find timestamps per entity
       |  Analysis      |---> Returns: [{url, start, end, relevance, era_ok}]
       +-------+-------+
               |
               v
       +---------------+
       |  Step 4        |
       |  Image         |---> Google Custom Search API -> find images
       |  Search        |---> Download + validate resolution
       +-------+-------+     ---> Playwright -> screenshot articles
               |
               v
       +---------------+
       |  Step 5        |
       |  Script        |---> Claude Code: assign assets to lines
       |  Annotation    |---> Produce annotated script
       +-------+-------+
               |
               v
       +---------------+
       |  Step 6        |
       |  Custom        |---> Claude Code: generate HTML for flagged lines
       |  Visuals       |
       +-------+-------+
               |
               v
       +---------------+
       |  Step 7        |
       |  Quality       |---> Run quality checks
       |  Evaluation    |---> If FAIL -> re-run weak steps
       +-------+-------+     ---> If PASS -> output final deliverables
               |
               v
       +---------------+
       |  Step 8        |
       |  HTML Guide    |---> Generate interactive editing guide
       |  Generation    |---> Self-contained HTML with all reasoning
       +-------+-------+
               |
               v
       +---------------+
       |  Output        |
       |  Deliverables  |---> annotated_script.md
       +---------------+---> pictures/ folder (1.png, 2.png...)
                         ---> videos/ folder (broll_manifest.json)
                         ---> custom_visuals/ folder (*.html)
                         ---> editing_guide.html
                         ---> quality_report.json
```

---

## File Structure

Create this exact project structure:

```
broll_bot/
|-- broll_bot.py              # CLI entry point
|-- config.py                 # API keys, model settings, thresholds
|-- requirements.txt          # Dependencies
|-- input_script.txt          # <-- USER PASTES THEIR SCRIPT HERE
|-- steps/
|   |-- __init__.py
|   |-- step1_entity_extraction.py
|   |-- step2_youtube_search.py
|   |-- step3_transcript_analysis.py
|   |-- step4_image_search.py
|   |-- step5_annotation.py
|   |-- step6_custom_visuals.py
|   |-- step7_quality_eval.py
|   |-- step8_html_guide.py
|-- utils/
|   |-- __init__.py
|   |-- claude_client.py      # Wrapper for Claude Code calls
|   |-- youtube_client.py     # YouTube Data API + transcript fetch
|   |-- image_client.py       # Google CSE + Playwright screenshots
|   |-- formatters.py         # Output formatting helpers
|-- output/                   # Generated output goes here
|   |-- annotated_script.md
|   |-- pictures/
|   |-- videos/
|   |   |-- broll_manifest.json
|   |-- custom_visuals/
|   |-- editing_guide.html
|   |-- quality_report.json
```

---

## Dependencies (requirements.txt)

```
google-api-python-client>=2.100.0
youtube-transcript-api>=0.6.0
playwright>=1.40.0
Pillow>=10.0.0
aiohttp>=3.9.0
requests>=2.31.0
python-dotenv>=1.0.0
```

After installing, also run: `playwright install chromium`

**Prerequisites:** Claude Code must be installed and authenticated (`claude` command on PATH, Max mode active). No Anthropic API key needed.

---

## Configuration (config.py)

```python
import os
from dotenv import load_dotenv
load_dotenv()

# API Keys -- NO Anthropic key needed (using Claude Code Max mode)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Claude Code settings -- all LLM calls go through `claude` CLI subprocess
# This runs for free under Claude Code Max mode
CLAUDE_CODE_PATH = "claude"  # assumes `claude` is on PATH
CLAUDE_MAX_TOKENS = 16384

# YouTube settings
YOUTUBE_RESULTS_PER_QUERY = 5
MAX_TRANSCRIPT_LENGTH = 50000  # chars -- truncate longer transcripts

# Image settings
MIN_IMAGE_WIDTH = 1280
MIN_IMAGE_HEIGHT = 720
MAX_IMAGES_PER_QUERY = 5

# Quality thresholds -- THE BOT ITERATES UNTIL THESE ARE MET
QUALITY_THRESHOLDS = {
    "min_broll_unique_sources": 60,       # Minimum unique B-roll video sources
    "target_broll_unique_sources": 80,    # Target (triggers extra search if below)
    "min_still_images": 45,               # Minimum unique still images
    "target_still_images": 60,            # Target
    "min_custom_visuals": 1,              # At least 1 custom visual
    "max_custom_visuals": 3,              # No more than 3
    "max_gap_percentage": 5.0,            # Max % of lines with no visual (target: 0%)
    "max_stock_footage_percentage": 10.0, # Max % of B-roll that is stock footage
    "min_coverage_percentage": 90.0,      # Min % of script lines with at least one visual
    "target_coverage_percentage": 98.0,   # Target coverage
    "min_avg_relevance_score": 6.0,       # Min average relevance score across all B-roll
    "max_era_mismatch_count": 0,          # No era mismatches allowed
    "min_broll_per_minute": 4.0,          # Minimum B-roll clips per minute of script
    "min_images_per_minute": 3.0,         # Minimum images per minute of script
}

# Iteration settings
MAX_ITERATIONS = 3  # Max times to re-run weak steps
ITERATION_STRATEGY = "targeted"  # "targeted" = only re-run failing steps; "full" = re-run everything
```

---

## Step-by-Step Implementation

### Step 1: Entity Extraction (`steps/step1_entity_extraction.py`)

**Input:** Raw script text (string)
**Output:** List of Entity objects

```python
"""
Entity Extraction -- Parse the script and identify every person, company,
event, quote, data point, and metaphor that needs a visual.
"""
from dataclasses import dataclass, field
from utils.claude_client import call_claude
import json

@dataclass
class Entity:
    name: str
    type: str  # person | company | event | product | location | concept | quote | metaphor
    era: str  # e.g., "1986", "2018-present", "unknown"
    script_lines: list[int] = field(default_factory=list)
    youtube_queries: list[str] = field(default_factory=list)
    image_queries: list[str] = field(default_factory=list)
    notes: str = ""

EXTRACTION_PROMPT = """You are parsing a documentary script for a finance YouTube channel called rareliquid.

Extract EVERY entity that needs a visual asset. Be exhaustive -- missing an entity means a gap in the final video.

For each entity return a JSON object with:
- "name": full name or title
- "type": one of: person, company, event, product, location, concept, quote, metaphor
- "era": the time period being discussed (e.g., "1986", "2018-present"). If unclear, use "unknown"
- "script_lines": array of line numbers (1-indexed) that reference this entity
- "youtube_queries": 3-5 YouTube search queries to find B-roll video. Be specific:
    - For people: "[name] interview", "[name] Bloomberg", "[name] CNBC", "[name] documentary"
    - For companies: "[company] news", "[company] history", "[company] documentary"
    - For events: "[event] news coverage", "[event] documentary"
    - For metaphors: search for the literal visual (e.g., "basketball block" for "rejection")
- "image_queries": 2-3 Google Image queries:
    - For people: "[name] [year]", "[name] young" (if discussing early career)
    - For quotes: "site:wsj.com [topic]", "site:nytimes.com [topic]"
    - For events: "[event] news article screenshot"
- "notes": any special instructions (e.g., "defunct company -- need 1980s archival footage", "metaphor -- find creative visual", "need the original article to screenshot")

IMPORTANT:
- Every person mentioned by name gets their own entity
- Every company gets its own entity
- Every specific quote or attributed statement gets a "quote" entity with notes about finding the source article
- Every metaphor or analogy (e.g., "cage match", "caught the bus by the tailpipe") gets a "metaphor" entity
- Every data point (revenue figure, percentage, stock price) gets a "concept" entity
- If a person is discussed in multiple eras (e.g., "young Solomon" vs "CEO Solomon"), create SEPARATE entities for each era

Return a JSON array of objects. Nothing else -- no markdown, no explanation, just the JSON array.

SCRIPT:
{script}"""

def extract_entities(script_text: str) -> list[Entity]:
    """Extract all entities from the script."""
    # Number the lines
    lines = script_text.strip().split('\n')
    numbered_script = '\n'.join(f"[{i+1}] {line}" for i, line in enumerate(lines))

    response = call_claude(
        EXTRACTION_PROMPT.format(script=numbered_script),
        model="sonnet",
        max_tokens=8192
    )

    # Parse JSON response
    try:
        entities_raw = json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response if wrapped in markdown
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            entities_raw = json.loads(match.group())
        else:
            raise ValueError(f"Failed to parse entity extraction response: {response[:500]}")

    entities = []
    for e in entities_raw:
        entities.append(Entity(
            name=e['name'],
            type=e['type'],
            era=e.get('era', 'unknown'),
            script_lines=e.get('script_lines', []),
            youtube_queries=e.get('youtube_queries', []),
            image_queries=e.get('image_queries', []),
            notes=e.get('notes', '')
        ))

    return entities
```

---

### Step 2: YouTube Search (`steps/step2_youtube_search.py`)

**Input:** List of Entity objects
**Output:** List of VideoSource objects (with transcripts)

```python
"""
YouTube Search -- For each entity, search YouTube and download transcripts.
Uses YouTube Data API v3 for search and youtube-transcript-api for transcripts.
"""
from dataclasses import dataclass, field
from utils.youtube_client import search_youtube, get_transcript
import asyncio

@dataclass
class VideoSource:
    video_id: str
    url: str
    title: str
    channel: str
    transcript: str  # Full transcript text with timestamps
    transcript_entries: list  # [{text, start, duration}]
    entity_name: str  # Which entity this was found for
    search_query: str  # Which query found this

async def search_for_entities(entities: list) -> list[VideoSource]:
    """Search YouTube for all entities in parallel."""
    all_sources = []
    seen_video_ids = set()

    # Build all search tasks
    tasks = []
    for entity in entities:
        for query in entity.youtube_queries:
            tasks.append((entity.name, query))

    # Execute searches (rate-limited)
    for entity_name, query in tasks:
        results = search_youtube(query, max_results=5)

        for result in results:
            vid_id = result['video_id']
            if vid_id in seen_video_ids:
                continue
            seen_video_ids.add(vid_id)

            # Get transcript
            transcript_entries = get_transcript(vid_id)
            if not transcript_entries:
                continue  # Skip videos with no transcript

            transcript_text = ' '.join(
                f"[{format_timestamp(e['start'])}] {e['text']}"
                for e in transcript_entries
            )

            # Truncate if too long
            if len(transcript_text) > 50000:
                transcript_text = transcript_text[:50000] + "\n[TRUNCATED]"

            all_sources.append(VideoSource(
                video_id=vid_id,
                url=f"https://www.youtube.com/watch?v={vid_id}",
                title=result['title'],
                channel=result.get('channel', ''),
                transcript=transcript_text,
                transcript_entries=transcript_entries,
                entity_name=entity_name,
                search_query=query
            ))

        await asyncio.sleep(0.1)  # Rate limiting

    return all_sources

def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"
```

---

### Step 3: Transcript Analysis (`steps/step3_transcript_analysis.py`)

**Input:** VideoSources + Entities
**Output:** List of BrollCandidate objects

This is the core intelligence step. Claude reads each transcript and identifies moments that match entities from the script. **Critically, for every match it must also extract the exact transcript excerpt that justified the match** -- this "reasoning" is surfaced later in the HTML editing guide.

```python
"""
Transcript Analysis -- Send each transcript to Claude to find relevant timestamps.
For each match, Claude must return the transcript excerpt that justified it,
so the editing guide can explain WHY this clip was chosen.
"""
from dataclasses import dataclass
from utils.claude_client import call_claude
import json, asyncio

@dataclass
class BrollCandidate:
    url: str
    video_title: str
    channel: str
    start_time: str  # MM:SS
    end_time: str    # MM:SS
    entity_name: str
    description: str
    relevance_score: int  # 1-10
    era_appropriate: bool
    with_audio: bool  # Should original audio play?
    source_type: str  # "interview", "news", "documentary", "stock", "other"
    transcript_excerpt: str  # The exact transcript lines that matched -- REQUIRED for the editing guide
    match_reasoning: str  # 1-2 sentence explanation of WHY this clip fits

ANALYSIS_PROMPT = """You are analyzing a YouTube video transcript to find B-roll clips for a finance documentary.

VIDEO: "{title}" ({url})
CHANNEL: {channel}

I need B-roll for these entities:
{entity_list}

Here is the transcript (timestamps in brackets):
{transcript}

For EVERY relevant moment in this transcript, return a JSON object:
{{
    "start_time": "MM:SS",
    "end_time": "MM:SS",
    "entity_name": "which entity this serves",
    "description": "what is happening visually in this moment (1 sentence)",
    "relevance_score": 1-10 (10 = perfect match, talks directly about the entity),
    "era_appropriate": true/false (does the time period match?),
    "with_audio": true/false (is the speaker saying something powerful enough to play their audio instead of voiceover? Reserve this for impactful statements only),
    "source_type": "interview" | "news" | "documentary" | "conference" | "other",
    "transcript_excerpt": "Copy the EXACT transcript text (with timestamps) from the start_time to end_time range. Include 1-2 lines before and after for context. This will be shown to the editor to justify the clip selection.",
    "match_reasoning": "1-2 sentences explaining WHY this clip fits the entity. Reference what the speaker says or what is shown. Example: 'Solomon discusses his early rejection from Goldman in his own words, matching script line about his 1984 application.'"
}}

RULES:
- Each clip should be 3-10 seconds (give start and end times accordingly)
- Only include moments with relevance_score >= 5
- Mark era_appropriate=false if the footage is clearly from a different decade than the entity's era
- with_audio=true should be VERY rare (only for genuinely powerful statements)
- transcript_excerpt is MANDATORY -- never leave it empty
- match_reasoning is MANDATORY -- explain the connection between the clip content and the entity
- Be generous -- find as many usable moments as possible. More is better.

Return a JSON array. Nothing else."""

async def analyze_transcripts(
    video_sources: list,
    entities: list,
    batch_size: int = 10
) -> list[BrollCandidate]:
    """Analyze all transcripts in parallel batches."""
    all_candidates = []

    # Group video sources by the entity they were found for
    entity_map = {e.name: e for e in entities}

    # Build analysis tasks
    tasks = []
    for source in video_sources:
        # Find all entities this video might serve (not just the one it was searched for)
        relevant_entities = []
        for entity in entities:
            # Check if any of the entity's keywords appear in the transcript
            name_lower = entity.name.lower()
            if name_lower in source.transcript.lower():
                relevant_entities.append(entity)

        # Always include the entity it was searched for
        if source.entity_name in entity_map:
            search_entity = entity_map[source.entity_name]
            if search_entity not in relevant_entities:
                relevant_entities.append(search_entity)

        if not relevant_entities:
            continue

        entity_list = '\n'.join(
            f"- {e.name} (type: {e.type}, era: {e.era}): {e.notes}"
            for e in relevant_entities
        )

        tasks.append((source, entity_list, relevant_entities))

    # Process in batches
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        batch_results = await asyncio.gather(*[
            _analyze_single(source, entity_list, relevant_entities)
            for source, entity_list, relevant_entities in batch
        ])
        for candidates in batch_results:
            all_candidates.extend(candidates)

    return all_candidates

async def _analyze_single(source, entity_list, relevant_entities) -> list[BrollCandidate]:
    """Analyze a single transcript."""
    prompt = ANALYSIS_PROMPT.format(
        title=source.title,
        url=source.url,
        channel=source.channel,
        entity_list=entity_list,
        transcript=source.transcript[:40000]  # Ensure under context limit
    )

    response = call_claude(prompt, model="sonnet", max_tokens=4096)

    try:
        results = json.loads(response)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            results = json.loads(match.group())
        else:
            return []

    candidates = []
    for r in results:
        candidates.append(BrollCandidate(
            url=source.url,
            video_title=source.title,
            channel=source.channel or '',
            start_time=r['start_time'],
            end_time=r['end_time'],
            entity_name=r['entity_name'],
            description=r['description'],
            relevance_score=r['relevance_score'],
            era_appropriate=r.get('era_appropriate', True),
            with_audio=r.get('with_audio', False),
            source_type=r.get('source_type', 'other'),
            transcript_excerpt=r.get('transcript_excerpt', ''),
            match_reasoning=r.get('match_reasoning', '')
        ))

    return candidates
```

---

### Step 4: Image Search (`steps/step4_image_search.py`)

**Input:** Entities
**Output:** List of ImageAsset objects + downloaded files

```python
"""
Image Search -- Find and download still images for each entity.
Uses Google Custom Search API for image discovery and Playwright for article screenshots.
"""
from dataclasses import dataclass
from utils.image_client import search_images, download_image, screenshot_article
from PIL import Image
import os

@dataclass
class ImageAsset:
    filename: str  # "1.png", "2.png", etc.
    filepath: str  # Full path to downloaded file
    source_url: str
    entity_name: str
    description: str
    width: int
    height: int
    type: str  # "photo", "article_screenshot", "chart", "document"
    search_query: str  # The query that found this image
    match_reasoning: str = ""  # WHY this image fits -- shown in the editing guide
    highlight_text: str = ""  # Text to highlight (for article screenshots)

async def search_and_download_images(
    entities: list,
    output_dir: str,
    start_index: int = 1
) -> list[ImageAsset]:
    """Search for and download images for all entities."""
    os.makedirs(output_dir, exist_ok=True)
    assets = []
    counter = start_index

    for entity in entities:
        for query in entity.image_queries:
            results = search_images(query, max_results=5)

            for result in results:
                image_url = result['url']
                # Download image
                temp_path = os.path.join(output_dir, f"temp_{counter}.png")
                success = download_image(image_url, temp_path)

                if not success:
                    continue

                # Validate resolution
                try:
                    img = Image.open(temp_path)
                    w, h = img.size
                    if w < 1280 or h < 720:
                        os.remove(temp_path)
                        continue
                except:
                    os.remove(temp_path)
                    continue

                # Rename to final name
                final_name = f"{counter}.png"
                final_path = os.path.join(output_dir, final_name)
                os.rename(temp_path, final_path)

                # Determine image type
                img_type = "photo"
                url_lower = image_url.lower()
                if any(d in url_lower for d in ['wsj.com', 'nytimes.com', 'bloomberg.com', 'ft.com']):
                    img_type = "article_screenshot"
                elif 'chart' in query.lower() or 'graph' in query.lower():
                    img_type = "chart"

                # Build reasoning
                reasoning = f"Found via query '{query}' for entity '{entity.name}' (era: {entity.era}). "
                reasoning += f"Source: {result.get('source', 'unknown')}. "
                reasoning += f"Image type: {img_type}. Resolution: {w}x{h}."

                assets.append(ImageAsset(
                    filename=final_name,
                    filepath=final_path,
                    source_url=image_url,
                    entity_name=entity.name,
                    description=f"{entity.name} - {query}",
                    width=w,
                    height=h,
                    type=img_type,
                    search_query=query,
                    match_reasoning=reasoning
                ))

                counter += 1

        # For quote entities, try to screenshot the article
        if entity.type == 'quote' and entity.notes:
            article_path = os.path.join(output_dir, f"{counter}.png")
            success = await screenshot_article(entity.notes, article_path)
            if success:
                try:
                    img = Image.open(article_path)
                    w, h = img.size
                    assets.append(ImageAsset(
                        filename=f"{counter}.png",
                        filepath=article_path,
                        source_url=entity.notes,
                        entity_name=entity.name,
                        description=f"Article screenshot: {entity.name}",
                        width=w, height=h,
                        type="article_screenshot",
                        search_query=f"article screenshot for {entity.name}",
                        match_reasoning=f"Direct article screenshot for quote entity '{entity.name}'. Source article: {entity.notes}",
                        highlight_text=entity.name
                    ))
                    counter += 1
                except:
                    pass

    return assets
```

---

### Step 5: Script Annotation (`steps/step5_annotation.py`)

**Input:** Original script + BrollCandidates + ImageAssets
**Output:** Annotated script (markdown string) + a structured assignment map (for the HTML guide)

```python
"""
Script Annotation -- The core assembly step.
Claude takes the script, the library of found B-roll clips, and the library of images,
and assigns the best asset to each line.

This step produces TWO outputs:
1. The annotated script markdown (for the editor to read)
2. A structured JSON assignment map (for the HTML editing guide)
"""
from utils.claude_client import call_claude
import json, re

ANNOTATION_PROMPT = """You are the final assembly step of an automated B-roll research pipeline for rareliquid, a finance YouTube channel.

You have a documentary SCRIPT and a LIBRARY of visual assets (B-roll video clips and still images). Your job is to annotate every line of the script with the best matching visual asset AND explain your reasoning.

## SCRIPT (with line numbers):
{numbered_script}

## B-ROLL VIDEO LIBRARY:
{broll_library}

## STILL IMAGE LIBRARY:
{image_library}

## YOUR TASK:

You must return TWO things separated by the delimiter `===ASSIGNMENT_MAP===`:

### PART 1: ANNOTATED SCRIPT (markdown)

For EVERY line of the script, insert the best matching visual asset reference directly after (or inline with) the text. Follow these rules:

1. **Every line gets at least one visual.** If a line has no good match, write: `[NO B-ROLL FOUND - need alternative]`
2. **Format B-roll as:** `[URL, start - end]`
   Example: `[https://www.youtube.com/watch?v=abc123, 2:15 - 2:22]`
3. **Format B-roll with audio as:** `[URL, start - end, WITH AUDIO]`
   Use this ONLY when with_audio=true AND relevance_score >= 8
4. **Format still images as:** `[pic N]`
   If the image is an article screenshot, add highlight instructions: `[pic N, highlight "key phrase"]`
5. **Prioritize by relevance_score** -- higher scores first
6. **Alternate between B-roll and stills** -- never 3+ consecutive still images without a video clip
7. **Check era_appropriate** -- never assign a clip marked era_appropriate=false unless nothing else exists
8. **Flag custom visual opportunities** -- If a line discusses data, timelines, or comparisons and no good asset exists, write: `[CUSTOM VISUAL NEEDED: description]`
9. **Never reuse the same B-roll clip for two different lines** unless it's the same topic being revisited
10. **Source type preference:** interview > news > documentary > conference > other

At the end of the annotated script, add a SUMMARY section:
```
## Asset Summary
- Total B-roll clips assigned: X
- Unique B-roll sources: X
- Total still images assigned: X
- Unique still images: X
- B-roll with audio: X
- Custom visuals needed: X
- Lines with no visual: X
- Coverage: X%
```

### PART 2: ASSIGNMENT MAP (JSON)

After the delimiter `===ASSIGNMENT_MAP===`, return a JSON array where each object represents one script line:

```json
[
  {{
    "line_number": 1,
    "line_text": "the original script line text",
    "assets": [
      {{
        "type": "broll" | "broll_with_audio" | "image" | "custom_visual",
        "url": "YouTube URL or null for images",
        "start_time": "MM:SS or null",
        "end_time": "MM:SS or null",
        "pic_number": null or integer,
        "video_title": "title of the YouTube video",
        "channel": "channel name",
        "description": "what this asset shows",
        "transcript_excerpt": "the transcript text from the video at this timestamp that made this a good match",
        "match_reasoning": "1-2 sentences: WHY does this asset fit this script line? What does the viewer see? How does it connect to what the narrator is saying?",
        "relevance_score": 1-10,
        "era_appropriate": true/false,
        "source_type": "interview/news/documentary/etc",
        "image_source_url": "original image URL or null",
        "image_type": "photo/article_screenshot/chart or null"
      }}
    ],
    "has_gap": false,
    "custom_visual_description": null
  }}
]
```

CRITICAL: The `match_reasoning` field must be detailed and specific. Do NOT write generic reasons like "relevant to topic". Instead write things like:
- "At 2:15 the Bloomberg anchor says 'Solomon was rejected by Goldman twice before eventually joining', which directly narrates the same rejection story as this script line."
- "This 1986 photo of Drexel Burnham Lambert's trading floor matches the era (1986) and the specific company mentioned in the script."
- "The CNBC interview shows Solomon at his DJ booth, which visually illustrates the script's mention of him DJing at Lollapalooza."

## OUTPUT FORMAT:

Return the annotated script markdown, then `===ASSIGNMENT_MAP===`, then the JSON array."""

def annotate_script(
    script_text: str,
    broll_candidates: list,
    image_assets: list
) -> tuple[str, list[dict]]:
    """Annotate the script with visual assets. Returns (annotated_md, assignment_map)."""
    # Number the lines
    lines = script_text.strip().split('\n')
    numbered_script = '\n'.join(f"[{i+1}] {line}" for i, line in enumerate(lines))

    # Format B-roll library
    broll_entries = []
    for c in sorted(broll_candidates, key=lambda x: -x.relevance_score):
        entry = (
            f"- URL: {c.url}, {c.start_time} - {c.end_time} | "
            f"Entity: {c.entity_name} | Score: {c.relevance_score}/10 | "
            f"Type: {c.source_type} | Era OK: {c.era_appropriate} | "
            f"Audio: {c.with_audio} | Desc: {c.description} | "
            f"Video: \"{c.video_title}\" (Channel: {c.channel}) | "
            f"Transcript: \"{c.transcript_excerpt[:200]}\" | "
            f"Reasoning: {c.match_reasoning}"
        )
        broll_entries.append(entry)
    broll_library = '\n'.join(broll_entries[:300])  # Cap to avoid context overflow

    # Format image library
    image_entries = []
    for img in image_assets:
        hl = f" | Highlight: \"{img.highlight_text}\"" if img.highlight_text else ""
        entry = (
            f"- [pic {img.filename.replace('.png', '')}] | "
            f"Entity: {img.entity_name} | Type: {img.type} | "
            f"Desc: {img.description} | Query: {img.search_query} | "
            f"Reasoning: {img.match_reasoning}{hl}"
        )
        image_entries.append(entry)
    image_library = '\n'.join(image_entries)

    prompt = ANNOTATION_PROMPT.format(
        numbered_script=numbered_script,
        broll_library=broll_library,
        image_library=image_library
    )

    # This is the most critical step
    response = call_claude(prompt, max_tokens=16384)

    # Split into annotated script and assignment map
    if '===ASSIGNMENT_MAP===' in response:
        parts = response.split('===ASSIGNMENT_MAP===', 1)
        annotated_md = parts[0].strip()
        try:
            # Extract JSON from the second part
            json_text = parts[1].strip()
            # Remove markdown code fences if present
            if json_text.startswith('```'):
                json_text = re.sub(r'^```\w*\n?', '', json_text)
                json_text = re.sub(r'\n?```$', '', json_text)
            assignment_map = json.loads(json_text)
        except (json.JSONDecodeError, IndexError):
            assignment_map = []
    else:
        annotated_md = response
        assignment_map = []

    return annotated_md, assignment_map
```

---

### Step 6: Custom Visuals (`steps/step6_custom_visuals.py`)

**Input:** Lines flagged `[CUSTOM VISUAL NEEDED]` from Step 5
**Output:** HTML files

```python
"""
Custom Visual Generation -- For lines flagged as needing a custom visual,
generate self-contained HTML files using Claude.
"""
from utils.claude_client import call_claude
import re, os

VISUAL_PROMPT = """Generate a self-contained HTML file for this visual element in a finance documentary:

DESCRIPTION: {description}

STYLE REQUIREMENTS:
- Dark background: #1B2A4A or #111827
- Clean sans-serif font (system-ui or Inter)
- Accent colors for highlights (use #C0392B for emphasis, #27AE60 for positive, #3498DB for neutral)
- Professional, cinematic look suitable for a YouTube documentary
- 16:9 aspect ratio (1920x1080 viewport)
- All text must be legible at 1080p
- If data is included, add a small source citation at the bottom

Return ONLY the complete HTML file. No markdown wrapping, no explanation."""

def generate_custom_visuals(annotated_script: str, output_dir: str) -> list[str]:
    """Find CUSTOM VISUAL NEEDED flags and generate HTML files."""
    os.makedirs(output_dir, exist_ok=True)

    # Find all custom visual flags
    pattern = r'\[CUSTOM VISUAL NEEDED: (.+?)\]'
    matches = re.findall(pattern, annotated_script)

    generated_files = []
    for i, description in enumerate(matches[:3]):  # Cap at 3
        response = call_claude(
            VISUAL_PROMPT.format(description=description),
            model="sonnet",
            max_tokens=8192
        )

        # Clean response (remove markdown wrapping if present)
        html = response.strip()
        if html.startswith('```html'):
            html = html[7:]
        if html.startswith('```'):
            html = html[3:]
        if html.endswith('```'):
            html = html[:-3]

        filename = f"custom_visual_{i+1}.html"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(html.strip())

        generated_files.append(filepath)

    return generated_files
```

---

### Step 7: Quality Evaluation (`steps/step7_quality_eval.py`)

**This is the most important step.** The bot evaluates its own output against the quality thresholds and decides whether to iterate.

```python
"""
Quality Evaluation -- Check the output against all quality thresholds.
Returns a detailed report and a PASS/FAIL verdict.
If FAIL, identifies which steps need to be re-run and what's missing.
"""
import re
import json
from config import QUALITY_THRESHOLDS

def evaluate_quality(
    annotated_script: str,
    broll_candidates: list,
    image_assets: list,
    custom_visuals: list,
    script_text: str
) -> dict:
    """Evaluate the quality of the bot's output."""
    total_lines = len([l for l in script_text.strip().split('\n') if l.strip()])

    # Count assets in annotated script
    broll_refs = re.findall(r'\[https://www\.youtube\.com/watch\?v=([^,\]]+)', annotated_script)
    pic_refs = re.findall(r'\[pic (\d+)', annotated_script)
    audio_refs = re.findall(r'WITH AUDIO', annotated_script)
    gaps = re.findall(r'\[NO B-ROLL FOUND', annotated_script)
    custom_flags = re.findall(r'\[CUSTOM VISUAL NEEDED', annotated_script)

    # Unique counts
    unique_broll = len(set(broll_refs))
    unique_images = len(set(pic_refs))
    total_broll_placements = len(broll_refs)
    total_image_placements = len(pic_refs)

    # Lines with at least one visual
    lines_with_visual = 0
    for line in annotated_script.split('\n'):
        if '[https://' in line or '[pic ' in line or '[CUSTOM VISUAL' in line:
            lines_with_visual += 1

    coverage_pct = (lines_with_visual / max(total_lines, 1)) * 100
    gap_pct = (len(gaps) / max(total_lines, 1)) * 100

    # Estimate script duration (rough: 150 words per minute)
    word_count = len(script_text.split())
    estimated_duration_min = word_count / 150

    broll_per_min = unique_broll / max(estimated_duration_min, 1)
    images_per_min = unique_images / max(estimated_duration_min, 1)

    # Average relevance score
    relevance_scores = [c.relevance_score for c in broll_candidates if c.relevance_score >= 5]
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

    # Era mismatches
    era_mismatches = sum(1 for c in broll_candidates if not c.era_appropriate and c.relevance_score >= 6)

    # Stock footage estimate (source_type == "other" is a rough proxy)
    stock_count = sum(1 for c in broll_candidates if c.source_type == "other")
    stock_pct = (stock_count / max(len(broll_candidates), 1)) * 100

    # Build report
    report = {
        "metrics": {
            "unique_broll_sources": unique_broll,
            "unique_still_images": unique_images,
            "total_broll_placements": total_broll_placements,
            "total_image_placements": total_image_placements,
            "broll_with_audio": len(audio_refs),
            "custom_visuals_generated": len(custom_visuals),
            "custom_visuals_flagged": len(custom_flags),
            "lines_with_no_visual": len(gaps),
            "coverage_percentage": round(coverage_pct, 1),
            "gap_percentage": round(gap_pct, 1),
            "estimated_script_duration_min": round(estimated_duration_min, 1),
            "broll_per_minute": round(broll_per_min, 1),
            "images_per_minute": round(images_per_min, 1),
            "avg_relevance_score": round(avg_relevance, 1),
            "era_mismatches": era_mismatches,
            "stock_footage_percentage": round(stock_pct, 1),
        },
        "checks": {},
        "failures": [],
        "warnings": [],
        "verdict": "PASS"
    }

    # Run checks against thresholds
    T = QUALITY_THRESHOLDS

    checks = [
        ("unique_broll_sources", unique_broll, ">=", T["min_broll_unique_sources"],
         f"Need {T['min_broll_unique_sources']} unique B-roll sources, have {unique_broll}",
         "step2_step3"),
        ("unique_still_images", unique_images, ">=", T["min_still_images"],
         f"Need {T['min_still_images']} unique images, have {unique_images}",
         "step4"),
        ("coverage_percentage", coverage_pct, ">=", T["min_coverage_percentage"],
         f"Need {T['min_coverage_percentage']}% coverage, have {coverage_pct:.1f}%",
         "step5"),
        ("gap_percentage", gap_pct, "<=", T["max_gap_percentage"],
         f"Gap percentage {gap_pct:.1f}% exceeds max {T['max_gap_percentage']}%",
         "step2_step3_step4"),
        ("avg_relevance_score", avg_relevance, ">=", T["min_avg_relevance_score"],
         f"Avg relevance {avg_relevance:.1f} below min {T['min_avg_relevance_score']}",
         "step3"),
        ("era_mismatches", era_mismatches, "<=", T["max_era_mismatch_count"],
         f"Found {era_mismatches} era mismatches (max: {T['max_era_mismatch_count']})",
         "step3"),
        ("broll_per_minute", broll_per_min, ">=", T["min_broll_per_minute"],
         f"B-roll/min: {broll_per_min:.1f} below min {T['min_broll_per_minute']}",
         "step2_step3"),
        ("images_per_minute", images_per_min, ">=", T["min_images_per_minute"],
         f"Images/min: {images_per_min:.1f} below min {T['min_images_per_minute']}",
         "step4"),
    ]

    for name, value, op, threshold, message, fix_step in checks:
        if op == ">=" and value < threshold:
            report["checks"][name] = "FAIL"
            report["failures"].append({"check": name, "message": message, "fix_step": fix_step})
        elif op == "<=" and value > threshold:
            report["checks"][name] = "FAIL"
            report["failures"].append({"check": name, "message": message, "fix_step": fix_step})
        else:
            report["checks"][name] = "PASS"

    # Warnings (below target but above minimum)
    if unique_broll < T["target_broll_unique_sources"] and unique_broll >= T["min_broll_unique_sources"]:
        report["warnings"].append(f"B-roll below target: {unique_broll} (target: {T['target_broll_unique_sources']})")
    if unique_images < T["target_still_images"] and unique_images >= T["min_still_images"]:
        report["warnings"].append(f"Images below target: {unique_images} (target: {T['target_still_images']})")
    if coverage_pct < T["target_coverage_percentage"] and coverage_pct >= T["min_coverage_percentage"]:
        report["warnings"].append(f"Coverage below target: {coverage_pct:.1f}% (target: {T['target_coverage_percentage']}%)")

    # Final verdict
    if report["failures"]:
        report["verdict"] = "FAIL"
    elif report["warnings"]:
        report["verdict"] = "PASS_WITH_WARNINGS"
    else:
        report["verdict"] = "PASS"

    return report

def get_retry_steps(report: dict) -> list[str]:
    """Determine which steps to re-run based on failures."""
    steps_to_retry = set()
    for failure in report["failures"]:
        for step in failure["fix_step"].split("_"):
            steps_to_retry.add(step)
    return sorted(steps_to_retry)
```

---

### Step 8: Interactive HTML Editing Guide (`steps/step8_html_guide.py`)

**THIS IS THE KEY NEW OUTPUT.** This step generates a self-contained, interactive HTML file that serves as the editor's primary reference. For every script line, it shows:

- The script text
- The assigned asset(s) with clickable YouTube links that jump to the exact timestamp
- Embedded YouTube thumbnails / inline image previews
- The transcript excerpt from the video at that timestamp (so the editor can read what's being said)
- A written explanation of WHY this clip/image was chosen for this line
- Color-coded badges for asset type (B-roll / Image / Audio / Custom Visual)
- Filter/search controls to navigate quickly
- A coverage progress bar and quality stats dashboard

```python
"""
HTML Editing Guide Generator -- Builds a self-contained interactive HTML file
that the editor uses as a visual reference for the entire video.

Every script line is shown with:
- Its assigned assets (clickable YouTube embeds at exact timestamps, inline image previews)
- The transcript excerpt from the source video at that timestamp
- A reasoning paragraph explaining WHY each asset was chosen
- Color-coded asset type badges
- Filter/search/navigation controls
"""
import json
import os
import html as html_lib
import base64

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

    lines = script_text.strip().split('\n')

    # Build image data map (filename -> base64 for inline embedding, or relative path)
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

    # Build broll lookup for supplementary info
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

    # Metrics for dashboard
    metrics = quality_report.get("metrics", {})

    # Build the line cards data
    line_cards_json = json.dumps(assignment_map, indent=2)
    image_map_json = json.dumps(image_map, indent=2)
    broll_lookup_json = json.dumps(broll_lookup, indent=2)
    metrics_json = json.dumps(metrics, indent=2)

    html_content = _build_html(
        line_cards_json=line_cards_json,
        image_map_json=image_map_json,
        broll_lookup_json=broll_lookup_json,
        metrics_json=metrics_json,
        verdict=quality_report.get("verdict", "UNKNOWN"),
        total_lines=len(lines)
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def _build_html(
    line_cards_json: str,
    image_map_json: str,
    broll_lookup_json: str,
    metrics_json: str,
    verdict: str,
    total_lines: int
) -> str:
    """Build the complete self-contained HTML string.

    IMPORTANT FOR THE LLM BUILDING THIS:
    This function must return a COMPLETE, self-contained HTML document.
    The HTML must include ALL of the following features inline (no external dependencies):

    1. DASHBOARD HEADER:
       - Quality verdict badge (PASS = green, FAIL = red, WARNINGS = yellow)
       - Coverage progress bar (percentage of lines with assets)
       - Stat cards: total B-roll clips, unique sources, total images, B-roll with audio,
         custom visuals, gaps, avg relevance score, era mismatches
       - Estimated script duration

    2. CONTROLS BAR:
       - Search box that filters script lines by text content
       - Filter buttons: "All", "B-Roll", "Images", "Audio", "Custom", "Gaps"
       - Sort toggle: by line number (default) or by relevance score

    3. SCRIPT LINE CARDS (one per line, scrollable):
       Each card contains:

       a) LINE HEADER:
          - Line number badge
          - The full script line text
          - Asset count indicator (e.g., "2 assets")

       b) ASSET PANELS (one per assigned asset, stacked vertically inside the card):
          Each panel has a colored left border indicating type:
          - Blue (#3498DB) = B-roll video
          - Purple (#9B59B6) = B-roll with audio
          - Green (#27AE60) = Still image
          - Orange (#E67E22) = Custom visual
          - Red (#E74C3C) = Gap (no asset found)

          For B-ROLL assets, the panel shows:
          - Asset type badge ("B-ROLL" or "B-ROLL + AUDIO")
          - Video title and channel name
          - Clickable YouTube link that opens at the exact start timestamp
            (use https://www.youtube.com/watch?v=VIDEO_ID&t=SECONDS format)
          - Start time - End time display
          - Relevance score (as a colored bar: red < 6, yellow 6-7, green > 7)
          - Era badge ("Era OK" in green or "ERA MISMATCH" in red)
          - Source type badge (interview/news/documentary/etc)
          - TRANSCRIPT EXCERPT section: a blockquote showing the exact words spoken
            in the video at that timestamp range, with a label "What's being said:"
          - REASONING section: a paragraph labeled "Why this fits:" explaining
            the connection between the clip and the script line

          For IMAGE assets, the panel shows:
          - Asset type badge ("STILL IMAGE")
          - Inline image preview (use the relative path pictures/N.png,
            rendered as an <img> tag with max-width: 400px)
          - Image filename and type (photo/article_screenshot/chart)
          - Source URL (linked)
          - Resolution display
          - Search query that found it
          - REASONING section: "Why this fits:" paragraph

          For CUSTOM VISUAL assets, the panel shows:
          - Asset type badge ("CUSTOM VISUAL")
          - Description of what should be built
          - Link to the generated HTML file if it exists

          For GAPS, the panel shows:
          - "NO ASSET FOUND" badge in red
          - Suggestion text for manual research

    4. STYLING:
       - Dark theme: background #0f172a, cards #1e293b, text #e2e8f0
       - Smooth card hover effects (subtle lift/glow)
       - Responsive layout (works on any screen width)
       - Monospace font for timestamps and transcript excerpts
       - All CSS must be in a <style> tag (no external stylesheets)
       - Smooth scrolling
       - Collapsible transcript/reasoning sections (click to expand, default expanded)

    5. JAVASCRIPT (inline, no external libraries):
       - Search filtering: hide cards that don't match search text
       - Type filtering: show only cards with selected asset type
       - Smooth scroll-to-top button
       - Click-to-copy YouTube URLs
       - Collapsible sections for transcript excerpts and reasoning
       - Line count updates when filtering

    The function must construct this HTML as a Python string and return it.
    Use f-strings or string concatenation. Embed the JSON data as <script> variables.
    """

    # The LLM must implement this function fully.
    # It should build and return the complete HTML string.
    # Embed the data like this:
    #   <script>
    #     const LINE_CARDS = {line_cards_json};
    #     const IMAGE_MAP = {image_map_json};
    #     const BROLL_LOOKUP = {broll_lookup_json};
    #     const METRICS = {metrics_json};
    #   </script>
    # Then render everything client-side with vanilla JS.

    raise NotImplementedError(
        "YOU MUST IMPLEMENT THIS FUNCTION. "
        "Build the complete HTML string using the specification in the docstring above. "
        "This is the most important output of the entire pipeline."
    )
```

---

### CLI Entry Point (`broll_bot.py`)

```python
"""
rareliquid B-Roll Bot -- Main entry point.
Runs the full pipeline with quality-gated iteration.
"""
import asyncio
import argparse
import json
import os
import time
from config import MAX_ITERATIONS, ITERATION_STRATEGY
from steps.step1_entity_extraction import extract_entities
from steps.step2_youtube_search import search_for_entities
from steps.step3_transcript_analysis import analyze_transcripts
from steps.step4_image_search import search_and_download_images
from steps.step5_annotation import annotate_script
from steps.step6_custom_visuals import generate_custom_visuals
from steps.step7_quality_eval import evaluate_quality, get_retry_steps
from steps.step8_html_guide import generate_html_guide

async def run_pipeline(script_path: str, output_dir: str):
    """Run the full B-roll research pipeline with iteration."""
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "pictures")
    videos_dir = os.path.join(output_dir, "videos")
    visuals_dir = os.path.join(output_dir, "custom_visuals")
    os.makedirs(videos_dir, exist_ok=True)

    # Load script
    with open(script_path) as f:
        script_text = f.read()

    print(f"Script loaded: {len(script_text)} chars, {len(script_text.split())} words")
    print(f"Estimated duration: {len(script_text.split()) / 150:.1f} minutes")
    print()

    # Track state across iterations
    all_broll_candidates = []
    all_image_assets = []
    all_custom_visuals = []
    entities = []
    assignment_map = []
    steps_to_retry = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"{'='*60}")
        print(f"ITERATION {iteration}/{MAX_ITERATIONS}")
        print(f"{'='*60}")
        start_time = time.time()

        # Step 1: Entity Extraction (only on first iteration)
        if iteration == 1:
            print("\n[Step 1] Extracting entities...")
            entities = extract_entities(script_text)
            print(f"  Found {len(entities)} entities")
            for e in entities:
                print(f"    {e.type:10s} | {e.name} (era: {e.era})")

        # Step 2: YouTube Search
        if iteration == 1 or "step2" in steps_to_retry:
            print("\n[Step 2] Searching YouTube...")
            new_sources = await search_for_entities(entities)
            print(f"  Found {len(new_sources)} video sources with transcripts")

        # Step 3: Transcript Analysis
        if iteration == 1 or "step3" in steps_to_retry:
            print("\n[Step 3] Analyzing transcripts...")
            new_candidates = await analyze_transcripts(new_sources, entities)
            all_broll_candidates.extend(new_candidates)
            # Deduplicate
            seen = set()
            deduped = []
            for c in all_broll_candidates:
                key = (c.url, c.start_time, c.end_time)
                if key not in seen:
                    seen.add(key)
                    deduped.append(c)
            all_broll_candidates = deduped
            print(f"  Total B-roll candidates: {len(all_broll_candidates)}")

        # Step 4: Image Search
        if iteration == 1 or "step4" in steps_to_retry:
            print("\n[Step 4] Searching for images...")
            new_images = await search_and_download_images(
                entities, images_dir, start_index=len(all_image_assets) + 1
            )
            all_image_assets.extend(new_images)
            print(f"  Total images: {len(all_image_assets)}")

        # Step 5: Script Annotation
        print("\n[Step 5] Annotating script...")
        annotated, assignment_map = annotate_script(script_text, all_broll_candidates, all_image_assets)

        # Step 6: Custom Visuals
        if iteration == 1:
            print("\n[Step 6] Generating custom visuals...")
            all_custom_visuals = generate_custom_visuals(annotated, visuals_dir)
            print(f"  Generated {len(all_custom_visuals)} custom visuals")

        # Step 7: Quality Evaluation
        print("\n[Step 7] Evaluating quality...")
        report = evaluate_quality(
            annotated, all_broll_candidates, all_image_assets,
            all_custom_visuals, script_text
        )

        elapsed = time.time() - start_time
        print(f"\n  Iteration {iteration} completed in {elapsed:.1f}s")
        print(f"\n  VERDICT: {report['verdict']}")
        print(f"  Metrics:")
        for k, v in report['metrics'].items():
            print(f"    {k}: {v}")

        if report['failures']:
            print(f"\n  FAILURES:")
            for f in report['failures']:
                print(f"    FAIL: {f['message']}")

        if report['warnings']:
            print(f"\n  WARNINGS:")
            for w in report['warnings']:
                print(f"    WARN: {w}")

        # Check if we pass
        if report['verdict'] in ('PASS', 'PASS_WITH_WARNINGS'):
            print(f"\nQuality gate PASSED. Finalizing output.")
            break

        # Determine what to retry
        steps_to_retry = get_retry_steps(report)
        if not steps_to_retry or iteration == MAX_ITERATIONS:
            print(f"\nMax iterations reached or no retry steps identified.")
            break

        print(f"\n  Retrying steps: {steps_to_retry}")

        # For retry: add more aggressive search queries to entities
        if "step2" in steps_to_retry or "step3" in steps_to_retry:
            for entity in entities:
                entity.youtube_queries.append(f"{entity.name} explained")
                entity.youtube_queries.append(f"{entity.name} overview")

        if "step4" in steps_to_retry:
            for entity in entities:
                entity.image_queries.append(f"{entity.name} photo")
                entity.image_queries.append(f"{entity.name} news")

    # ── Save outputs ──────────────────────────────────────────────

    print(f"\n{'='*60}")
    print("SAVING OUTPUTS")
    print(f"{'='*60}")

    # Annotated script
    annotated_path = os.path.join(output_dir, "annotated_script.md")
    with open(annotated_path, 'w') as f:
        f.write(annotated)
    print(f"  Annotated script: {annotated_path}")

    # Quality report
    report_path = os.path.join(output_dir, "quality_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Quality report: {report_path}")

    # Videos folder -- B-roll manifest (the editor's cache)
    broll_manifest = {
        "description": "B-roll video cache manifest. Each entry is a clip the editor can pull from YouTube. Use the URL with &t= parameter to jump to the start timestamp.",
        "total_clips": len(all_broll_candidates),
        "unique_sources": len(set(c.url for c in all_broll_candidates)),
        "clips": [
            {
                "url": c.url,
                "url_at_timestamp": f"{c.url}&t={_timestamp_to_seconds(c.start_time)}",
                "video_title": c.video_title,
                "channel": c.channel,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "duration_seconds": _timestamp_to_seconds(c.end_time) - _timestamp_to_seconds(c.start_time),
                "entity": c.entity_name,
                "description": c.description,
                "relevance_score": c.relevance_score,
                "era_appropriate": c.era_appropriate,
                "with_audio": c.with_audio,
                "source_type": c.source_type,
                "transcript_excerpt": c.transcript_excerpt,
                "match_reasoning": c.match_reasoning
            }
            for c in sorted(all_broll_candidates, key=lambda x: -x.relevance_score)
        ]
    }
    manifest_path = os.path.join(videos_dir, "broll_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(broll_manifest, f, indent=2)
    print(f"  B-roll manifest: {manifest_path}")

    # Asset inventory (combined)
    inventory = {
        "broll_candidates": [
            {
                "url": c.url, "start": c.start_time, "end": c.end_time,
                "entity": c.entity_name, "relevance": c.relevance_score,
                "description": c.description, "with_audio": c.with_audio,
                "era_ok": c.era_appropriate, "source_type": c.source_type,
                "transcript_excerpt": c.transcript_excerpt,
                "match_reasoning": c.match_reasoning
            }
            for c in all_broll_candidates
        ],
        "images": [
            {
                "filename": img.filename, "entity": img.entity_name,
                "type": img.type, "source_url": img.source_url,
                "description": img.description,
                "match_reasoning": img.match_reasoning
            }
            for img in all_image_assets
        ],
        "custom_visuals": all_custom_visuals
    }
    inventory_path = os.path.join(output_dir, "asset_inventory.json")
    with open(inventory_path, 'w') as f:
        json.dump(inventory, f, indent=2)
    print(f"  Asset inventory: {inventory_path}")

    # Step 8: Interactive HTML Editing Guide
    print(f"\n[Step 8] Generating interactive HTML editing guide...")
    guide_path = os.path.join(output_dir, "editing_guide.html")
    generate_html_guide(
        script_text=script_text,
        assignment_map=assignment_map,
        broll_candidates=all_broll_candidates,
        image_assets=all_image_assets,
        custom_visuals=all_custom_visuals,
        quality_report=report,
        output_path=guide_path,
        images_dir=images_dir
    )
    print(f"  Editing guide: {guide_path}")

    print(f"\n  Pictures folder: {images_dir}/ ({len(all_image_assets)} files)")
    print(f"  Videos folder: {videos_dir}/ (manifest with {len(all_broll_candidates)} clips)")
    print(f"  Custom visuals: {visuals_dir}/ ({len(all_custom_visuals)} files)")
    print(f"\n{'='*60}")
    print(f"DONE. Final verdict: {report['verdict']}")
    print(f"{'='*60}")

def _timestamp_to_seconds(ts: str) -> int:
    """Convert MM:SS to seconds."""
    parts = ts.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0

def main():
    parser = argparse.ArgumentParser(description="rareliquid B-Roll Research Bot")
    parser.add_argument("--script", required=True, help="Path to script file (.txt or .md)")
    parser.add_argument("--output", default="./output", help="Output directory")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.script, args.output))

if __name__ == "__main__":
    main()
```

---

### Utility: Claude Client (`utils/claude_client.py`)

```python
"""
Wrapper that calls Claude via the `claude` CLI (Claude Code Max mode).
No API key needed -- runs for free under Max subscription.

Uses `claude -p "prompt"` which sends a one-shot prompt and returns the response.
"""
import subprocess
import json
import tempfile
import os

def call_claude(prompt: str, model: str = "sonnet", max_tokens: int = None) -> str:
    """
    Call Claude via Claude Code CLI subprocess.

    Args:
        prompt: The prompt to send
        model: "sonnet" or "opus" (passed via --model flag)
        max_tokens: ignored (Claude Code manages this)

    Returns:
        The response text from Claude
    """
    # For long prompts, write to a temp file and pipe it in
    # to avoid shell argument length limits
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        # Build the claude command
        cmd = [
            "claude",
            "-p",  # print mode (non-interactive, one-shot)
            "--output-format", "text",  # plain text output
        ]

        # Read prompt from file via stdin
        with open(prompt_file, 'r') as pf:
            result = subprocess.run(
                cmd,
                stdin=pf,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per call
            )

        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")

        return result.stdout.strip()

    finally:
        os.unlink(prompt_file)


def call_claude_with_file(prompt: str, file_path: str) -> str:
    """
    Call Claude with a file attachment (useful for long transcripts).
    Uses Claude Code's ability to read files.
    """
    full_prompt = f"{prompt}\n\nFile contents of {file_path}:\n<file>\n{open(file_path).read()}\n</file>"
    return call_claude(full_prompt)
```

**How this works:** Instead of hitting the Anthropic API with an API key, every LLM call shells out to `claude -p` which runs under your Claude Code Max subscription at zero marginal cost.

---

### Utility: YouTube Client (`utils/youtube_client.py`)

```python
"""YouTube Data API v3 search + youtube-transcript-api for transcripts."""
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from config import YOUTUBE_API_KEY

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def search_youtube(query: str, max_results: int = 5) -> list[dict]:
    """Search YouTube and return video metadata."""
    try:
        response = youtube.search().list(
            q=query,
            type='video',
            part='snippet',
            maxResults=max_results,
            order='relevance',
            relevanceLanguage='en'
        ).execute()

        results = []
        for item in response.get('items', []):
            results.append({
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description'],
            })
        return results
    except Exception as e:
        print(f"  YouTube search error for '{query}': {e}")
        return []

def get_transcript(video_id: str) -> list[dict]:
    """Get transcript for a YouTube video."""
    try:
        entries = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return entries
    except Exception:
        try:
            # Try auto-generated captions
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_generated_transcript(['en'])
            return transcript.fetch()
        except Exception:
            return []
```

---

### Utility: Image Client (`utils/image_client.py`)

```python
"""Google Custom Search for images + Playwright for article screenshots."""
from googleapiclient.discovery import build
from config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID
import aiohttp
import os

cse = build('customsearch', 'v1', developerKey=GOOGLE_CSE_API_KEY)

def search_images(query: str, max_results: int = 5) -> list[dict]:
    """Search Google for images."""
    try:
        response = cse.cse().list(
            q=query,
            searchType='image',
            num=min(max_results, 10),
            cx=GOOGLE_CSE_ID,
            imgSize='LARGE',
            safe='active'
        ).execute()

        results = []
        for item in response.get('items', []):
            results.append({
                'url': item['link'],
                'title': item.get('title', ''),
                'source': item.get('displayLink', ''),
                'width': item.get('image', {}).get('width', 0),
                'height': item.get('image', {}).get('height', 0),
            })
        return results
    except Exception as e:
        print(f"  Image search error for '{query}': {e}")
        return []

def download_image(url: str, filepath: str) -> bool:
    """Download an image from URL."""
    import requests
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        if response.status_code == 200 and len(response.content) > 5000:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False

async def screenshot_article(url: str, filepath: str) -> bool:
    """Screenshot a web article using Playwright."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            await page.goto(url, timeout=15000)
            await page.wait_for_timeout(2000)  # Wait for render
            await page.screenshot(path=filepath, full_page=False)
            await browser.close()
        return os.path.exists(filepath)
    except Exception as e:
        print(f"  Screenshot error for {url}: {e}")
        return False
```

---

## Input File

Create `input_script.txt` in the project root. This is where the user pastes their script. The bot reads from this file.

The file should be empty by default with a comment:

```
PASTE YOUR SCRIPT BELOW THIS LINE AND RUN: python broll_bot.py --script input_script.txt --output ./output/
---

```

---

## Output Folder Structure

After a successful run, the output directory contains:

```
output/
|-- annotated_script.md          # Full script with inline [URL, MM:SS - MM:SS] and [pic N] annotations
|-- editing_guide.html           # THE INTERACTIVE HTML GUIDE (open in browser)
|-- pictures/                    # Downloaded still images
|   |-- 1.png
|   |-- 2.png
|   |-- 3.png
|   |-- ...
|-- videos/                      # B-roll cache for editor
|   |-- broll_manifest.json      # All clips: URL, timestamps, reasoning, transcript excerpts
|-- custom_visuals/              # Generated HTML data visualizations
|   |-- custom_visual_1.html
|   |-- ...
|-- asset_inventory.json         # Combined inventory of all assets
|-- quality_report.json          # Quality metrics and pass/fail verdicts
```

### What the `videos/` folder is for

The `videos/` folder is a **cache/manifest** for your video editor. It does NOT contain downloaded video files. Instead, `broll_manifest.json` contains every B-roll clip reference with:

- The YouTube URL (with `&t=` parameter to jump to the exact second)
- Start and end timestamps
- Duration in seconds
- The transcript excerpt at that timestamp
- Why this clip was chosen
- Relevance score and metadata

Your editor uses this manifest to know which YouTube videos to pull clips from and exactly where to cut. The manifest is sorted by relevance score (best clips first).

### What `editing_guide.html` is for

This is the **primary deliverable for the editor**. Open it in a browser and it shows:

- Every script line as a card
- Each card shows the assigned B-roll/image with:
  - A clickable YouTube link that opens at the exact timestamp
  - The transcript excerpt from that moment in the video ("What's being said")
  - A reasoning paragraph ("Why this fits: At 2:15 the interviewer asks Solomon about his Goldman rejections, and Solomon describes being turned down twice -- directly matching this script line about his 1984 application")
  - Inline image previews for still image assignments
- Dashboard with quality stats
- Search/filter controls to navigate

---

## Test Script

Use this as your test script. Save it as `test/test_script.txt`:

```
It's a question that sounds impossible.
How does someone get rejected twice by Goldman Sachs and still end up winning an intense cage battle to be selected as CEO?
And how does he run the most prestigious bank in the world while also DJ'ing at Lollapalooza and partying in the Hamptons with the Chainsmokers?
Most people know Solomon as Goldman's CEO. But his path wasn't clean, linear, or traditional.
He didn't break into banking out of college and his daddy wasn't a bank executive.
So how did he rise? And why did his unconventional path end up giving him more leverage than the people who looked perfect on paper?
Today, we break down the full story of how one of the most powerful bankers in the world blazed his own path and denied all standard formulas.
This is the unlikely story of David Solomon, aka DJ D-Sol.
Now if you've been following me for a while, you've seen me teach you how to break into banking, but this video is about the long game.
And what drives a successful long-term finance career isn't school prestige or building DCFs. It's the decisions, habits, and experiences that compound over time.
Solomon's story doesn't start anywhere near Wall Street.
He was born in Hartsdale, New York in 1962 and his father worked in publishing while his mother worked in audiology.
He worked at a local Baskin Robbins and as a camp counselor in high school and afterwards went to Hamilton College, where he played on the rugby team and joined the social frat Alpha Delta Phi.
Graduation arrives in 1984 and he takes his first big swing by applying to Goldman for an analyst role. And Goldman says no.
So he finds another entry point into finance by joining Irving Trust, where there's no prestige or glamour, but it's where he learns about credit, risk, and real financial fundamentals.
While working at Irving, Solomon decides to shoot his shot once again at Goldman, who again rejects him.
But at a cocktail party in 1986, Solomon gets introduced to a few people from Drexel Burnham Lambert, which at the time was the beating heart of the junk-bond boom.
```

---

## How to Run

```bash
# 1. Set up environment
pip install -r requirements.txt
playwright install chromium

# 2. Set API keys in .env file (NO Anthropic key needed -- Claude Code Max handles LLM calls):
# YOUTUBE_API_KEY=AIza...
# GOOGLE_CSE_API_KEY=AIza...
# GOOGLE_CSE_ID=...
#
# Get these from:
# - YouTube Data API v3: https://console.cloud.google.com -> Enable "YouTube Data API v3" -> Create API key
# - Google Custom Search: Same console -> Enable "Custom Search API" -> Create Programmable Search Engine at https://programmablesearchengine.google.com (enable "Search the entire web" + "Image search")

# 3. Run the bot
python broll_bot.py --script input_script.txt --output ./output/

# 4. Open the interactive guide in your browser
open output/editing_guide.html

# 5. Check quality report
cat output/quality_report.json

# 6. Review annotated script
cat output/annotated_script.md
```

---

## Quality Parameters Reference

These are the quality gates. The bot iterates until all pass or MAX_ITERATIONS is reached:

| Parameter | Minimum | Target | What Fails It |
|---|---|---|---|
| Unique B-roll sources | 60 | 80 | Not enough YouTube search or transcript analysis |
| Unique still images | 45 | 60 | Not enough image search queries |
| Coverage % | 90% | 98% | Too many unmatched lines |
| Gap % | <=5% | 0% | Lines with [NO B-ROLL FOUND] |
| Avg relevance score | >=6.0 | >=7.0 | Low-quality matches from transcripts |
| Era mismatches | 0 | 0 | Clips flagged era_appropriate=false assigned anyway |
| B-roll per minute | >=4.0 | >=5.5 | Not dense enough |
| Images per minute | >=3.0 | >=4.0 | Not dense enough |
| Stock footage % | <=10% | <=5% | Too much generic footage |
| Custom visuals | 1-3 | 2 | Missing data/timeline opportunities |

---

## Iteration Logic

When a quality check fails, the bot identifies which step to re-run:

| Failure | Re-run Steps | Strategy |
|---|---|---|
| Not enough B-roll | Steps 2+3 | Add fallback search queries ("[entity] explained", "[entity] overview") |
| Not enough images | Step 4 | Add fallback image queries ("[entity] photo", "[entity] news") |
| Low coverage | Step 5 | Re-annotate with lower relevance threshold |
| Era mismatches | Step 3 | Re-analyze with stricter era filtering |
| Low relevance | Steps 2+3 | Search for more specific queries |

The bot adds the new results to the existing pool (doesn't discard previous work) and re-runs the annotation step with the larger asset library.

---

## After Building: Manual Validation

Once the bot runs successfully on the test script, manually check:

1. **Open the editing_guide.html** -- Does every script line have assets? Do the reasoning paragraphs make sense? Do the transcript excerpts match?
2. **Click 5 random YouTube links** -- Do the timestamps actually show relevant content?
3. **Open 5 random images in pictures/** -- Are they the right person/company? Right era? Good quality?
4. **Read the annotated script** -- Does every annotation make sense for its line?
5. **Check the custom visuals** -- Do the HTML files render correctly?
6. **Open broll_manifest.json in videos/** -- Is it well-structured? Can your editor parse it?
