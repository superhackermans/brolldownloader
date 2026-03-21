"""YouTube Data API v3 search + youtube-transcript-api for transcripts."""
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from config import YOUTUBE_API_KEY

_youtube = None


def _get_youtube():
    global _youtube
    if _youtube is None:
        _youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    return _youtube


def search_youtube(query: str, max_results: int = 5) -> list[dict]:
    """Search YouTube and return video metadata."""
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
            results.append({
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description'],
            })
        return results
    except Exception as e:
        print(f"  YouTube search error for '{query}': {e}")
        return []


def get_transcript(video_id: str) -> list[dict]:
    """Get transcript for a YouTube video."""
    try:
        entries = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return entries
    except Exception:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_generated_transcript(['en'])
            return transcript.fetch()
        except Exception:
            return []
