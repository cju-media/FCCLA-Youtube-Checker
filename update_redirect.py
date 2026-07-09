import urllib.request
import re
import json

playlist_url = 'https://www.youtube.com/playlist?list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs'
streams_url = 'https://www.youtube.com/@firstchurchla/streams'

def get_live_or_upcoming_video_id():
    try:
        req = urllib.request.Request(streams_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        match = re.search(r'var ytInitialData = ({.*?});</script>', html)
        if match:
            data = json.loads(match.group(1))
            tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
            for tab in tabs:
                if 'tabRenderer' in tab and tab['tabRenderer'].get('title') == 'Live':
                    items = tab['tabRenderer'].get('content', {}).get('richGridRenderer', {}).get('contents', [])
                    for item in items:
                        if 'richItemRenderer' in item:
                            content_item = item['richItemRenderer'].get('content', {})

                            # Check new lockupViewModel format
                            if 'lockupViewModel' in content_item:
                                lockup = content_item['lockupViewModel']
                                image = lockup.get('contentImage', {}).get('collectionThumbnailViewModel', {}).get('primaryThumbnail', {}).get('thumbnailViewModel', {})
                                if not image:
                                    image = lockup.get('contentImage', {}).get('thumbnailViewModel', {})

                                overlays = image.get('overlays', [])
                                is_upcoming_or_live = False
                                for overlay in overlays:
                                    if 'thumbnailBottomOverlayViewModel' in overlay:
                                        badges = overlay['thumbnailBottomOverlayViewModel'].get('badges', [])
                                        for badge in badges:
                                            text = badge.get('thumbnailBadgeViewModel', {}).get('text', '')
                                            if text in ('Upcoming', 'LIVE'):
                                                is_upcoming_or_live = True
                                                break

                                if is_upcoming_or_live:
                                    return lockup.get('contentId')

                            # Check older videoRenderer format
                            elif 'videoRenderer' in content_item:
                                video_renderer = content_item['videoRenderer']
                                is_upcoming_or_live = False

                                badges = video_renderer.get('badges', [])
                                for badge in badges:
                                    if 'metadataBadgeRenderer' in badge:
                                        label = badge['metadataBadgeRenderer'].get('label', '')
                                        if label in ('LIVE', 'UPCOMING'):
                                            is_upcoming_or_live = True

                                thumbnail_overlays = video_renderer.get('thumbnailOverlays', [])
                                for overlay in thumbnail_overlays:
                                    if 'thumbnailOverlayTimeStatusRenderer' in overlay:
                                        style = overlay['thumbnailOverlayTimeStatusRenderer'].get('style')
                                        if style in ('LIVE', 'UPCOMING'):
                                            is_upcoming_or_live = True

                                if is_upcoming_or_live:
                                    return video_renderer.get('videoId')
    except Exception as e:
        print("Error checking live streams:", e)
    return None


def get_latest_playlist_video_id():
    try:
        req = urllib.request.Request(playlist_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')

        # Try parsing JSON first
        match = re.search(r'var ytInitialData = ({.*?});</script>', html)
        if match:
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

        # Fallback to simple regex if JSON parsing fails
        match = re.search(r'"videoId":"(.*?)"', html)
        if match:
            return match.group(1)

    except Exception as e:
        print("Failed to parse playlist:", e)

    return None

def main():
    redirect_url = None

    # Check for live stream first
    live_video_id = get_live_or_upcoming_video_id()
    if live_video_id:
        print(f"Found live/upcoming video: {live_video_id}")
        redirect_url = f"https://www.youtube.com/watch?v={live_video_id}"
    else:
        # Fall back to playlist
        playlist_video_id = get_latest_playlist_video_id()
        if playlist_video_id:
            print(f"Found playlist video: {playlist_video_id}")
            redirect_url = f"https://www.youtube.com/watch?v={playlist_video_id}&list=PLGtiSp5WvUc_I0M_vvfSdGY9dJ43ZofXs"

    if not redirect_url:
        print("Could not find any video ID")
        return

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={redirect_url}">
    <title>Redirecting...</title>
    <script>
        // Use window.location.href to ensure JavaScript also triggers a redirect
        window.location.href = "{redirect_url}";
        // Attempt to close the window after a short delay (useful on mobile when app opens)
        setTimeout(function() {{
            window.close();
        }}, 2000);
    </script>
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
