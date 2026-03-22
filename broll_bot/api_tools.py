"""
API tools for the B-Roll Bot. These handle ONLY external API calls and file I/O.
All LLM reasoning is done by the cowork Claude instance directly.

Usage from cowork:
  python3 api_tools.py youtube_search "Frank Quattrone interview"
  python3 api_tools.py youtube_transcript VIDEO_ID
  python3 api_tools.py image_search "Frank Quattrone photo"
  python3 api_tools.py download_image "https://..." "output/pictures/1.png"
  python3 api_tools.py batch_youtube_search queries.json results.json
  python3 api_tools.py batch_image_search queries.json output/pictures/ results.json
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import YOUTUBE_API_KEY, GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID


def youtube_search(query: str, max_results: int = 5) -> list[dict]:
    from googleapiclient.discovery import build
    yt = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    try:
        response = yt.search().list(
            q=query, type='video', part='snippet',
            maxResults=max_results, order='relevance', relevanceLanguage='en'
        ).execute()
        results = []
        for item in response.get('items', []):
            results.append({
                'video_id': item['id']['videoId'],
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description'][:200],
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def youtube_transcript(video_id: str) -> list[dict]:
    """Fetch transcript using yt-dlp with cookies."""
    import subprocess
    import tempfile

    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'www.youtube.com_cookies.txt')

    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = os.path.join(tmpdir, 'sub')
        url = f'https://www.youtube.com/watch?v={video_id}'

        cmd = [
            'yt-dlp',
            '--cookies', cookies_path,
            '--write-auto-sub',
            '--write-sub',
            '--sub-lang', 'en',
            '--skip-download',
            '--sub-format', 'json3',
            '-o', out_template,
            url
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception as e:
            return [{"error": f"yt-dlp failed: {str(e)}"}]

        # Look for the subtitle file (could be .en.json3 or similar)
        sub_file = None
        for f in os.listdir(tmpdir):
            if f.endswith('.json3'):
                sub_file = os.path.join(tmpdir, f)
                break

        if not sub_file:
            return [{"error": "no subtitle file produced by yt-dlp"}]

        try:
            with open(sub_file) as f:
                cap_json = json.load(f)

            entries = []
            for event in cap_json.get('events', []):
                segs = event.get('segs', [])
                if segs:
                    text = ''.join(s.get('utf8', '') for s in segs).strip()
                    if text:
                        start_ms = event.get('tStartMs', 0)
                        dur_ms = event.get('dDurationMs', 0)
                        entries.append({
                            'text': text,
                            'start': start_ms / 1000,
                            'duration': dur_ms / 1000
                        })

            if entries:
                return entries
            return [{"error": "empty captions"}]
        except Exception as e:
            return [{"error": f"parse error: {str(e)}"}]


def image_search(query: str, max_results: int = 5) -> list[dict]:
    from googleapiclient.discovery import build
    cse = build('customsearch', 'v1', developerKey=GOOGLE_CSE_API_KEY)
    try:
        response = cse.cse().list(
            q=query, searchType='image', num=min(max_results, 10),
            cx=GOOGLE_CSE_ID, imgSize='LARGE', safe='active'
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
        return [{"error": str(e)}]


def download_image(url: str, filepath: str) -> dict:
    import requests
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200 and len(response.content) > 5000:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            from PIL import Image
            img = Image.open(filepath)
            w, h = img.size
            return {"success": True, "width": w, "height": h, "path": filepath}
        return {"success": False, "reason": f"status={response.status_code}, size={len(response.content)}"}
    except Exception as e:
        return {"success": False, "reason": str(e)}


def batch_youtube_search(queries_file: str, output_file: str):
    """Run many YouTube searches from a JSON file of queries."""
    with open(queries_file) as f:
        queries = json.load(f)  # [{"entity": "name", "query": "search terms"}, ...]

    all_results = []
    seen_ids = set()
    for item in queries:
        entity = item.get("entity", "")
        query = item["query"]
        results = youtube_search(query, max_results=5)
        for r in results:
            if "error" in r:
                continue
            vid_id = r.get("video_id", "")
            if vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)
            r["entity"] = entity
            r["search_query"] = query
            all_results.append(r)

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"Found {len(all_results)} unique videos from {len(queries)} queries")
    return all_results


def batch_transcripts(videos_file: str, output_file: str):
    """Fetch transcripts for all videos in a JSON file."""
    with open(videos_file) as f:
        videos = json.load(f)

    results = []
    for v in videos:
        vid_id = v.get("video_id", "")
        if not vid_id:
            continue
        entries = youtube_transcript(vid_id)
        if entries and "error" not in entries[0]:
            # Format transcript with timestamps
            text_lines = []
            for e in entries:
                m = int(e['start']) // 60
                s = int(e['start']) % 60
                text_lines.append(f"[{m}:{s:02d}] {e['text']}")
            transcript_text = ' '.join(text_lines)
            if len(transcript_text) > 50000:
                transcript_text = transcript_text[:50000] + " [TRUNCATED]"
            results.append({
                **v,
                "transcript": transcript_text,
                "transcript_entries": entries,
                "has_transcript": True
            })
        else:
            results.append({**v, "transcript": "", "transcript_entries": [], "has_transcript": False})

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    has = sum(1 for r in results if r["has_transcript"])
    print(f"Transcripts: {has}/{len(results)} videos have transcripts")
    return results


def batch_image_search(queries_file: str, pictures_dir: str, output_file: str):
    """Search and download images from a JSON file of queries."""
    os.makedirs(pictures_dir, exist_ok=True)
    with open(queries_file) as f:
        queries = json.load(f)  # [{"entity": "name", "query": "search terms"}, ...]

    # Find next available image number
    existing = [int(f.replace('.png', '')) for f in os.listdir(pictures_dir)
                if f.endswith('.png') and f.replace('.png', '').isdigit()]
    counter = max(existing, default=0) + 1

    assets = []
    for item in queries:
        entity = item.get("entity", "")
        query = item["query"]
        results = image_search(query, max_results=5)

        for r in results:
            if "error" in r:
                continue
            filepath = os.path.join(pictures_dir, f"{counter}.png")
            dl = download_image(r['url'], filepath)
            if dl.get("success"):
                w, h = dl["width"], dl["height"]
                if w >= 1280 and h >= 720:
                    img_type = "photo"
                    url_lower = r['url'].lower()
                    if any(d in url_lower for d in ['wsj.com', 'nytimes.com', 'bloomberg.com', 'ft.com']):
                        img_type = "article_screenshot"
                    elif 'chart' in query.lower() or 'graph' in query.lower():
                        img_type = "chart"

                    assets.append({
                        "filename": f"{counter}.png",
                        "filepath": filepath,
                        "source_url": r['url'],
                        "entity_name": entity,
                        "description": f"{entity} - {query}",
                        "width": w, "height": h,
                        "type": img_type,
                        "search_query": query,
                        "source_title": r.get('title', ''),
                        "source_domain": r.get('source', ''),
                    })
                    counter += 1
                else:
                    os.remove(filepath)

    with open(output_file, 'w') as f:
        json.dump(assets, f, indent=2)
    print(f"Downloaded {len(assets)} images from {len(queries)} queries")
    return assets


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 api_tools.py <command> [args...]")
        print("Commands: youtube_search, youtube_transcript, image_search, download_image,")
        print("          batch_youtube_search, batch_transcripts, batch_image_search")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "youtube_search":
        query = sys.argv[2]
        print(json.dumps(youtube_search(query), indent=2))

    elif cmd == "youtube_transcript":
        vid_id = sys.argv[2]
        entries = youtube_transcript(vid_id)
        # Print formatted transcript
        for e in entries[:10]:
            if "error" in e:
                print(f"Error: {e['error']}")
                break
            m = int(e['start']) // 60
            s = int(e['start']) % 60
            print(f"[{m}:{s:02d}] {e['text']}")
        if len(entries) > 10:
            print(f"... ({len(entries)} total entries)")

    elif cmd == "image_search":
        query = sys.argv[2]
        print(json.dumps(image_search(query), indent=2))

    elif cmd == "download_image":
        url, filepath = sys.argv[2], sys.argv[3]
        print(json.dumps(download_image(url, filepath), indent=2))

    elif cmd == "batch_youtube_search":
        batch_youtube_search(sys.argv[2], sys.argv[3])

    elif cmd == "batch_transcripts":
        batch_transcripts(sys.argv[2], sys.argv[3])

    elif cmd == "batch_image_search":
        batch_image_search(sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
