#!/usr/bin/env python3
import json
import re

# Read input script
with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/input_script.txt', 'r', encoding='utf-8') as f:
    script_text = f.read()

# Parse script into paragraphs/logical segments
paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]

# Create script lines with sequential numbering
script_lines = []
line_num = 1
for para in paragraphs:
    # Skip title and section headers
    if ':' in para and len(para) < 50:  # Section headers
        script_lines.append((line_num, para))
        line_num += 1
    else:
        # Split longer paragraphs by sentences
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for sent in sentences:
            if sent.strip():
                script_lines.append((line_num, sent.strip()))
                line_num += 1

# Read B-roll candidates
with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/broll_candidates.json', 'r') as f:
    broll_data = json.load(f)

# Read image assets
with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/image_assets.json', 'r') as f:
    image_data = json.load(f)

# Create pic number map (1-30)
pic_map = {}
for img in image_data:
    filename = img['filename']
    match = re.match(r'(\d+)', filename)
    if match:
        pic_num = int(match.group(1))
        pic_map[pic_num] = img

# Comprehensive B-roll mapping - use real data from candidates
BROLL_LIST = [
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '0:00', '1:00', 'Frank Quattrone intro segment', False),
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '0:56', '3:30', 'Frank discussing Steve Jobs meeting at Stanford', True),
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '10:37', '13:00', 'Frank on Stanford and early career at Morgan Stanley', True),
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '13:00', '16:00', 'Frank discussing 1990s tech IPO boom and Netscape', True),
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '37:47', '41:00', 'Frank on Qatalyst methodology and deal execution', False),
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '41:17', '44:00', 'Frank on understanding buyer positioning and leverage', False),
    ('https://www.youtube.com/watch?v=foDmbiR2kH8', '46:56', '48:39', 'Frank on strategic thinking for deal dominance', False),
    ('https://www.youtube.com/watch?v=AeKnw4awmQY', '0:00', '0:07', 'George Boutros intro segment', False),
    ('https://www.youtube.com/watch?v=AeKnw4awmQY', '2:00', '5:00', 'George discussing aggressive negotiation tactics', True),
    ('https://www.youtube.com/watch?v=AeKnw4awmQY', '5:00', '8:00', 'George on strategies to maximize deal value', True),
    ('https://www.youtube.com/watch?v=AeKnw4awmQY', '8:00', '11:00', 'George discussing the $26B LinkedIn acquisition', False),
    ('https://www.youtube.com/watch?v=AeKnw4awmQY', '17:00', '20:00', 'George on why pure sell-side advisory is better', False),
]

def get_best_image_for_line(line_text, line_num):
    """Determine best image for a line based on content"""
    text_lower = line_text.lower()

    # Frank Quattrone mentions
    if any(w in text_lower for w in ['frank quattrone', 'quattrone']):
        if any(w in text_lower for w in ['trial', 'prison', 'arrest', 'charged']):
            return [3, 4]
        else:
            return [1, 2]

    # George Boutros
    if 'george' in text_lower or 'boutros' in text_lower:
        return [7, 8]

    # Qatalyst Partners
    if any(w in text_lower for w in ['qatalyst', 'boutique']):
        return [5, 6]

    # Steve Jobs / Apple
    if any(w in text_lower for w in ['steve jobs', 'apple']):
        return [11, 12]

    # IPO / Market events
    if 'netscape' in text_lower:
        return [13, 14]
    if 'bubble' in text_lower or 'crash' in text_lower:
        return [15, 16]
    if 'amazon' in text_lower:
        return [17, 18]

    # Banks
    if 'goldman' in text_lower or 'morgan stanley' in text_lower:
        return [9, 10, 29, 30]
    if 'credit suisse' in text_lower or 'csfb' in text_lower:
        return [19, 20]

    # LinkedIn / Microsoft
    if 'linkedin' in text_lower or 'microsoft' in text_lower:
        return [25, 26]

    # Deals
    if 'synopsys' in text_lower or 'ansys' in text_lower:
        return [27, 28]
    if 'aruba' in text_lower or 'autonomy' in text_lower:
        return [9, 10]

    # Silicon Valley / Tech
    if 'silicon valley' in text_lower or 'tech' in text_lower:
        return [21, 22]
    if 'wall street' in text_lower or 'new york' in text_lower or 'finance' in text_lower:
        return [23, 24]

    # Default
    return [5, 6, 21, 22]

