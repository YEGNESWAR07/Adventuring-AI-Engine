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
from typing import List, Dict, Optional
from src.models import LoreData

class LoreManager:
    def __init__(self, lore_entries: List[LoreData], collection_name: str = "world_lore", db_path: str = "./data/lore_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_lore(lore_entries)

    def _initialize_lore(self, lore_entries: List[LoreData]):
        if not lore_entries:
            return

        # Check if collection is already populated
        if self.collection.count() > 0:
            # For simplicity in this demo, we clear and re-initialize if entries change
            # In a real app, you'd check for updates
            print("Lore collection exists. Checking if update needed...")
            # For now, let's just use existing if it's there
            return

        documents = [entry.content for entry in lore_entries]
        metadatas = [{"title": entry.title, "tags": ",".join(entry.tags)} for entry in lore_entries]
        ids = [entry.id for entry in lore_entries]

        # Generate embeddings
        embeddings = self.model.encode(documents).tolist()

        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Initialized lore with {len(lore_entries)} entries.")

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
