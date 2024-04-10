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


def get_section_data(title: str, section: str, sections_count: int):

    not_include_titles = []
    doc = collection.get(
        where_document={"$contains": f"{title}; {section}"},
        include=["embeddings"],
    )["embeddings"][0]

    distances = []
    uuids = []

    for _ in range(sections_count):
        q = collection.query(
            query_embeddings=[doc],
            n_results=1,
            where={"title": {"$nin": [title] + not_include_titles}},
        )
        not_include_titles.append(q["metadatas"][0][0]["title"])
        distances.append(q["distances"][0][0])
        uuids.append(q["metadatas"][0][0]["uuid"])

    return distances, uuids


def get_linking_articles(
    title: str, sections: list[str]
) -> tuple[list[str], list[str]]:

    data = []

    for idx, section in zip(range(len(sections)), sections):
        distances, uuids = get_section_data(title, section, len(sections))
        for d, u in zip(distances, uuids):
            data.append([idx, u, d])

    data.sort(key=lambda x: x[2], reverse=True)  # sort distances

    unique_sections = []
    unique_uuids = []
    unique_sections_data = []

    for item in data:
        if item[0] not in unique_sections and item[1] not in unique_uuids:
            unique_sections.append(item[0])
            unique_uuids.append(item[1])
            unique_sections_data.append(item)

    unique_sections_data.sort(key=lambda x: x[0])  # sort sections

    uuids = [d[1] for d in unique_sections_data]

    return uuids
