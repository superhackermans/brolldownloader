#!/usr/bin/env python3
"""
Enhanced B-Roll Annotation with Transcript Timestamp Matching
Searches transcripts for specific moments matching script content
"""

import json
import re
from typing import List, Dict, Tuple

# ============= LOAD DATA =============
print("Loading source files...")

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/input_script.txt', 'r') as f:
    script_text = f.read()

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/new_transcripts.json', 'r') as f:
    transcripts_data = json.load(f)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json', 'r') as f:
    current_map = json.load(f)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/image_assets.json', 'r') as f:
    images = json.load(f)

# Build transcript index
transcript_map = {v['video_id']: v for v in transcripts_data}
print(f"Loaded {len(transcript_map)} video transcripts")

# ============= HELPER FUNCTIONS =============

def ts_to_seconds(ts_str: str) -> int:
    """Convert MM:SS or HH:MM:SS to seconds"""
    try:
        parts = ts_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

def seconds_to_ts(seconds: int) -> str:
    """Convert seconds to MM:SS format"""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"

def search_transcript(video_id: str, keywords: List[str], context_window: int = 2) -> List[Dict]:
    """
    Search transcript for keyword matches with context
    Returns list of matches with start/end times and surrounding text
    """
    if video_id not in transcript_map:
        return []

    video = transcript_map[video_id]
    entries = video.get('transcript', [])

    if not entries:
        return []

    matches = []
    text_lower = ' '.join([e.get('text', '').lower() for e in entries])

    # Search for any keyword
    for keyword in keywords:
        if keyword.lower() in text_lower:
            # Find all entries containing this keyword
            for i, entry in enumerate(entries):
                if keyword.lower() in entry.get('text', '').lower():
                    # Extract surrounding context
                    context_start = max(0, i - context_window)
                    context_end = min(len(entries), i + context_window + 1)
                    context_text = ' '.join([e.get('text', '') for e in entries[context_start:context_end]])

                    # Calculate clip duration (aim for 5-7 seconds)
                    start_ts = entries[context_start].get('start', '0:00')
                    end_ts = entries[min(i + 2, len(entries) - 1)].get('end', '0:10')
                    duration = ts_to_seconds(end_ts) - ts_to_seconds(start_ts)

                    matches.append({
                        'keyword': keyword,
                        'start': start_ts,
                        'end': end_ts,
                        'duration': duration,
                        'excerpt': entry.get('text'),
                        'context': context_text[:200],
                        'score': len(keyword.split())  # Longer keywords score higher
                    })
                    break

    # Sort by score and return top matches
    matches = sorted(matches, key=lambda x: -x['score'])
    return matches[:3]

def extract_best_keywords(line_text: str) -> List[str]:
    """Extract best search keywords from script line"""
    line_lower = line_text.lower()
    keywords = []

    # Major entities and events
    entity_patterns = {
        'Steve Jobs': ['steve jobs', 'jobs'],
        'Apple': ['apple'],
        'NeXT': ['next'],
        'Netscape': ['netscape'],
        'Cisco': ['cisco'],
        'Intuit': ['intuit'],
        'Amazon': ['amazon'],
        'Morgan Stanley': ['morgan stanley', 'morgan'],
        'Deutsche Bank': ['deutsche'],
        'Credit Suisse': ['credit suisse', 'csfb'],
        'Goldman': ['goldman'],
        'Google': ['google'],
        'Microsoft': ['microsoft'],
        'LinkedIn': ['linkedin'],
        'AppDynamics': ['appdynamics', 'app dynamics'],
        'Autonomy': ['autonomy'],
        'HP': ['hewlett packard', ' hp '],
        'Qualtrics': ['qualtrics'],
        'SAP': ['sap'],
        'Data Domain': ['data domain'],
        'EMC': ['emc'],
        '3PAR': ['3par'],
        'Dell': ['dell'],
        'Aruba': ['aruba'],
        'Motorola': ['motorola'],
        'Tencent': ['tencent'],
        'Pixar': ['pixar'],
        'Disney': ['disney'],
        'YouTube': ['youtube'],
        'George Boutros': ['george boutros', 'boutros'],
        'Qatalyst': ['qatalyst'],
        'SEC': ['sec'],
        'FBI': ['fbi'],
        'IPO': ['ipo', 'public offering'],
        'M&A': ['m&a', 'merger', 'acquisition'],
        'Recession': ['recession', 'financial crisis'],
        'Dot-com': ['dot com', 'dotcom', 'bubble'],
        'Conviction': ['conviction', 'prison', 'trial', 'arrested'],
        'Yahoo': ['yahoo'],
    }

    for entity, patterns in entity_patterns.items():
        for pattern in patterns:
            if pattern in line_lower:
                keywords.append(entity)
                break

    # Activity verbs
    if any(word in line_lower for word in ['went public', 'took public', 'ipo']):
        keywords.append('IPO')

    if any(word in line_lower for word in ['acquired', 'acquisition', 'bought', 'deal']):
        keywords.append('acquisition')

    if any(word in line_lower for word in ['negotiat', 'sales process', 'bidding']):
        keywords.append('negotiations')

    return list(set(keywords)) if keywords else ['banking', 'deal']

