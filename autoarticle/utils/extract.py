# from utils.create import save_new_articles

from advertools import sitemap_to_df
import re


def extract_sitemap_titles(sitemap_url: str):
    df = sitemap_to_df(sitemap_url, recursive=False)

    def extract_last_path(url):
        pattern = re.compile(r"/([^/]+)/?$")
        match = pattern.search(url)
        if match:
            return match.group(1)
        else:
            return None

    def clean_url(url):
        return url.replace("-", " ").capitalize()

    df = df["loc"].apply(lambda x: clean_url(extract_last_path(x)))

    titles = df.to_list()

    return titles
