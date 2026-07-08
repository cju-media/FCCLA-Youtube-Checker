import json
import subprocess
import os
import re

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs"
OUTPUT_FILE = "data/playlist_streams.json"

def get_recent_playlist_videos():
    print("Fetching recent playlist items with flat-playlist...")
    # Using --playlist-end 20 to only fetch newest items to save time on normal runs.
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--playlist-end", "20",
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
    print(f"Fetching metadata for video using iOS client workaround: {url}")
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

    processed = {}
    fetch_limit = 50
    fetched_count = 0

    # 1. Process items in the "0" backlog first
    zero_backlog = existing_data.get("0", [])
    still_zero = []

    for url in zero_backlog:
        if fetched_count >= fetch_limit:
            still_zero.append(url)
            continue

        metadata = fetch_video_metadata_with_ios_client(url)
        date_str = None
        if metadata:
            date_str = metadata.get('release_date') or metadata.get('upload_date')

        fetched_count += 1

        if date_str:
            if date_str not in processed:
                processed[date_str] = []
            if url not in processed[date_str]:
                processed[date_str].append(url)
        else:
            still_zero.append(url)

    # 2. Check for new videos
    recent_videos = get_recent_playlist_videos()

    for video in recent_videos:
        url = video.get('url') or video.get('webpage_url')
        if not url:
            if 'id' in video:
                url = f"https://www.youtube.com/watch?v={video['id']}"
            else:
                continue

        if url in existing_urls:
            # We already track this video somewhere
            continue

        # Completely new video
        title = video.get('title', '')
        date_str = None

        if fetched_count < fetch_limit:
            metadata = fetch_video_metadata_with_ios_client(url)
            if metadata:
                date_str = metadata.get('release_date') or metadata.get('upload_date')
            fetched_count += 1

        if not date_str:
            date_str = extract_date_from_title(title)

        if not date_str:
            # We don't have a date for it, throw it into the backlog
            date_str = "0"

        if date_str not in processed:
            processed[date_str] = []

        if url not in processed[date_str]:
            processed[date_str].append(url)

    # 3. Merge everything back together
    # Add items that were successfully processed out of "0"
    for date_str, urls in existing_data.items():
        if date_str == "0":
            continue
        if date_str not in processed:
            processed[date_str] = urls
        else:
            for url in urls:
                if url not in processed[date_str]:
                    processed[date_str].append(url)

    # Handle the remaining "0" backlog
    # Any new videos that landed in "0" will be in processed["0"]
    if "0" not in processed:
        processed["0"] = []

    for url in still_zero:
        if url not in processed["0"]:
            processed["0"].append(url)

    # If "0" is empty, remove it
    if not processed["0"]:
        del processed["0"]

    return processed

if __name__ == "__main__":
    processed_data = process_videos()

    # Sort the dictionary by date (descending, keeping "0" at the end if it exists)
    sorted_items = sorted([(k, v) for k, v in processed_data.items() if k != "0"], reverse=True)
    sorted_data = dict(sorted_items)
    if "0" in processed_data:
        sorted_data["0"] = processed_data["0"]

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sorted_data, f, indent=2)

    print(f"Successfully updated {OUTPUT_FILE}")
