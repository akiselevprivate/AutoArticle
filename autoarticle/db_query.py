from generation.embeddings import get_linking_articles
from db.models import Section

sections: list[Section] = Section.select().where(
    Section.article == "6e7dab78-a424-4782-94ef-06672b965e1e"
)


res = get_linking_articles(sections[0].article.title, [s.title for s in sections])

print(res)
