from db.models import Article, Section
from generation.image import generate_image
import json

sections: list[Section] = Section.select()

for s in sections:
    s.markdown = None
    s.save()

articles: list[Article] = Article.select()

for a in articles:
    a.is_complete = False
    a.save()
