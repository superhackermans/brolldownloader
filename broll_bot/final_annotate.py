#!/usr/bin/env python3
"""
Final B-Roll Annotation Script
Maps script lines to video timestamps with transcript matching
Handles OCR variations and creates comprehensive assignments
"""

import json
import re
from typing import List, Dict, Tuple, Set

# ============= LOAD DATA =============
print("=" * 60)
print("LOADING SOURCE FILES")
print("=" * 60)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/input_script.txt', 'r') as f:
    script_text = f.read()

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/new_transcripts.json', 'r') as f:
    transcripts_data = json.load(f)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json', 'r') as f:
    current_map = json.load(f)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/image_assets.json', 'r') as f:
    images_data = json.load(f)

# Build indices
transcript_map = {v['video_id']: v for v in transcripts_data}
print(f"✓ Loaded {len(transcript_map)} video transcripts")
print(f"✓ Loaded {len(images_data)} image assets")
print(f"✓ Loaded {len(current_map)} script line assignments")

# ============= SEARCH ENGINE =============

def normalize_text(text: str) -> str:
    """Normalize text for searching (handle OCR errors)"""
    # Common OCR variations
    replacements = {
        'Quatron': 'Quattrone',
        'quatron': 'quattrone',
        'QUATRON': 'QUATTRONE',
        'Boutro': 'Boutros',
        'boutro': 'boutros',
        'Autonomey': 'Autonomy',
        'autonomey': 'autonomy',
    }
    normalized = text
    for wrong, correct in replacements.items():
        normalized = normalized.replace(wrong, correct)
    return normalized

def search_transcript_smart(video_id: str, script_line: str, keywords: List[str]) -> List[Dict]:
    """
    Intelligent transcript search with OCR tolerance
    Returns best matching segments with timestamps
    """
    if video_id not in transcript_map:
        return []

    video = transcript_map[video_id]
    entries = video.get('transcript', [])

    if not entries:
        return []

    matches = []

    # Search for keyword matches
    for keyword in keywords:
        keyword_lower = keyword.lower()

        for i, entry in enumerate(entries):
            text = normalize_text(entry.get('text', '')).lower()

            # Check for keyword or fuzzy match
            if keyword_lower in text or (len(keyword) > 3 and keyword_lower[:4] in text):
                # Found a match - create a clip segment
                # Aim for 5-7 seconds of content
                clip_start_idx = max(0, i - 1)
                clip_end_idx = min(len(entries) - 1, i + 3)

                start_ts = entries[clip_start_idx].get('start', '0:00')
                end_ts = entries[clip_end_idx].get('end', '0:10')

                # Gather context
                context_entries = entries[clip_start_idx:clip_end_idx + 1]
                full_text = ' '.join([e.get('text', '') for e in context_entries])

                # Calculate relevance
                score = 0
                for kw in keywords:
                    if kw.lower() in text:
                        score += 1

                matches.append({
                    'keyword': keyword,
                    'start': start_ts,
                    'end': end_ts,
                    'excerpt': entry.get('text', ''),
                    'context': full_text[:250],
                    'score': score,
                    'matching_entry_index': i
                })

    # Remove duplicates (same timestamp)
    unique_matches = {}
    for match in matches:
        key = f"{match['start']}-{match['end']}"
        if key not in unique_matches or match['score'] > unique_matches[key]['score']:
            unique_matches[key] = match

    # Sort by score and return top 3
    sorted_matches = sorted(unique_matches.values(), key=lambda x: -x['score'])
    return sorted_matches[:3]

def find_image_matches(line_text: str, keywords: List[str]) -> List[int]:
    """Find image indices that match the script line"""
    matching_images = []

    for i, image in enumerate(images_data):
        entity = (image.get('entity_name', '') or '').lower()
        description = (image.get('description', '') or '').lower()

        for keyword in keywords:
            kw_lower = keyword.lower()
            if kw_lower in entity or kw_lower in description:
                matching_images.append(i)
                break

    return matching_images[:5]  # Top 5 matching images

# ============= SCRIPT LINE KEYWORDS =============

