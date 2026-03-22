#!/usr/bin/env python3

import json
import sys
from googleapiclient.discovery import build
from datetime import datetime
import time

# API configuration
API_KEY = "AIzaSyDmrh3kCXRRIXm_cM-6X3b8mGBK281Z9ZY"
youtube = build("youtube", "v3", developerKey=API_KEY)

# Existing video IDs to exclude (deduplication)
EXISTING_IDS = {
    "06ChbedZuvA", "073uKAH_Ibs", "0QMgb7p6-SE", "41S8Gd_u5KU",
    "5uj5GILfl_I", "8LYBjpmjB4k", "8uklaIRJYYM", "AeKnw4awmQY",
    "At1hnVKMoMs", "HaQu_XcHYnI", "M0QcqrWSrTc", "aL9YzkZ2lt0",
    "c7-0bCrG7ys", "eAwY9Z3G_bo", "ex3wCwZl2kg", "foDmbiR2kH8",
    "npa-8GIfo8Q", "qAyCWU04mK4"
}

# Comprehensive search queries - optimized for quality
SEARCH_QUERIES = [
    # Frank Quattrone and core subjects
    "Frank Quattrone interview", "Frank Quattrone CNBC",
    "Frank Quattrone trial", "Frank Quattrone prosecution",
    "Qatalyst Partners", "Qatalyst Partners deals",
    "George Boutros investment banker", "George Boutros Qatalyst",

    # Major deals with CNBC focus
    "Microsoft LinkedIn CNBC", "Dell take private CNBC",
    "Qualtrics SAP CNBC", "Motorola Google CNBC",
    "HP Autonomy CNBC", "3PAR HP Dell CNBC",
    "Qualcomm NXP CNBC", "YouTube Google CNBC",
    "Pixar Disney CNBC", "Apple NeXT Jobs CNBC",

    # Financial documentaries and crises
    "2008 financial crisis CNBC", "Lehman Brothers CNBC",
    "Bear Stearns JPMorgan CNBC", "dot com bubble CNBC",
    "tech bubble 2000 CNBC",

    # M&A and investment banking focused
    "tech acquisition documentary", "investment banker profile",
    "merger acquisition interview", "CEOs talk deals",
    "Goldman Sachs investment banking", "Morgan Stanley CNBC",
    "tech CEO interview", "startup acquisition",

    # Broader business and finance
    "CNBC documentary", "business documentary",
    "venture capital", "tech business news",
    "stock market documentary", "Silicon Valley history",
    "IPO documentary", "business news 2000s",

    # Additional specific queries
    "Ryan Smith Qualtrics", "Bill McDermott SAP",
    "Meg Whitman HP", "Michael Dell LBO",
    "Steve Ballmer Microsoft", "Larry Ellison Oracle",
    "Sandy Weill Citigroup", "Jamie Dimon JPMorgan",
]

def get_video_details(video_ids):
    """Batch fetch detailed video information."""
    if not video_ids:
        return {}

    details_map = {}
    try:
        request = youtube.videos().list(
            part="statistics,contentDetails",
            id=",".join(video_ids),
            fields="items(id,statistics/viewCount,contentDetails/duration)"
        )
        response = request.execute()

        for item in response.get("items", []):
            vid_id = item["id"]
            stats = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            view_count = int(stats.get("viewCount", 0))
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = parse_duration(duration_str)

            details_map[vid_id] = {
                "view_count": view_count,
                "duration_seconds": duration_seconds,
            }
    except Exception as e:
        print(f"Error batch fetching videos: {e}", file=sys.stderr)

    return details_map

def parse_duration(duration_str):
    """Convert ISO 8601 duration to seconds."""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    return 0

def search_youtube(query, max_results=15):
    """Search YouTube for videos matching a query."""
    results = []
    try:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            order="relevance",
            relevanceLanguage="en",
            fields="items(id/videoId,snippet(title,description,channelTitle))"
        )
        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"].get("videoId")
            snippet = item.get("snippet", {})

            results.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
            })
    except Exception as e:
        print(f"Error searching for '{query}': {e}", file=sys.stderr)

    return results

def filter_and_deduplicate(all_videos):
    """Filter videos by criteria and remove duplicates."""
    filtered = []
    seen_ids = set(EXISTING_IDS)

    for video in all_videos:
        video_id = video.get("video_id")

        if video_id in seen_ids:
            continue

        view_count = video.get("view_count", 0)
        duration = video.get("duration_seconds", 0)

        # Apply filters: >1000 views, >60 seconds
        if view_count >= 1000 and duration > 60:
            filtered.append(video)
            seen_ids.add(video_id)

    return filtered

def main():
    print(f"Starting YouTube search with {len(SEARCH_QUERIES)} queries...", file=sys.stderr)
    print(f"Excluding {len(EXISTING_IDS)} existing videos", file=sys.stderr)

    all_videos = []
    query_count = 0
    failed_count = 0
    skipped_count = 0

    for query in SEARCH_QUERIES:
        query_count += 1
        print(f"[{query_count}/{len(SEARCH_QUERIES)}] {query}", file=sys.stderr)

        search_results = search_youtube(query, max_results=15)
        video_ids = [r["video_id"] for r in search_results if r["video_id"] not in EXISTING_IDS]

        if not video_ids:
            skipped_count += len(search_results)
            continue

        # Batch fetch details (max 50 per request)
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            details_map = get_video_details(batch_ids)

            for result in search_results:
                vid_id = result.get("video_id")
                if vid_id in details_map:
                    result.update(details_map[vid_id])
                    result["url"] = f"https://www.youtube.com/watch?v={vid_id}"
                    all_videos.append(result)
                elif vid_id not in EXISTING_IDS:
                    failed_count += 1

        time.sleep(0.2)

    # Filter and deduplicate
    filtered_videos = filter_and_deduplicate(all_videos)
    filtered_videos.sort(key=lambda x: x.get("view_count", 0), reverse=True)

    # Save results
    output_path = "/sessions/relaxed-nice-wozniak/mnt/rareliquid-broll-bot/broll_bot/output/new_youtube_results.json"
    with open(output_path, "w") as f:
        json.dump(filtered_videos, f, indent=2)

    # Print summary
    print("\n" + "="*80, file=sys.stderr)
    print(f"Search complete!", file=sys.stderr)
    print(f"Total queries: {len(SEARCH_QUERIES)}", file=sys.stderr)
    print(f"Videos found: {len(all_videos)}", file=sys.stderr)
    print(f"Failed to fetch: {failed_count}", file=sys.stderr)
    print(f"Skipped (existing): {skipped_count}", file=sys.stderr)
    print(f"After filtering (>1000 views, >60s): {len(filtered_videos)}", file=sys.stderr)
    print(f"Saved to: {output_path}", file=sys.stderr)
    print("="*80, file=sys.stderr)

    # Print top 30 videos
    if filtered_videos:
        print(f"\nTop {min(30, len(filtered_videos))} videos by view count:\n", file=sys.stderr)
        for i, video in enumerate(filtered_videos[:30], 1):
            print(f"{i:2d}. {video['title'][:75]}", file=sys.stderr)
            print(f"    ID: {video['video_id']} | Views: {video['view_count']:>10,} | {video['duration_seconds']}s\n", file=sys.stderr)
    else:
        print("No videos found matching criteria.", file=sys.stderr)

    print(f"\nTotal filtered videos to add: {len(filtered_videos)}", file=sys.stderr)

if __name__ == "__main__":
    main()
