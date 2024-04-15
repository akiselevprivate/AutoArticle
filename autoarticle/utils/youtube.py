from youtubesearchpython import CustomSearch, VideoSortOrder


def get_video_url(title: str):
    videosSearch = CustomSearch(title, VideoSortOrder.viewCount, limit=1)
    url = videosSearch.result()["result"][0]["link"]
    return url


def video_embed_html(url: str):
    return f'<iframe width="560" height="315" src="{url}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
