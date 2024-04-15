from generation.embeddings import get_linking_articles
from db.models import Section, Article

articles: list[Article] = Article.select()

for a in articles:
    a.is_complete = False
    a.save()
