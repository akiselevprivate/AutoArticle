import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from chromadb.config import Settings

import uuid as uuid_pkg

from settings.settings import settings


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.OPENAI_KEY, model_name=settings.EMBEDDINGS_OPENAI_MODEL
)

client = chromadb.PersistentClient(
    path="vectors", settings=Settings(anonymized_telemetry=False)
)


collection = client.get_or_create_collection(
    name="main",
    metadata={"hnsw:space": "cosine"},
    embedding_function=openai_ef,
)


def add_linking_embeddings(
    titles: list[str], sections: list[list[str]], article_uuids: list[str]
):
    docs = []
    meta = []
    ids = []
    for title, local_sections, article_uuid in zip(titles, sections, article_uuids):
        for section in local_sections:
            docs.append(f"{title}; {section}")
            meta.append({"title": title, "section": section, "uuid": article_uuid})
            ids.append(str(uuid_pkg.uuid4()))

    collection.add(documents=docs, metadatas=meta, ids=ids)


def get_best_title(title: str, section: str, not_include_titles):
    doc = collection.get(
        where_document={"$contains": f"{title}; {section}"},
        include=["embeddings"],
    )["embeddings"][0]

    q = collection.query(
        query_embeddings=[doc],
        n_results=1,
        where={"title": {"$nin": [title] + not_include_titles}},
    )

    res_title = q["metadatas"][0][0]["title"]
    res_uuid = q["metadatas"][0][0]["uuid"]

    return res_title, res_uuid


def get_linking_articles(title: str, sections: list) -> tuple[list[str], list[str]]:
    titles = []
    uuids = []
    for section in sections:
        res_title, res_uuid = get_best_title(title, section, titles)
        titles.append(res_title)
        uuids.append(res_uuid)

    return titles, uuids
