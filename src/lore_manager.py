import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from src.models import LoreData

class LoreManager:
    def __init__(self, lore_entries: List[LoreData], collection_name: str = "world_lore"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_lore(lore_entries)

    def _initialize_lore(self, lore_entries: List[LoreData]):
        if not lore_entries:
            return

        # Check if collection is already populated
        if self.collection.count() > 0:
            print("Lore collection already populated. Skipping initialization.")
            return

        documents = [entry.content for entry in lore_entries]
        metadatas = [{"title": entry.title, "tags": entry.tags} for entry in lore_entries]
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

    def get_relevant_lore(self, query: str, n_results: int = 3) -> List[Dict]:
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents', 'metadatas']
        )
        return results['documents']
