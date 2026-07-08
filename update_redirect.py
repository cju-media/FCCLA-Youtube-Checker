import urllib.request
import re
import json

url = 'https://www.youtube.com/playlist?list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs'

def get_latest_video_id():
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    match = re.search(r'var ytInitialData = ({.*?});</script>', html)
    if match:
        data = json.loads(match.group(1))
        # The playlist items are listed in order, we can assume the first item is the newest
        # because the user mentioned "newest video by publish date" and playlists are usually sorted.
        # But wait, looking at the UI, the first item *is* the newest one ("2 days ago").
        contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        for item in contents:
            if 'lockupViewModel' in item:
                return item['lockupViewModel']['contentId']
            # Fallback for old renderer format
            if 'playlistVideoRenderer' in item:
                return item['playlistVideoRenderer']['videoId']

    # Fallback to simple regex if JSON parsing fails
    match = re.search(r'"videoId":"(.*?)"', html)
    if match:
        return match.group(1)

    return None

def main():
    video_id = get_latest_video_id()
    if not video_id:
        print("Could not find video ID")
        return

    redirect_url = f"https://www.youtube.com/watch?v={video_id}&list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={redirect_url}">
    <title>Redirecting...</title>
</head>
<body>
    <p>If you are not redirected, <a href="{redirect_url}">click here</a>.</p>
</body>
</html>
"""

    with open('index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    main()
