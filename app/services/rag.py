from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from ..config import settings


client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)

model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "epr_docs"


def search_documents(question: str):

    vector = model.encode(question).tolist()

    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=15
    )

    return [item.payload for item in search_result.points]