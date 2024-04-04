import click
from db.models import Article, Section
from peewee import fn
import matplotlib.pyplot as plt
import json
import pandas as pd


@click.group()
def info():
    pass


@info.command()
def anchors():
    articles: list[Article] = Article.select()

    data = []

    cn = 0
    cw = 0

    c = 0

    for article in articles:
        sections: list[Section] = Section.select().where(Section.link == article)

        for s in sections:
            c += 1
            if len(s.generated_anchors) == 0:
                cn += 1
            elif s.generated_anchors[0].lower() != s.anchor.lower():
                cw += 1
                print(f"Anchor not matched: {s.anchor} --- {s.generated_anchors[0]}")

            data.append(
                [
                    s.article.title,
                    s.link.title,
                    s.anchor,
                    s.generated_anchors[0] if s.generated_anchors else None,
                ]
            )

    df = pd.DataFrame(
        data, columns=["From article", "To article", "Anchor", "Generated Anchor"]
    )

    open("anchors.txt", "w+").write(df.to_markdown())

    # json.dump(data, open("anchors.json", "w+"), indent=2)

    print(f"No links {cn}, wrong links {cw}, out of {c}")

    print("Saved anchors to anchors.txt")


@info.command()
def links():

    query = (
        Section.select(Section.link, fn.Count(Section.link).alias("count"))
        .group_by(Section.link)
        .order_by(fn.Count(Section.link).desc())
    )

    counts = []

    print("How many incoming link each article has:")
    for result in query:
        counts.append(result.count)
        print(f"Value: {result.link}, Count: {result.count}")

    print(f"max: {max(counts)}, min: {min(counts)}")

    plt.hist(
        counts,
        bins=range(min(counts), max(counts) + 2),
        color="blue",
        edgecolor="black",
        alpha=0.7,
        rwidth=0.8,
        align="left",
    )
    plt.xlabel("# of in-links")
    plt.ylabel("# of Articles")
    plt.title("In-link distribution")
    plt.grid(True)

    # Show plot
    plt.show()
