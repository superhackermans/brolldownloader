"""
Script Annotation -- Assign the best visual asset to each script line.
Produces annotated markdown AND a structured assignment map for the HTML guide.
"""
from utils.claude_client import call_claude
import json
import re


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

For EVERY line of the script, insert the best matching visual asset reference directly after the text:

1. **Every line gets at least one visual.** If no good match: `[NO B-ROLL FOUND - need alternative]`
2. **B-roll:** `[URL, start - end]`
3. **B-roll with audio:** `[URL, start - end, WITH AUDIO]` (only when with_audio=true AND relevance >= 8)
4. **Still images:** `[pic N]` or `[pic N, highlight "key phrase"]`
5. **Prioritize by relevance_score**
6. **Alternate B-roll and stills** -- never 3+ consecutive stills without a video clip
7. **Check era_appropriate** -- never assign era_appropriate=false clips unless nothing else exists
8. **Flag custom visual opportunities:** `[CUSTOM VISUAL NEEDED: description]`
9. **Never reuse the same B-roll clip for different lines**
10. **Source type preference:** interview > news > documentary > conference > other

End with:
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

After `===ASSIGNMENT_MAP===`, return a JSON array:
[
  {{
    "line_number": 1,
    "line_text": "the original script line text",
    "assets": [
      {{
        "type": "broll" | "broll_with_audio" | "image" | "custom_visual",
        "url": "YouTube URL or null",
        "start_time": "MM:SS or null",
        "end_time": "MM:SS or null",
        "pic_number": null or integer,
        "video_title": "title of the YouTube video",
        "channel": "channel name",
        "description": "what this asset shows",
        "transcript_excerpt": "the transcript text at this timestamp that justified the match",
        "match_reasoning": "1-2 sentences: WHY does this asset fit this script line?",
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

CRITICAL: match_reasoning must be specific. NOT "relevant to topic". Instead:
- "At 2:15 the Bloomberg anchor says 'Solomon was rejected by Goldman twice', directly matching this script line."
- "This 1986 photo of Drexel Burnham Lambert's trading floor matches the era and company mentioned."
"""


def annotate_script(
    script_text: str,
    broll_candidates: list,
    image_assets: list
) -> tuple[str, list[dict]]:
    """Annotate the script. Returns (annotated_md, assignment_map)."""
    lines = script_text.strip().split('\n')
    numbered_script = '\n'.join(f"[{i+1}] {line}" for i, line in enumerate(lines))

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
    broll_library = '\n'.join(broll_entries[:300])

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

    response = call_claude(prompt, max_tokens=16384)

    if '===ASSIGNMENT_MAP===' in response:
        parts = response.split('===ASSIGNMENT_MAP===', 1)
        annotated_md = parts[0].strip()
        try:
            json_text = parts[1].strip()
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
