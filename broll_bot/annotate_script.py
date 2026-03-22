#!/usr/bin/env python3
"""
B-Roll Annotation Script for Qatalyst Partners YouTube Video
Assigns specific video clips and images to each script line with exact timestamps
"""

import json
import re
from collections import defaultdict
from datetime import timedelta

# ============= LOAD DATA FILES =============
print("Loading files...")
with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/input_script.txt', 'r') as f:
    script_text = f.read()

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/new_transcripts.json', 'r') as f:
    transcripts_data = json.load(f)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json', 'r') as f:
    existing_map = json.load(f)

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/image_assets.json', 'r') as f:
    images = json.load(f)

# Create video ID to transcript mapping
transcript_map = {}
for video in transcripts_data:
    video_id = video['video_id']
    transcript_map[video_id] = video

print(f"Loaded {len(transcript_map)} videos with transcripts")
print(f"Loaded {len(images)} image assets")
print(f"Loaded {len(existing_map)} script lines")

# ============= HELPER FUNCTIONS =============

def ts_to_seconds(ts_str):
    """Convert MM:SS or HH:MM:SS format to seconds"""
    try:
        parts = ts_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

def seconds_to_ts(seconds):
    """Convert seconds to MM:SS format"""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"

def find_transcript_matches(script_line, video_id, keywords, match_threshold=1):
    """Search transcript for keyword matches"""
    if video_id not in transcript_map:
        return []

    video = transcript_map[video_id]
    transcript_entries = video.get('transcript', [])

    matches = []
    script_line_lower = script_line.lower()

    for entry in transcript_entries:
        text = entry.get('text', '').lower()
        start_ts = entry.get('start', '0:00')
        end_ts = entry.get('end', '0:00')

        # Check each keyword
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text:
                # Calculate match score (how many keywords match in this entry)
                score = len([k for k in keywords if k.lower() in text])
                matches.append({
                    'start': start_ts,
                    'end': end_ts,
                    'text': entry.get('text'),
                    'keywords': keyword,
                    'score': score
                })
                break

    # Sort by score (highest first) and return top results
    matches = sorted(matches, key=lambda x: (-x['score'], ts_to_seconds(x['start'])))
    return matches[:3]

def get_video_title_channel(video_id, existing_assets):
    """Extract video title and channel from existing assets"""
    for asset in existing_assets:
        if asset.get('type') == 'broll' and video_id in asset.get('url', ''):
            return asset.get('video_title'), asset.get('channel')
    return "Unknown", "Unknown"

