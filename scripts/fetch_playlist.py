import json
import subprocess
import os

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs"
OUTPUT_FILE = "playlist_streams.json"

def get_playlist_videos():
    print("Fetching playlist items...")
    # By omitting --playlist-end, we will fetch all detailed info.
    # It might take a bit longer but since it runs in a GitHub Action, it's fine.
    # Using --no-warnings to reduce log spam
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--ignore-errors",
        "--no-warnings",
        # Only fetch metadata
        "--skip-download",
        PLAYLIST_URL
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    videos = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                videos.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return videos

def process_videos(videos):
    processed = {}
    for video in videos:
        # Check for live_status, release_date, upload_date
        # Scheduled live streams often have `live_status: is_upcoming` or similar.
        date_str = video.get('release_date') or video.get('upload_date')

        if not date_str:
            # Fallback if no date is found
            continue

        url = video.get('webpage_url') or video.get('original_url')
        if not url:
            continue

        if date_str not in processed:
            processed[date_str] = []

        # Avoid duplicates
        if url not in processed[date_str]:
            processed[date_str].append(url)

    return processed

if __name__ == "__main__":
    videos = get_playlist_videos()
    processed_data = process_videos(videos)

    # Sort the dictionary by date (descending)
    sorted_data = dict(sorted(processed_data.items(), reverse=True))

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sorted_data, f, indent=2)

    print(f"Successfully processed {len(videos)} videos and saved to {OUTPUT_FILE}")
