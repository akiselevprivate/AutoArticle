import json
from itertools import cycle


topics = [
    "make money from Onlyfans",
    "earn money from Webcams",
    "earn money from JustForFans",
    "make money from Fanvue",
    "more money from FanCentro",
    "make money from Fansly",
    "earn money from ManyVids",
    "make money from Patreon",
    "make money from Loyalfans",
    "make money from Ifans",
]

categories = [
    "strategy",
    "marketing",
    "promoting",
    "reddit",
    "agency",
    "sites",
    "followers",
    "subscribers",
    "traffic",
    "profit",
    "instruction",
    "tutorial",
    "top models",
]


topics_extended = cycle(topics)
categories_extended = cycle(categories)

distibute = [[1, 25], [30, 1], [15, 2], [15, 3]]

total_days = sum([i[0] for i in distibute])
total_articles = sum([i[0] * i[1] for i in distibute])

print("total days: ", total_days)
print("total articles: ", total_articles)

collections = []

for days, amount in distibute:
    for _ in range(days):
        day = []
        for _ in range(amount):
            data = {
                "topic": next(topics_extended),
                "categories": [next(categories_extended)],
                "data_req": True,
                "image_req": True,
                "content_type": "BASIC",
                "amount": 1,
            }
            day.append(data)
        collections.append(day)


json.dump({"collections": collections}, open("config.json", "w+"))
