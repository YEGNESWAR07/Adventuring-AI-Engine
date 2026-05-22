import os
import warnings

# Suppress TensorFlow/Keras noise before they load
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'    # ERROR-level only
warnings.filterwarnings('ignore', category=FutureWarning)

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
from src.models import LoreData

class LoreManager:
    def __init__(self, lore_entries: List[LoreData], collection_name: str = "world_lore", db_path: str = "./data/lore_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_lore(lore_entries)

    def _initialize_lore(self, lore_entries: List[LoreData]):
        if not lore_entries:
            return

        documents = [entry.content for entry in lore_entries]
        metadatas = [{"title": entry.title, "tags": ",".join(entry.tags)} for entry in lore_entries]
        ids = [entry.id for entry in lore_entries]

        # Generate embeddings
        embeddings = self.model.encode(documents).tolist()

        self.collection.upsert(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Synchronized lore DB with {len(lore_entries)} entries.")

    def get_relevant_lore(self, query: str, n_results: int = 3) -> List[str]:
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents']
        )
        return results['documents'][0] if results['documents'] else []

    def get_lore_context(self, query: str, n_results: int = 2) -> str:
        relevant_docs = self.get_relevant_lore(query, n_results=n_results)
        if not relevant_docs:
            return ""
        
        context = "Relevant World Lore:\n"
        for doc in relevant_docs:
            context += f"- {doc}\n"
        return context

    def search_lore(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents', 'metadatas']
        )
        output = []
        if results.get('documents') and results.get('metadatas'):
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                output.append({
                    "title": meta.get("title", "Unknown Title"),
                    "content": doc,
                    "tags": meta.get("tags", "").split(",") if meta.get("tags") else []
                })
        return output

