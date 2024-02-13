from db.models import Article

artices = Article.select()

titles = "\n".join([a.title for a in artices])

print(titles)