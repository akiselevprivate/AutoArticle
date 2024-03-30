from db.models import Article
import json


articles: list[Article] = Article.select()

for a in articles:
    a.embedding_complete = False
    a.interlinking_uuids = None

    a.save()
