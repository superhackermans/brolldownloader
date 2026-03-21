"""YouTube Data API v3 search + yt-dlp for transcripts and metadata."""
import subprocess
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY, COOKIES_PATH, MIN_VIEW_COUNT, MAX_SHORT_DURATION

_youtube = None


def _get_youtube():
    global _youtube
    if _youtube is None:
        _youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    return _youtube


def _get_video_metadata(video_id: str) -> dict | None:
    """Use yt-dlp with cookies to fetch video metadata (duration, view count)."""
    url = f'https://www.youtube.com/watch?v={video_id}'
    cmd = [
        'yt-dlp',
        '--cookies', COOKIES_PATH,
        '--skip-download',
        '--print', '%(duration)s',
        '--print', '%(view_count)s',
        '--no-warnings',
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            duration = int(float(lines[0])) if lines[0] and lines[0] != 'NA' else None
            view_count = int(float(lines[1])) if lines[1] and lines[1] != 'NA' else None
            return {'duration': duration, 'view_count': view_count}
    except Exception:
        pass
    return None


def _is_eligible_video(video_id: str) -> bool:
    """Return False for Shorts (<=60s) or videos under 1000 views."""
    meta = _get_video_metadata(video_id)
    if meta is None:
        return True
    if meta['duration'] is not None and meta['duration'] <= MAX_SHORT_DURATION:
        return False
    if meta['view_count'] is not None and meta['view_count'] < MIN_VIEW_COUNT:
        return False
    return True


def search_youtube(query: str, max_results: int = 5) -> list[dict]:
    """Search YouTube and return video metadata, filtering out Shorts and low-view videos."""
    try:
        response = _get_youtube().search().list(
            q=query,
            type='video',
            part='snippet',
            maxResults=max_results,
            order='relevance',
            relevanceLanguage='en'
        ).execute()

        results = []
        for item in response.get('items', []):
            vid_id = item['id']['videoId']
            if not _is_eligible_video(vid_id):
                continue
            results.append({
                'video_id': vid_id,
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description'],
            })
        return results
    except Exception as e:
        print(f"  YouTube search error for '{query}': {e}")
        return []


def get_transcript(video_id: str) -> list[dict]:
    """Get transcript for a YouTube video using yt-dlp with cookies."""
    import json
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = os.path.join(tmpdir, 'sub')
        url = f'https://www.youtube.com/watch?v={video_id}'
        cmd = [
            'yt-dlp',
            '--cookies', COOKIES_PATH,
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
        except Exception:
            return []

        sub_file = None
        for f in os.listdir(tmpdir):
            if f.endswith('.json3'):
                sub_file = os.path.join(tmpdir, f)
                break

        if not sub_file:
            return []

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
            return entries
        except Exception:
            return []
