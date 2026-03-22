#!/usr/bin/env python3
"""
Search YouTube using yt-dlp (doesn't use API quota).
This extracts video information without hitting the YouTube API quota limits.
"""

import json
import sys
import re
from yt_dlp import YoutubeDL

# Existing video IDs to exclude
EXISTING_IDS = {
    "06ChbedZuvA", "073uKAH_Ibs", "0QMgb7p6-SE", "41S8Gd_u5KU",
    "5uj5GILfl_I", "8LYBjpmjB4k", "8uklaIRJYYM", "AeKnw4awmQY",
    "At1hnVKMoMs", "HaQu_XcHYnI", "M0QcqrWSrTc", "aL9YzkZ2lt0",
    "c7-0bCrG7ys", "eAwY9Z3G_bo", "ex3wCwZl2kg", "foDmbiR2kH8",
    "npa-8GIfo8Q", "qAyCWU04mK4"
}

SEARCH_QUERIES = [
    # Frank Quattrone and core subjects
    "Frank Quattrone interview", "Frank Quattrone CNBC",
    "Frank Quattrone trial", "Qatalyst Partners",
    "George Boutros banker", "tech banking deals",

    # Major deals
    "Microsoft LinkedIn acquisition", "Dell take private",
    "Qualtrics SAP deal", "Motorola Google acquisition",
    "HP Autonomy scandal", "3PAR Dell HP bidding war",
    "NXP Qualcomm deal", "YouTube Google acquisition",
    "Pixar Disney deal", "Apple NeXT Jobs",

    # Financial crisis and history
    "financial crisis documentary", "Lehman Brothers 2008",
    "Bear Stearns collapse", "dot com bubble 2000",
    "tech bubble crash", "Netscape IPO",
    "Silicon Valley history",

    # Investment banking and M&A
    "investment banker documentary", "merger acquisition",
    "Goldman Sachs documentary", "Morgan Stanley banking",
    "tech CEO interview", "M&A deals",

    # CEOs and executives
    "Ryan Smith Qualtrics", "Bill McDermott SAP",
    "Meg Whitman HP", "Michael Dell interview",
    "Steve Ballmer Microsoft", "Larry Ellison Oracle",
]

def search_youtube_ytdlp(query, max_results=25):
    """Search YouTube using yt-dlp."""
    videos = []
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'socket_timeout': 30,
        }

        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

            if result and 'entries' in result:
                for entry in result['entries']:
                    video = extract_video_info(entry)
                    if video:
                        videos.append(video)

    except Exception as e:
        print(f"Error searching for '{query}': {str(e)[:100]}", file=sys.stderr)

    return videos

def extract_video_info(entry):
    """Extract relevant video information from yt-dlp output."""
    if not entry or entry.get("id") is None:
        return None

    video_id = entry.get("id")
    title = entry.get("title", "")
    channel = entry.get("channel", "")
    description = entry.get("description", "") or ""
    view_count = entry.get("view_count")
    duration = entry.get("duration")

    # Skip if already in existing set
    if video_id in EXISTING_IDS:
        return None

    # Filter: >1000 views, >60 seconds
    if not view_count or view_count < 1000:
        return None
    if not duration or duration <= 60:
        return None

    return {
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "description": description[:500] if description else "",
        "view_count": view_count,
        "duration_seconds": duration,
        "url": f"https://www.youtube.com/watch?v={video_id}"
    }

def main():
    print(f"Searching YouTube using yt-dlp...", file=sys.stderr)
    print(f"Queries: {len(SEARCH_QUERIES)}", file=sys.stderr)
    print(f"Excluding: {len(EXISTING_IDS)} existing videos\n", file=sys.stderr)

    all_videos = {}  # Use dict to deduplicate by ID
    query_count = 0

    for query in SEARCH_QUERIES:
        query_count += 1
        print(f"[{query_count}/{len(SEARCH_QUERIES)}] {query}", file=sys.stderr)

        try:
            videos = search_youtube_ytdlp(query, max_results=25)

            for video in videos:
                vid_id = video["video_id"]
                if vid_id not in all_videos:
                    all_videos[vid_id] = video
        except Exception as e:
            print(f"  ERROR: {str(e)[:80]}", file=sys.stderr)

        if query_count % 5 == 0:
            print(f"  -> Found {len(all_videos)} unique videos so far", file=sys.stderr)

    # Convert to list and sort by views
    filtered_videos = list(all_videos.values())
    filtered_videos.sort(key=lambda x: x.get("view_count", 0), reverse=True)

    # Save results
    output_path = "/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/new_youtube_results.json"
    with open(output_path, "w") as f:
        json.dump(filtered_videos, f, indent=2)

    # Print summary
    print("\n" + "="*80, file=sys.stderr)
    print(f"Search complete!", file=sys.stderr)
    print(f"Total queries: {len(SEARCH_QUERIES)}", file=sys.stderr)
    print(f"Unique videos found: {len(filtered_videos)}", file=sys.stderr)
    print(f"Saved to: {output_path}", file=sys.stderr)
    print("="*80, file=sys.stderr)

    # Print top videos
    if filtered_videos:
        print(f"\nTop {min(40, len(filtered_videos))} videos by view count:\n", file=sys.stderr)
        for i, video in enumerate(filtered_videos[:40], 1):
            title = video['title'][:70]
            views = video['view_count']
            duration = video['duration_seconds']
            vid_id = video['video_id']
            print(f"{i:2d}. {title}", file=sys.stderr)
            print(f"    ID: {vid_id} | Views: {views:>10,} | Duration: {duration:>5}s", file=sys.stderr)
    else:
        print("No videos found.", file=sys.stderr)

    print(f"\nTotal videos found: {len(filtered_videos)}", file=sys.stderr)

if __name__ == "__main__":
    main()
