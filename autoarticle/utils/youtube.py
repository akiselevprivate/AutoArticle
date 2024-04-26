from youtubesearchpython import CustomSearch, VideoSortOrder
import re


def get_video_url(title: str):
    videosSearch = CustomSearch(title, VideoSortOrder.relevance, limit=1)
    result = videosSearch.result()["result"]
    if len(result) == 0:
        return None
    url = result[0]["link"]
    return url


def extract_video_id(url):
    pattern = r"v=([A-Za-z0-9_-]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None


def video_embed_html(video_id: str):
    return f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
