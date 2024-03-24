from db.models import Article
import json


articles = Article.select()

data = []
for a in articles:
    data.append(a.title)


json.dump(data, open("vector.json", "w+"))
