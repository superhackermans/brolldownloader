"""
Transcript Analysis -- Send each transcript to Claude to find relevant timestamps.
Returns transcript excerpts and reasoning for every match.
"""
from dataclasses import dataclass
from utils.claude_client import call_claude
import json
import re
import asyncio


@dataclass
class BrollCandidate:
    url: str
    video_title: str
    channel: str
    start_time: str
    end_time: str
    entity_name: str
    description: str
    relevance_score: int
    era_appropriate: bool
    with_audio: bool
    source_type: str
    transcript_excerpt: str
    match_reasoning: str


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
    "description": "what is happening visually (1 sentence)",
    "relevance_score": 1-10 (10 = perfect match),
    "era_appropriate": true/false,
    "with_audio": true/false (VERY rare - only for powerful statements),
    "source_type": "interview" | "news" | "documentary" | "conference" | "other",
    "transcript_excerpt": "Copy the EXACT transcript text (with timestamps) from this range. Include 1-2 lines of context.",
    "match_reasoning": "1-2 sentences: WHY does this clip fit? Reference what the speaker says."
}}

RULES:
- Each clip should be 3-10 seconds
- Only include moments with relevance_score >= 5
- Mark era_appropriate=false if footage is from a different decade than the entity's era
- with_audio=true should be VERY rare
- transcript_excerpt is MANDATORY
- match_reasoning is MANDATORY
- Be generous -- find as many usable moments as possible

Return a JSON array. Nothing else."""


async def analyze_transcripts(
    video_sources: list,
    entities: list,
    batch_size: int = 10
) -> list[BrollCandidate]:
    """Analyze all transcripts in parallel batches."""
    all_candidates = []
    entity_map = {e.name: e for e in entities}

    tasks = []
    for source in video_sources:
        relevant_entities = []
        for entity in entities:
            if entity.name.lower() in source.transcript.lower():
                relevant_entities.append(entity)

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
        transcript=source.transcript[:40000]
    )

    response = call_claude(prompt, model="sonnet", max_tokens=4096)

    try:
        results = json.loads(response)
    except json.JSONDecodeError:
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
