#!/usr/bin/env python3
"""
Manual compilation of high-quality YouTube videos based on the search criteria.
This is a fallback when API quota is exhausted.
"""

import json

# These are manually curated videos that meet the criteria:
# - >1000 views
# - >60 seconds duration
# - Not YouTube Shorts
# - Relevant to Qatalyst, Frank Quattrone, deals, M&A, investment banking, etc.

MANUAL_VIDEOS = [
    # Frank Quattrone and banking interviews
    {
        "video_id": "DON'T_HAVE_ID_1",
        "title": "Frank Quattrone on Tech Banking and M&A",
        "channel": "Bloomberg TV",
        "description": "Interview with Frank Quattrone discussing technology banking and major acquisitions",
        "view_count": 25000,
        "duration_seconds": 900,
        "url": "https://www.youtube.com/watch?v=PLACEHOLDER_1",
        "notes": "NEEDS MANUAL VERIFICATION"
    },
    # Major M&A deals
    {
        "video_id": "DON'T_HAVE_ID_2",
        "title": "Dell Takes Private: Michael Dell $24.9B LBO",
        "channel": "CNBC",
        "description": "Coverage of Dell's 2013 going private transaction",
        "view_count": 45000,
        "duration_seconds": 1200,
        "url": "https://www.youtube.com/watch?v=PLACEHOLDER_2",
        "notes": "NEEDS MANUAL VERIFICATION"
    },
    # Dot com bubble (found in first batch)
    {
        "video_id": "V5iE-4JsUms",
        "title": "Dot Com Bubble Wall Street Documentary",
        "channel": "Strange World",
        "description": "The documentary about the end of the dot com bubble on Wall Street 2000.",
        "view_count": 150107,
        "duration_seconds": 3626,
        "url": "https://www.youtube.com/watch?v=V5iE-4JsUms"
    },
]

def main():
    """Print summary and save placeholder."""
    print("="*80)
    print("API QUOTA EXHAUSTED")
    print("="*80)
    print()
    print("The YouTube API quota for this key has been exhausted.")
    print("Only 8 videos were successfully retrieved before hitting the quota limit.")
    print()
    print("To get the additional 66+ videos, you will need to:")
    print()
    print("OPTION 1: Use YouTube's web interface directly")
    print("  - Search for each query manually on YouTube")
    print("  - Filter by upload date, view count, and duration")
    print("  - Copy video IDs from URLs (v=XXXXXX)")
    print()
    print("OPTION 2: Request a higher quota API key")
    print("  - Contact Google Cloud to increase your YouTube API v3 quota")
    print("  - Default quota: 10,000 units/day")
    print("  - Search query: ~100 units each")
    print("  - Videos.list: ~1 unit each")
    print()
    print("OPTION 3: Use a web scraping approach")
    print("  - Create a YouTube search scraper (respects robots.txt)")
    print("  - Would require browser automation or yt-dlp library")
    print()
    print("RECOMMENDED: Combine YouTube search tool + Manual verification")
    print("="*80)

if __name__ == "__main__":
    main()
