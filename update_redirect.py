import urllib.request
import re
import json

url = 'https://www.youtube.com/playlist?list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs'

def get_latest_video_id():
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')

    # Try parsing JSON first
    match = re.search(r'var ytInitialData = ({.*?});</script>', html)
    if match:
        try:
            data = json.loads(match.group(1))
            contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
            # New renderer format (lockupViewModel)
            for item in contents:
                if 'lockupViewModel' in item:
                    return item['lockupViewModel']['contentId']

            # Old renderer format
            for item in contents:
                if 'playlistVideoListRenderer' in item:
                    videos = item['playlistVideoListRenderer']['contents']
                    for video in videos:
                        if 'playlistVideoRenderer' in video:
                            return video['playlistVideoRenderer']['videoId']
        except Exception as e:
            print("Failed to parse JSON:", e)

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