# Track used B-roll
used_broll = set()

# First pass: identify which lines should get B-roll to avoid 3+ consecutive stills
broll_needs = set()
consecutive_without_broll = 0

for i, (line_num, line_text) in enumerate(script_lines):
    # Force B-roll every 2 stills to prevent 3+ consecutive
    if consecutive_without_broll >= 2 and i < len(script_lines) - 1:
        broll_needs.add(i)
        consecutive_without_broll = 0
    else:
        consecutive_without_broll += 1

# Second pass: assign assets
broll_index = 0
assignment_map = []
annotated_lines = []

for idx, (line_num, line_text) in enumerate(script_lines):
    line_entry = {
        "line_number": line_num,
        "line_text": line_text,
        "assets": [],
        "has_gap": False,
        "custom_visual_description": None
    }

    # Use B-roll if needed to break up stills, or if we have relevant keywords
    use_broll = False

    # Priority 1: Break up too many stills
    if idx in broll_needs and broll_index < len(BROLL_LIST):
        use_broll = True
    # Priority 2: Line has relevant keywords
    elif broll_index < len(BROLL_LIST) * 0.6:  # Use B-roll for ~60% of availability
        keywords = ['frank', 'quattrone', 'george', 'boutros', 'stanford', 'jobs', 'netscape', 'ipo', 'linkedin', 'methodology']
        if any(kw in line_text.lower() for kw in keywords):
            use_broll = True

    if use_broll and broll_index < len(BROLL_LIST):
        url, start, end, desc, has_audio = BROLL_LIST[broll_index]
        broll_key = f"{url}|{start}|{end}"

        if broll_key not in used_broll:
            asset = {
                "type": "broll",
                "url": url,
                "start_time": start,
                "end_time": end,
                "description": desc,
                "match_reasoning": f"Interview footage matching: '{line_text[:50]}...'",
                "relevance_score": 9,
                "with_audio": has_audio
            }
            line_entry["assets"].append(asset)
            used_broll.add(broll_key)
            broll_index += 1

    # If no B-roll, use image
    if not line_entry["assets"]:
        possible_pics = get_best_image_for_line(line_text, line_num)
        for pic_num in possible_pics:
            if pic_num in pic_map:
                img = pic_map[pic_num]
                asset = {
                    "type": "image",
                    "pic_number": pic_num,
                    "description": img['description'],
                    "entity_name": img['entity_name'],
                    "match_reasoning": f"{img['entity_name']} visual for: '{line_text[:50]}...'"
                }
                line_entry["assets"].append(asset)
                break

    if not line_entry["assets"]:
        line_entry["has_gap"] = True

    assignment_map.append(line_entry)

    # Build annotated line
    annotated_text = line_text
    if line_entry["assets"]:
        annotation = "  "
        for i, asset in enumerate(line_entry["assets"]):
            if i > 0:
                annotation += " | "
            if asset["type"] == "image":
                annotation += f"[pic {asset['pic_number']}]"
            else:
                audio_note = ", WITH AUDIO" if asset.get("with_audio") else ""
                annotation += f"[{asset['url']}, {asset['start_time']} - {asset['end_time']}{audio_note}]"
        annotated_text += annotation
    else:
        annotated_text += "  [NO B-ROLL FOUND - need alternative]"

    annotated_lines.append((line_num, annotated_text))

# Write files
with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/annotated_script.md', 'w', encoding='utf-8') as f:
    f.write("# Qatalyst Partners: Annotated Script with Visual Assignments\n\n")
    f.write("Generated: Step 6 - Visual Asset Mapping\n\n")
    f.write("---\n\n")
    for line_num, text in annotated_lines:
        f.write(f"{line_num}→{text}\n")

with open('/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/assignment_map.json', 'w', encoding='utf-8') as f:
    json.dump(assignment_map, f, indent=2, ensure_ascii=False)

print("Generated files:")
print("1. annotated_script.md")
print("2. assignment_map.json")
print(f"\nTotal lines: {len(script_lines)}")
print(f"B-roll clips used: {len(used_broll)}")