# ============= ENHANCE EACH LINE =============

print("\nSearching transcripts for keyword matches...")

updated_map = []
stats = {
    'total_broll': 0,
    'unique_videos': set(),
    'audio_clips': 0,
    'with_transcripts': 0,
    'total_images': 0,
}

for line_entry in current_map:
    line_num = line_entry['line_number']
    line_text = line_entry['line_text']
    existing_assets = line_entry.get('assets', [])

    # Extract keywords
    keywords = extract_best_keywords(line_text)

    new_assets = []
    last_was_video = False

    for asset in existing_assets:
        if asset['type'] == 'broll':
            # Extract video ID
            url_match = re.search(r'v=([a-zA-Z0-9_-]+)', asset.get('url', ''))
            if url_match:
                video_id = url_match.group(1)
                stats['unique_videos'].add(video_id)

                # Search for matching timestamps
                matches = search_transcript(video_id, keywords)

                if matches and matches[0]['duration'] > 3:
                    # Use the best match
                    best = matches[0]
                    updated_asset = {
                        'type': 'broll',
                        'url': asset['url'],
                        'start_time': best['start'],
                        'end_time': best['end'],
                        'video_title': asset.get('video_title', 'Unknown'),
                        'channel': asset.get('channel', 'Unknown'),
                        'description': f"Scene showing {best['keyword']}",
                        'transcript_excerpt': best['excerpt'][:150],
                        'match_reasoning': f"Transcript at {best['start']}: '{best['excerpt'][:80]}...' matches script discussion of {keywords[0] if keywords else 'topic'}",
                        'relevance_score': min(9, 7 + len([k for k in keywords if k.lower() in best['context'].lower()])),
                        'era_appropriate': True,
                        'with_audio': asset.get('with_audio', False),
                        'source_type': asset.get('source_type', 'interview')
                    }
                    new_assets.append(updated_asset)
                    stats['total_broll'] += 1
                    if updated_asset['with_audio']:
                        stats['audio_clips'] += 1
                    stats['with_transcripts'] += 1
                    last_was_video = True
                else:
                    # No good match, keep original but note missing data
                    new_assets.append(asset)
                    stats['total_broll'] += 1
                    last_was_video = True

        elif asset['type'] == 'image':
            new_assets.append(asset)
            stats['total_images'] += 1
            last_was_video = False

    # Ensure we have some coverage
    if not new_assets:
        new_assets = existing_assets

    updated_map.append({
        'line_number': line_num,
        'line_text': line_text,
        'assets': new_assets,
        'has_gap': len(new_assets) == 0
    })

# ============= SAVE AND REPORT =============

print(f"\nUpdating {len(updated_map)} script lines...")
print(f"\nStatistics:")
print(f"  Total B-roll clips: {stats['total_broll']}")
print(f"  Unique video sources: {len(stats['unique_videos'])}")
print(f"  Clips with transcript timestamps: {stats['with_transcripts']}")
print(f"  Audio clips with narration: {stats['audio_clips']}")
print(f"  Total images: {stats['total_images']}")
print(f"  Total assets: {stats['total_broll'] + stats['total_images']}")

output_path = '/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json'
with open(output_path, 'w') as f:
    json.dump(updated_map, f, indent=2)

print(f"\nSaved to {output_path}")

# List unique videos used
print(f"\nUnique video sources ({len(stats['unique_videos'])}):")
for vid in sorted(stats['unique_videos'])[:20]:
    if vid in transcript_map:
        title = transcript_map[vid]['title'][:60]
        print(f"  {vid}: {title}")

