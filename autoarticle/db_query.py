from db.models import Article, Collection, Section
from settings.settings import settings
import requests

sections: list[Section] = Section.select().join(Article).where(Article.collection == 1)

for s in sections:
    url = settings.SITE_URL + s.link.slug
    req = requests.get(url)

    if req.status_code == 404:
        print(url, "status 404")

print(f"Checked {sections.count()} links")
