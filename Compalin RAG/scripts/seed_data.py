import os
import json
import glob
import logging
from backend.config import settings
from backend.db.embedder import BGEEmbedder, DummyEmbedder
from backend.db.vector_store import ChromaVectorStore
from backend.db.audit_db import AuditDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed():
    logger.info("Initializing Embedder...")
    try:
        embedder = BGEEmbedder(model_name=settings.EMBEDDING_MODEL)
    except Exception as e:
        logger.warning(f"Could not load BGEEmbedder ({e}), using DummyEmbedder for seeding.")
        embedder = DummyEmbedder()

    vector_store = ChromaVectorStore(persist_dir=settings.CHROMA_DB_DIR, embedder=embedder)
    
    # 1. Seed Tickets Collection
    sample_tickets_file = "./data/sample_tickets.json"
    if os.path.exists(sample_tickets_file):
        with open(sample_tickets_file, "r") as f:
            tickets_data = json.load(f)
            
        logger.info(f"Seeding {len(tickets_data)} historical tickets into 'tickets' collection...")
        ids = [t["ticket_id"] for t in tickets_data]
        documents = [t["complaint_text"] for t in tickets_data]
        metadatas = [
            {
                "customer": t.get("customer", ""),
                "product_area": t.get("product_area", ""),
                "resolution": t.get("resolution", ""),
                "assigned_developer": t.get("assigned_developer", "")
            }
            for t in tickets_data
        ]
        
        embeddings = embedder.embed_documents(documents)
        vector_store.add_documents(
            collection_name="tickets",
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info("Successfully seeded 'tickets' collection.")

    # 2. Seed Docs Collection
    docs_dir = "./data/docs"
    doc_files = glob.glob(os.path.join(docs_dir, "*.md"))
    
    doc_ids = []
    doc_texts = []
    doc_metadatas = []
    
    logger.info(f"Indexing documentation files from {docs_dir}...")
    for doc_path in doc_files:
        filename = os.path.basename(doc_path)
        with open(doc_path, "r") as f:
            content = f.read()
            
        # Basic chunking by double newlines (paragraphs/sections)
        chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 20]
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{filename}_chunk_{idx}"
            doc_ids.append(chunk_id)
            doc_texts.append(chunk)
            doc_metadatas.append({
                "source": filename,
                "chunk_index": idx
            })
            
    if doc_texts:
        doc_embeddings = embedder.embed_documents(doc_texts)
        vector_store.add_documents(
            collection_name="docs",
            ids=doc_ids,
            documents=doc_texts,
            metadatas=doc_metadatas,
            embeddings=doc_embeddings
        )
        logger.info(f"Successfully indexed {len(doc_texts)} documentation chunks into 'docs' collection.")

    # 3. Initialize Audit Database
    logger.info("Initializing SQLite audit database...")
    audit_db = AuditDB(db_path=settings.SQLITE_DB_PATH)
    logger.info("Audit database ready.")
    logger.info("Database seeding complete!")

if __name__ == "__main__":
    seed()
