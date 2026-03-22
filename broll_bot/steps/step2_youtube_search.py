"""
YouTube Search -- For each entity, search YouTube and download transcripts.
"""
from dataclasses import dataclass, field
from utils.youtube_client import search_youtube, get_transcript
from utils.formatters import format_timestamp
import asyncio


@dataclass
class VideoSource:
    video_id: str
    url: str
    title: str
    channel: str
    transcript: str
    transcript_entries: list
    entity_name: str
    search_query: str


async def search_for_entities(entities: list) -> list[VideoSource]:
    """Search YouTube for all entities."""
    all_sources = []
    seen_video_ids = set()

    tasks = []
    for entity in entities:
        for query in entity.youtube_queries:
            tasks.append((entity.name, query))

    for entity_name, query in tasks:
        results = search_youtube(query, max_results=5)

        for result in results:
            vid_id = result['video_id']
            if vid_id in seen_video_ids:
                continue
            seen_video_ids.add(vid_id)

            transcript_entries = get_transcript(vid_id)
            if not transcript_entries:
                continue

            transcript_text = ' '.join(
                f"[{format_timestamp(e['start'])}] {e['text']}"
                for e in transcript_entries
            )

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

        await asyncio.sleep(0.1)

    return all_sources
