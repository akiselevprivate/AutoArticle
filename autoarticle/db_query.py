from db.models import Article, Section
import os

articles: list[Article] = Article.select()

l = []

for a in articles:

    print("##", a.title)
    sec: list[Section] = Section.select().where(Section.article == a)

    for s in sec:
        print(s.title)

    print("")
