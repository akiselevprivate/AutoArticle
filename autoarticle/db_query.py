# from generation.embeddings import get_linking_articles
# from db.models import Section, Article

# articles: list[Article] = Article.select()

# for a in articles:
#     a.is_complete = False
#     a.save()


from generation.other import generate_addiional_data

title = "Marketing Tips for OnlyFans Models"

open("small.txt", "w+").write(generate_addiional_data(title))
