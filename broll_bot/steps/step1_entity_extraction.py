"""
Entity Extraction -- Parse the script and identify every person, company,
event, quote, data point, and metaphor that needs a visual.
"""
from dataclasses import dataclass, field
from utils.claude_client import call_claude
import json
import re


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
- "notes": any special instructions (e.g., "defunct company -- need 1980s archival footage", "metaphor -- find creative visual")

IMPORTANT:
- Every person mentioned by name gets their own entity
- Every company gets its own entity
- Every specific quote or attributed statement gets a "quote" entity
- Every metaphor or analogy gets a "metaphor" entity
- Every data point gets a "concept" entity
- If a person is discussed in multiple eras, create SEPARATE entities for each era

Return a JSON array of objects. Nothing else -- no markdown, no explanation, just the JSON array.

SCRIPT:
{script}"""


def extract_entities(script_text: str) -> list[Entity]:
    """Extract all entities from the script."""
    lines = script_text.strip().split('\n')
    numbered_script = '\n'.join(f"[{i+1}] {line}" for i, line in enumerate(lines))

    response = call_claude(
        EXTRACTION_PROMPT.format(script=numbered_script),
        model="sonnet",
        max_tokens=8192
    )

    try:
        entities_raw = json.loads(response)
    except json.JSONDecodeError:
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
