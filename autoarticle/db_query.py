from db.models import Article, Collection, Section
from settings.settings import settings

for c in Collection.select():
    print(c.id, Article.select().where(Article.collection == c).count())
