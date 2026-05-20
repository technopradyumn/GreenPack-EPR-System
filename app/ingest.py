from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import Distance, VectorParams, PointStruct
from pypdf import PdfReader

from .config import settings

import os
import uuid

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list:
    """
    Splits text into chunks of chunk_size with overlap.
    """
    text = " ".join(text.split())
    if not text:
        return []
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks

def run_ingest():
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT
    )

    model = SentenceTransformer("all-MiniLM-L6-v2")
    COLLECTION_NAME = "epr_docs"

   
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if exists:
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(collection_name=COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

    points = []
    docs_path = "data/docs"

    if not os.path.exists(docs_path):
        print(f"Error: Documents path {docs_path} does not exist!")
        return

    for file_name in os.listdir(docs_path):
        if not file_name.lower().endswith(".pdf"):
            continue
            
        file_path = os.path.join(docs_path, file_name)
        print(f"Parsing PDF: {file_name}")
        
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            for page_idx in range(total_pages):
                page = reader.pages[page_idx]
                page_text = page.extract_text() or ""
                
                
                chunks = chunk_text(page_text, chunk_size=800, overlap=100)
                
                for chunk_idx, chunk in enumerate(chunks):
                    vector = model.encode(chunk).tolist()
                    
                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=vector,
                            payload={
                                "source": file_name,
                                "page": page_idx + 1,
                                "text": chunk
                            }
                        )
                    )
                    
            print(f"Successfully processed {file_name} ({total_pages} pages)")
        except Exception as e:
            print(f"Error parsing PDF {file_name}: {str(e)}")

    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Successfully inserted {len(points)} document chunks into Qdrant!")
    else:
        print("No documents found or processed.")

if __name__ == "__main__":
    run_ingest()