SCRIPT_KEYWORDS = {
    # Lines about Steve Jobs / Apple / NeXT
    'jobs': ['Steve Jobs', 'Jobs', 'Apple', 'NeXT', 'personal computing'],
    'apple': ['Apple', 'Steve Jobs', 'NeXT'],

    # IPO mentions
    'ipo': ['IPO', 'public', 'underwriting', 'Morgan Stanley'],
    'netscape': ['Netscape', 'IPO', '1995', 'internet'],
    'cisco': ['Cisco', 'IPO', 'public'],
    'intuit': ['Intuit', 'IPO'],
    'amazon': ['Amazon', 'IPO', 'public'],
    'internet': ['internet', 'technology', 'innovation'],

    # Bank moves
    'deutsche': ['Deutsche', 'Deutsche Bank', 'tech banking'],
    'credit suisse': ['Credit Suisse', 'CSFB', 'tech'],
    'morgan stanley': ['Morgan Stanley', 'Morgan', 'Stanley'],
    'goldman': ['Goldman', 'Goldman Sachs'],

    # Dot-com / crisis
    'crash': ['crash', 'bubble', 'burst', 'collapse'],
    'dot.com': ['dot com', 'dotcom', 'bubble', 'IPO'],
    'crisis': ['crisis', 'recession', '2008', 'financial'],

    # Legal issues
    'prison': ['prison', 'jail', 'sentence', 'trial', 'arrest', 'convicted'],
    'sec': ['SEC', 'investigation', 'subpoena', 'fraud'],
    'fbi': ['FBI', 'arrest', 'charged'],

    # Major deals
    'linkedin': ['LinkedIn', 'Microsoft', 'acquisition'],
    'appdynamics': ['AppDynamics', 'Cisco', 'acquisition'],
    'autonomy': ['Autonomy', 'HP', 'Hewlett Packard', 'writedown'],
    'qualtrics': ['Qualtrics', 'SAP', 'acquisition'],
    'data domain': ['Data Domain', 'EMC'],
    '3par': ['3PAR', 'Dell'],
    'motorola': ['Motorola', 'Google'],

    # People
    'quattrone': ['Quattrone', 'Frank', 'banker', 'tech'],
    'boutros': ['Boutros', 'George Boutros', 'negotiator'],

    # Companies/Institutions
    'qatalyst': ['Qatalyst', 'founding', 'boutique'],
    'google': ['Google', 'acquisition', 'CEO'],
    'microsoft': ['Microsoft', 'deal'],
    'yahoo': ['Yahoo', 'acquisition'],
    'tencent': ['Tencent', 'gaming'],
    'pixar': ['Pixar', 'Disney'],
    'youtube': ['YouTube', 'Google', 'acquisition'],
}

def extract_keywords_v2(line_text: str) -> List[str]:
    """Extract keywords from script line using pattern matching"""
    line_lower = line_text.lower()
    keywords = []

    # Check against known patterns
    for pattern_key, pattern_keywords in SCRIPT_KEYWORDS.items():
        for pattern in pattern_keywords:
            if pattern.lower() in line_lower:
                keywords.extend(pattern_keywords)
                break

    # Add fallbacks
    if not keywords:
        if any(word in line_lower for word in ['deal', 'acquisition', 'merger']):
            keywords.extend(['M&A', 'deal', 'banking', 'acquisition'])
        elif any(word in line_lower for word in ['bank', 'banker']):
            keywords.extend(['banking', 'deal', 'financial'])
        else:
            keywords.extend(['deal', 'technology', 'investment'])

    return list(set(keywords))

# ============= PROCESS ASSIGNMENTS =============

print("\n" + "=" * 60)
print("PROCESSING SCRIPT LINES")
print("=" * 60)

updated_assignments = []
stats = {
    'total_broll': 0,
    'unique_video_ids': set(),
    'with_transcript_ts': 0,
    'with_audio': 0,
    'total_images': 0,
    'unique_image_count': set(),
    'lines_processed': 0,
    'lines_with_gaps': 0,
}

