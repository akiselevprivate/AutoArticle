from db.models import Article
import json


articles = Article.select().where(Article.is_complete == True)

data = {}
for a in articles:
    sections = []
    for s in json.loads(a.outline_json)["outline"]:
        sections.append(s["title"])
    data[str(a.id)] = {"title": a.title, "sections": sections}


json.dump(data, open("vector.json", "w+"))
