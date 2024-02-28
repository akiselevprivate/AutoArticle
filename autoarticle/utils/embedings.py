import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import json
import uuid

from settings.settings import settings


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.OPENAI_KEY, model_name=settings.EMBEDDINGS_OPENAI_MODEL
)

client = chromadb.PersistentClient(path="vectors")


collection = client.get_or_create_collection(
    name="main",
    metadata={"hnsw:space": "cosine"},
    embedding_function=openai_ef,
)


def add_embedings(outline_dict: dict, title: str, uuid: str):
    for key, value in outline_dict.items():
        docs = []
        meta = []
        ids = []
        for s in value["outline"]:
            docs.append(f'{title}; {s['title']}')
            meta.append({"title": title, "section": s})
            ids.append(uuid)

        collection.add(documents=docs, metadatas=meta, ids=ids)


def get_best_titles_uuids(title: str, section: str):
    doc = collection.get(
        where_document={
            "$contains": f"{title}; {section}"
        },
        include=["embeddings"],
    )["embeddings"][0]

    q = collection.query(
        query_embeddings=[doc],
        n_results=50,
        where={"title": {"$nin": [title]}},
    )

    titles = [i["title"] for i in q["metadatas"][0]]
    ids = [i for i in q["ids"][0]]

    exisiting = []
    results = []
    for t, i in zip(titles, ids):
        if t not in exisiting:
            exisiting.append(t)
            results.append([t, i])


    return results
