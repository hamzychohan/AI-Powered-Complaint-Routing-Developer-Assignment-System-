import sys
import os
import json
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

from ingestion.pipeline import RAGPipeline
from retrieval.vector import SimpleVectorRetriever
from retrieval.lexical import BM25Retriever
from retrieval.hybrid import HybridRetriever
from embeddings.factory import get_embedding_model

embed = get_embedding_model("mock")
v_ret = SimpleVectorRetriever(embedding_model=embed)
l_ret = BM25Retriever()
retriever = HybridRetriever(vector_retriever=v_ret, lexical_retriever=l_ret)

# Dummy indexing for mock
retriever.index_documents([{"page_content": "test", "metadata": {"source": "Asthma.txt"}}])

pipeline = RAGPipeline(retriever=retriever, generator_model="mock")
result = pipeline.generate("Asthma", k=1)
print(json.dumps(result["retrieved_contexts"], indent=2))
