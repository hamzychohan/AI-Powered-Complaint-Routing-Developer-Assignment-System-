import os
import glob
import logging
from typing import List, Dict, Any
from backend.models import DocChunk
from backend.db.embedder import Embedder
from backend.db.vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, embedder: Embedder, vector_store: VectorStore, docs_dir: str = "./data/docs"):
        self.embedder = embedder
        self.vector_store = vector_store
        self.docs_dir = docs_dir

    def retrieve_docs(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: int = 5,
        rerank_top_n: int = 3
    ) -> List[DocChunk]:
        """
        Retrieves top-k documentation chunks from vector store,
        applies a re-ranking step for precision, and returns top rerank_top_n DocChunks.
        """
        raw_results = self.vector_store.similarity_search(
            collection_name="docs",
            query_embedding=query_embedding,
            top_k=top_k
        )

        if not raw_results:
            return []

        doc_chunks: List[DocChunk] = []
        for r in raw_results:
            meta = r.get("metadata", {})
            doc_chunks.append(
                DocChunk(
                    source=meta.get("source", "unknown"),
                    content=r["document"],
                    relevance_score=r["score"]
                )
            )

        # Re-ranking step: hybrid relevance scoring based on query keyword matching + vector similarity score
        reranked_chunks = self._rerank(query_text, doc_chunks)
        return reranked_chunks[:rerank_top_n]

    def _rerank(self, query: str, chunks: List[DocChunk]) -> List[DocChunk]:
        """
        Hybrid re-ranking logic:
        Boosts relevance score based on exact keyword overlap (e.g. error codes, service names, team leads).
        """
        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in chunks:
            text_words = set(chunk.content.lower().split())
            overlap = len(query_words.intersection(text_words))
            overlap_score = overlap / max(len(query_words), 1)
            
            # Combined score: 70% vector similarity + 30% lexical overlap boost
            final_score = (chunk.relevance_score * 0.7) + (overlap_score * 0.3)
            
            scored_chunk = DocChunk(
                source=chunk.source,
                content=chunk.content,
                relevance_score=round(final_score, 4)
            )
            scored_chunks.append(scored_chunk)

        # Sort descending by relevance_score
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_chunks

    def reindex_docs(self) -> int:
        """
        Ingestion/re-indexing pipeline: scans docs folder, re-chunks, re-embeds, and upserts into vector store.
        """
        doc_files = glob.glob(os.path.join(self.docs_dir, "*.md"))
        if not doc_files:
            logger.warning(f"No markdown documents found in {self.docs_dir}")
            return 0

        self.vector_store.delete_collection("docs")

        doc_ids = []
        doc_texts = []
        doc_metadatas = []

        for doc_path in doc_files:
            filename = os.path.basename(doc_path)
            with open(doc_path, "r") as f:
                content = f.read()

            chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 20]
            for idx, chunk in enumerate(chunks):
                doc_ids.append(f"{filename}_chunk_{idx}")
                doc_texts.append(chunk)
                doc_metadatas.append({
                    "source": filename,
                    "chunk_index": idx
                })

        if doc_texts:
            embeddings = self.embedder.embed_documents(doc_texts)
            self.vector_store.add_documents(
                collection_name="docs",
                ids=doc_ids,
                documents=doc_texts,
                metadatas=doc_metadatas,
                embeddings=embeddings
            )

        logger.info(f"Re-indexed {len(doc_texts)} documentation chunks.")
        return len(doc_texts)