def extract_keywords_from_line(line_text):
    """Extract key terms from script line for searching"""
    # Remove common words and extract meaningful terms
    line_lower = line_text.lower()

    # Define keyword sets for major topics
    keywords = []

    if any(word in line_lower for word in ['steve jobs', 'apple', 'jobs', 'next']):
        keywords.extend(['Steve Jobs', 'Apple', 'Jobs', 'NeXT'])

    if 'netscape' in line_lower:
        keywords.append('Netscape')

    if any(word in line_lower for word in ['ipо', 'ipo', 'public']):
        keywords.extend(['IPO', 'public'])

    if 'cisco' in line_lower:
        keywords.append('Cisco')

    if 'intuit' in line_lower:
        keywords.append('Intuit')

    if 'amazon' in line_lower:
        keywords.append('Amazon')

    if 'deutsche' in line_lower:
        keywords.extend(['Deutsche', 'Deutsche Bank'])

    if 'credit suisse' in line_lower or 'csfb' in line_lower:
        keywords.extend(['Credit Suisse', 'CSFB'])

    if any(word in line_lower for word in ['dot com', 'dotcom', 'bubble', 'crash']):
        keywords.extend(['dot com', 'bubble', 'crash', 'collapse'])

    if any(word in line_lower for word in ['linkedin', 'microsoft', 'acquisition']):
        keywords.extend(['LinkedIn', 'Microsoft', 'acquisition'])

    if 'appdynamics' in line_lower or 'app dynamics' in line_lower:
        keywords.extend(['AppDynamics', 'Cisco', 'acquisition'])

    if 'autonomy' in line_lower or 'hewlett packard' in line_lower or 'hp' in line_lower:
        keywords.extend(['Autonomy', 'Hewlett Packard', 'HP', 'writedown'])

    if 'qualtrics' in line_lower or 'sap' in line_lower:
        keywords.extend(['Qualtrics', 'SAP'])

    if any(word in line_lower for word in ['prison', 'jail', 'arrest', 'conviction', 'sentence']):
        keywords.extend(['prison', 'arrest', 'trial', 'conviction'])

    if any(word in line_lower for word in ['sec', 'investigation', 'subpoena', 'grand jury']):
        keywords.extend(['SEC', 'investigation', 'subpoena', 'grand jury'])

    if 'goldman' in line_lower:
        keywords.extend(['Goldman', 'Goldman Sachs'])

    if 'morgan stanley' in line_lower or 'morgan' in line_lower:
        keywords.extend(['Morgan Stanley', 'Morgan', 'Stanley'])

    if 'george boutros' in line_lower or 'boutros' in line_lower:
        keywords.extend(['George Boutros', 'Boutros'])

    if 'qatalyst' in line_lower:
        keywords.extend(['Qatalyst', 'founding'])

    if any(word in line_lower for word in ['recession', 'financial crisis', '2008', 'bear stearns', 'lehman']):
        keywords.extend(['recession', 'crisis', 'financial', 'Bear Stearns', 'Lehman'])

    if any(word in line_lower for word in ['data domain', 'emc', '3par', 'dell']):
        keywords.extend(['Data Domain', 'EMC', '3PAR', 'Dell'])

    if 'youtube' in line_lower:
        keywords.append('YouTube')

    if 'google' in line_lower:
        keywords.append('Google')

    if 'aruba' in line_lower:
        keywords.extend(['Aruba', 'networks'])

    # Clean up and deduplicate
    keywords = list(set(keywords))

    return keywords if keywords else ['deal', 'banking', 'M&A']

# ============= CREATE ENHANCED ASSIGNMENT MAP =============

print("\nProcessing script lines and searching transcripts...")

enhanced_map = []
used_clips = set()  # Track used clips to avoid reuse
consecutive_images = 0  # Track consecutive images

# Map script lines from input
script_lines = []
current_line = 1
for para in script_text.split('\n\n'):
    para = para.strip()
    if para and not para.startswith('→'):
        script_lines.append({
            'line_number': current_line,
            'line_text': para
        })
        current_line += 1

print(f"Extracted {len(script_lines)} script lines")

