from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import logging
from backend.db.embedder import Embedder

logger = logging.getLogger(__name__)

class VectorStore(ABC):
    """Abstract interface for Vector Database providers (Chroma, PGVector, etc.)"""
    
    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """Add document texts with metadata and embeddings to a collection."""
        pass

    @abstractmethod
    def similarity_search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        Returns a list of dicts: [{'id': ..., 'document': ..., 'metadata': ..., 'score': ...}]
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Clear or delete a collection."""
        pass


class ChromaVectorStore(VectorStore):
    """Local persistent ChromaDB vector store implementation."""
    
    def __init__(self, persist_dir: str = "./data/chroma_db", embedder: Optional[Embedder] = None):
        # pyrefly: ignore [missing-import]
        import chromadb
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = embedder

    def _get_collection(self, collection_name: str):
        return self.client.get_or_create_collection(name=collection_name)

    def add_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        if not ids or not documents:
            return
            
        if embeddings is None and self.embedder is not None:
            embeddings = self.embedder.embed_documents(documents)
            
        collection = self._get_collection(collection_name)
        
        # Ensure metadatas are plain dicts without None values (Chroma requirement)
        cleaned_metadatas = None
        if metadatas:
            cleaned_metadatas = []
            for meta in metadatas:
                cleaned = {k: v for k, v in meta.items() if v is not None}
                cleaned_metadatas.append(cleaned)
                
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=cleaned_metadatas,
            embeddings=embeddings
        )

    def similarity_search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            logger.warning(f"Collection '{collection_name}' does not exist.")
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata if filter_metadata else None,
            include=["documents", "metadatas", "distances"]
        )
        
        output = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

            for i in range(len(ids)):
                # Convert Chroma distance (cosine distance 0..2) to similarity score 0..1
                dist = distances[i]
                sim_score = max(0.0, 1.0 - (dist / 2.0))
                output.append({
                    "id": ids[i],
                    "document": docs[i],
                    "metadata": metas[i],
                    "score": round(sim_score, 4)
                })
        return output

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"Could not delete collection {collection_name}: {e}")


class PGVectorStore(VectorStore):
    """pgvector on PostgreSQL implementation (stub/adapter for production swap)."""
    
    def __init__(self, connection_string: str, embedder: Optional[Embedder] = None):
        self.connection_string = connection_string
        self.embedder = embedder
        logger.info(f"Initialized PGVectorStore targeting {connection_string}")

    def add_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        logger.info(f"[PGVectorStore] Upserted {len(ids)} documents into table {collection_name}")

    def similarity_search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"[PGVectorStore] Similarity search in {collection_name}")
        return []

    def delete_collection(self, collection_name: str) -> None:
        logger.info(f"[PGVectorStore] Truncated table {collection_name}")
