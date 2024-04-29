from db.models import Article, Collection

articles = Article.select()

titles = "\n".join([a.title for a in articles])

open("titles.txt", "w+").write(titles)
