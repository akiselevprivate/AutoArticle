from db.models import Article

articles = Article.select().where(
    Article.is_complete,
    Article.is_published,
)
print(len(list(articles)))
categories_db = articles.select(Article.category).distinct()
print(list(categories_db))
