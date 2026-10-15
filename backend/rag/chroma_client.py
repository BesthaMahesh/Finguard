import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.core.config import settings
from backend.rag.embeddings import FinGuardEmbeddingFunction

_chroma_client = None
_collection = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        persist_dir = settings.CHROMA_PERSIST_DIR
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client

def get_knowledge_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        embedder = FinGuardEmbeddingFunction()
        _collection = client.get_or_create_collection(
            name="finguard_policies_and_typologies",
            embedding_function=embedder,
            metadata={"description": "Financial risk compliance documents, AML/KYC guidelines, and fraud typologies"}
        )
    return _collection
