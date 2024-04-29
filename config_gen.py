import json
from copy import copy

categories = [
    "Affiliate Marketing",
    "Ai",
    "Amazon",
    "Ambassadors",
    "Being A Housewife",
    "Below 18",
    "Blogging",
    "Casino",
    "Chatgpt",
    "Crypto",
    "Cryptocurrency",
    "Facebook",
    "For Beginners",
    "For Students",
    "Freelancing",
    "From Home",
    "Gambling",
    "Gaming",
    "In India",
    "Instagram",
    "Online Courses",
    "Onlyfans",
    "Pinterest",
    "Telegram",
    "Tiktok",
    "Trading",
    "Webcams",
    "Without Any Skills",
    "Without Investment",
    "Youtube",
]

conf = json.load(open("config.json"))

rev = copy(categories)
rev.reverse()

for i, z in zip(categories, rev):
    data = {
        "topic": "How to earn money",
        "categories": [i, z],
        "data_req": True,
        "image_req": True,
        "article_type": "informative",
        "tone": "informative",
        "content_type": "BASIC",
        "amount": 2,
    }
    conf["collections"].append([data])

json.dump(conf, open("config.json", "w+"))