for line_entry in current_map:
    line_num = line_entry['line_number']
    line_text = line_entry['line_text']
    existing_assets = line_entry.get('assets', [])

    # Skip empty lines
    if not line_text or line_text.strip() in ['HOOK', 'PROMISE', 'SECTION 1', 'SECTION 2', 'SECTION 3',
                                               'SECTION 4', 'SECTION 5', 'OUTRO', 'Transition:']:
        updated_assignments.append(line_entry)
        stats['lines_processed'] += 1
        continue

    # Extract keywords
    keywords = extract_keywords_v2(line_text)

    # Process existing assets
    new_assets = []
    last_asset_type = None

    for asset in existing_assets:
        if asset['type'] == 'broll':
            # Extract video ID from URL
            url_match = re.search(r'v=([a-zA-Z0-9_-]+)', asset.get('url', ''))
            if url_match:
                video_id = url_match.group(1)
                stats['unique_video_ids'].add(video_id)

                # Search for transcript matches
                matches = search_transcript_smart(video_id, line_text, keywords)

                if matches and matches[0].get('start'):
                    # Use best match
                    best_match = matches[0]
                    try:
                        enhanced_asset = {
                            'type': 'broll',
                            'url': asset['url'],
                            'start_time': best_match['start'],
                            'end_time': best_match['end'],
                            'video_title': asset.get('video_title', 'Video'),
                            'channel': asset.get('channel', 'Unknown'),
                            'description': f"Scene showing discussion of {best_match['keyword']}",
                            'transcript_excerpt': best_match['excerpt'][:120],
                            'match_reasoning': f"At {best_match['start']}: '{best_match['excerpt'][:60]}...' discusses {best_match['keyword']} matching script context",
                            'relevance_score': min(9, 6 + best_match['score']),
                            'era_appropriate': asset.get('era_appropriate', True),
                            'with_audio': asset.get('with_audio', False),
                            'source_type': asset.get('source_type', 'interview')
                        }
                        new_assets.append(enhanced_asset)
                        stats['total_broll'] += 1
                        stats['with_transcript_ts'] += 1
                        if enhanced_asset['with_audio']:
                            stats['with_audio'] += 1
                        last_asset_type = 'broll'
                    except Exception as e:
                        # Fallback if enhancement fails
                        new_assets.append(asset)
                        stats['total_broll'] += 1
                else:
                    # No transcript match found, keep original
                    new_assets.append(asset)
                    stats['total_broll'] += 1
                    last_asset_type = 'broll'

        elif asset['type'] == 'image':
            new_assets.append(asset)
            stats['total_images'] += 1
            if 'pic_number' in asset:
                stats['unique_image_count'].add(asset['pic_number'])
            last_asset_type = 'image'

    # Add image if we're missing visuals and don't have 3+ consecutive stills
    if len(new_assets) < 2 and last_asset_type != 'image':
        image_matches = find_image_matches(line_text, keywords)
        if image_matches and len(new_assets) > 0:
            for img_idx in image_matches[:1]:
                new_assets.append({
                    'type': 'image',
                    'pic_number': img_idx,
                    'description': images_data[img_idx].get('description', 'Related image'),
                    'match_reasoning': f"Image of {images_data[img_idx].get('entity_name')} related to script discussion"
                })
                stats['total_images'] += 1
                stats['unique_image_count'].add(img_idx)
                break

    # Mark gaps
    has_gap = len(new_assets) == 0
    if has_gap:
        stats['lines_with_gaps'] += 1

    updated_assignments.append({
        'line_number': line_num,
        'line_text': line_text,
        'assets': new_assets if new_assets else existing_assets,
        'has_gap': has_gap
    })

    stats['lines_processed'] += 1

# ============= SAVE AND REPORT =============

print("\n" + "=" * 60)
print("FINAL STATISTICS")
print("=" * 60)

print(f"\n✓ Script Lines Processed: {stats['lines_processed']}")
print(f"✓ Lines with Assets: {stats['lines_processed'] - stats['lines_with_gaps']}")
print(f"✗ Lines with Gaps: {stats['lines_with_gaps']}")

print(f"\n[B-ROLL CLIPS]")
print(f"✓ Total B-roll Clips: {stats['total_broll']}")
print(f"✓ Unique Video Sources: {len(stats['unique_video_ids'])}")
print(f"✓ Clips with Transcript Timestamps: {stats['with_transcript_ts']}")
print(f"✓ Audio Clips with Narration: {stats['with_audio']}")

print(f"\n[IMAGES]")
print(f"✓ Total Image Assets Used: {stats['total_images']}")
print(f"✓ Unique Image Indices: {len(stats['unique_image_count'])}")

print(f"\n[TOTALS]")
total_assets = stats['total_broll'] + stats['total_images']
print(f"✓ Total Assets Deployed: {total_assets}")

print(f"\n[TARGET GOALS]")
print(f"  B-roll sources: 75-90 (current: {len(stats['unique_video_ids'])})")
print(f"  Images: 55-70 (current: {len(stats['unique_image_count'])})")
print(f"  Total assets: ~148 (current: {total_assets})")

# Save output
output_path = '/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json'
with open(output_path, 'w') as f:
    json.dump(updated_assignments, f, indent=2)

print(f"\n✓ Saved to {output_path}")

# List unique videos
print(f"\n[UNIQUE VIDEO SOURCES] ({len(stats['unique_video_ids'])})")
for video_id in sorted(stats['unique_video_ids'])[:15]:
    if video_id in transcript_map:
        title = transcript_map[video_id]['title'][:55]
        print(f"  • {video_id}: {title}...")

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
