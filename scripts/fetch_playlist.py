import json
import subprocess
import os
import re
from datetime import datetime

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs"
OUTPUT_FILE = "data/playlist_streams.json"

def get_recent_playlist_videos():
    print("Fetching playlist items with flat-playlist...")
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
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

def fetch_video_metadata_with_ios_client(url):
    print(f"Fetching metadata for new video using iOS client workaround: {url}")
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--skip-download",
        "--ignore-no-formats-error",
        "--no-warnings",
        "--extractor-args", "youtube:player_client=ios",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            pass
    return None

def extract_date_from_title(title):
    if not isinstance(title, str):
        return None

    months = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12",
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})', title)
    if match:
        month = months[match.group(1)]
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}{month}{day}"
    return None

def process_videos():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Load existing data
    existing_data = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    existing_urls = set()
    for urls in existing_data.values():
        for u in urls:
            existing_urls.add(u)

    videos = get_recent_playlist_videos()
    processed = {}

    # Process only new videos. If a video is already in the file, we skip it.
    # To not timeout on a huge initial run, we use a fetch_limit.
    # We will try up to 50 videos using the iOS client, then fallback to title parse.
    fetch_limit = 50
    fetched_count = 0

    for video in videos:
        url = video.get('url') or video.get('webpage_url')
        if not url:
            if 'id' in video:
                url = f"https://www.youtube.com/watch?v={video['id']}"
            else:
                continue

        if url in existing_urls:
            continue

        date_str = None
        title = video.get('title', '')

        if fetched_count < fetch_limit:
            metadata = fetch_video_metadata_with_ios_client(url)
            if metadata:
                date_str = metadata.get('release_date') or metadata.get('upload_date')
            fetched_count += 1

        if not date_str:
            # Fallback to parsing title
            date_str = extract_date_from_title(title)

        if not date_str:
            # Final fallback to current date if limit reached or fetch fails
            date_str = datetime.now().strftime("%Y%m%d")

        if date_str not in processed:
            processed[date_str] = []

        if url not in processed[date_str]:
            processed[date_str].append(url)

    # Merge with existing
    for date_str, urls in existing_data.items():
        if date_str not in processed:
            processed[date_str] = urls
        else:
            for url in urls:
                if url not in processed[date_str]:
                    processed[date_str].append(url)

    return processed

if __name__ == "__main__":
    processed_data = process_videos()

    # Sort the dictionary by date (descending)
    sorted_data = dict(sorted(processed_data.items(), reverse=True))

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sorted_data, f, indent=2)

    print(f"Successfully updated {OUTPUT_FILE}")
