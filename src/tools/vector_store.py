from typing import List, Optional
import chromadb
from sentence_transformers import SentenceTransformer
import logging
from pathlib import Path

class VectorStoreTool:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Ensure vector store directory exists
        store_path = Path("data/vector_store")
        store_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = SentenceTransformer(model_name)
        # Updated ChromaDB client initialization
        self.client = chromadb.PersistentClient(
            path=str(store_path)
        )
        self.collection = self.client.get_or_create_collection(
            name="reference_docs",
            metadata={"hnsw:space": "cosine"}
        )
    
    def index_documents(self, documents: List[dict]):
        try:
            ids = [str(i) for i in range(len(documents))]
            embeddings = self.embedding_model.encode(
                [doc["content"] for doc in documents]
            )
            self.collection.add(
                embeddings=embeddings,
                documents=[doc["content"] for doc in documents],
                metadatas=[doc["metadata"] for doc in documents],
                ids=ids
            )
            return True
        except Exception as e:
            logging.error(f"Error indexing documents: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """Get count of indexed documents"""
        try:
            return self.collection.count()
        except Exception as e:
            logging.error(f"Error getting document count: {e}")
            return 0

    async def query(self, query: str, k: int = 3) -> List[dict]:
        try:
            query_embedding = self.embedding_model.encode(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            if not results["ids"][0]:  # No results found
                return []
                
            return [
                {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                }
                for i in range(len(results["documents"][0]))
            ]
        except Exception as e:
            logging.error(f"Error querying vector store: {e}")
            return []