# Process each line
for line_entry in existing_map:
    line_num = line_entry['line_number']
    line_text = line_entry['line_text']
    existing_assets = line_entry.get('assets', [])

    # Extract keywords from this line
    keywords = extract_keywords_from_line(line_text)

    # Initialize new assets list
    new_assets = []

    # Strategy 1: Use existing assets as base, but enhance them with transcript data
    for existing_asset in existing_assets:
        if existing_asset.get('type') == 'broll':
            # Extract video ID from URL
            url_match = re.search(r'v=([a-zA-Z0-9_-]+)', existing_asset.get('url', ''))
            if url_match:
                video_id = url_match.group(1)

                # Try to find matching transcript entries for this video
                matches = find_transcript_matches(line_text, video_id, keywords)

                if matches:
                    match = matches[0]  # Use best match
                    # Create enhanced asset with transcript data
                    enhanced_asset = {
                        'type': 'broll',
                        'url': existing_asset.get('url'),
                        'start_time': match.get('start'),
                        'end_time': match.get('end'),
                        'video_title': existing_asset.get('video_title', 'Unknown'),
                        'channel': existing_asset.get('channel', 'Unknown'),
                        'description': existing_asset.get('description', 'Deal discussion'),
                        'transcript_excerpt': match.get('text'),
                        'match_reasoning': f"Matched keyword '{match.get('keywords')}' from script line about {keywords[0] if keywords else 'topic'}",
                        'relevance_score': existing_asset.get('relevance_score', 8),
                        'era_appropriate': existing_asset.get('era_appropriate', True),
                        'with_audio': existing_asset.get('with_audio', False),
                        'source_type': existing_asset.get('source_type', 'interview')
                    }
                    new_assets.append(enhanced_asset)
                    consecutive_images = 0
                else:
                    # No transcript match, but keep the asset with improved data
                    new_assets.append(existing_asset)
                    consecutive_images = 0

        elif existing_asset.get('type') == 'image':
            new_assets.append(existing_asset)
            consecutive_images += 1

    # If we don't have enough assets, try to add more images
    if len(new_assets) < 2 and consecutive_images < 3:
        # Find relevant images based on keywords
        for image in images:
            image_desc = image.get('description', '').lower()
            image_entity = image.get('entity_name', '').lower()

            # Check if this image matches the keywords
            if any(kw.lower() in image_desc or kw.lower() in image_entity for kw in keywords):
                # Check if this image is already in assets
                already_used = any(a.get('type') == 'image' and
                                   a.get('pic_number') == image.get('pic_number')
                                   for a in new_assets)

                if not already_used:
                    new_assets.append({
                        'type': 'image',
                        'pic_number': images.index(image),
                        'description': image.get('description'),
                        'match_reasoning': f"Image of {image.get('entity_name')} related to script content"
                    })
                    consecutive_images += 1
                    break

    enhanced_map.append({
        'line_number': line_num,
        'line_text': line_text,
        'assets': new_assets if new_assets else existing_assets,
        'has_gap': len(new_assets) == 0 or len(existing_assets) == 0
    })

# ============= STATISTICS =============

print("\n=== SUMMARY STATISTICS ===")

total_broll = sum(len([a for a in entry['assets'] if a['type'] == 'broll']) for entry in enhanced_map)
total_images = sum(len([a for a in entry['assets'] if a['type'] == 'image']) for entry in enhanced_map)
total_assets = total_broll + total_images

unique_video_ids = set()
for entry in enhanced_map:
    for asset in entry['assets']:
        if asset['type'] == 'broll':
            url_match = re.search(r'v=([a-zA-Z0-9_-]+)', asset.get('url', ''))
            if url_match:
                unique_video_ids.add(url_match.group(1))

unique_images = set()
for entry in enhanced_map:
    for asset in entry['assets']:
        if asset['type'] == 'image':
            unique_images.add(asset.get('pic_number'))

audio_clips = sum(len([a for a in entry['assets']
                       if a.get('type') == 'broll' and a.get('with_audio', False)])
                 for entry in enhanced_map)

gaps = sum(1 for entry in enhanced_map if entry.get('has_gap'))

print(f"Total script lines: {len(enhanced_map)}")
print(f"Total B-roll clips: {total_broll}")
print(f"Unique B-roll sources: {len(unique_video_ids)}")
print(f"Total images: {total_images}")
print(f"Unique image assets: {len(unique_images)}")
print(f"Total assets deployed: {total_assets}")
print(f"Audio clips with narration: {audio_clips}")
print(f"Lines with gaps: {gaps}")
print(f"\nTarget metrics:")
print(f"  B-roll sources: 75-90 (current: {len(unique_video_ids)})")
print(f"  Images: 55-70 (current: {len(unique_images)})")
print(f"  Total assets: ~148 (current: {total_assets})")

# ============= SAVE OUTPUT =============

output_path = '/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json'
print(f"\nSaving to {output_path}...")

with open(output_path, 'w') as f:
    json.dump(enhanced_map, f, indent=2)

print("Done!")
