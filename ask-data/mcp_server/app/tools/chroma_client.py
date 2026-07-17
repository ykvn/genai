from __future__ import annotations

import sys
import os
from pathlib import Path

# 🩹 ENTERPRISE RUNTIME PATCH 1: Force modern SQLite layers immediately
try:
    import pysqlite3  # type: ignore
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

# 🩹 ENTERPRISE RUNTIME PATCH 2: Guarantee direct sibling resolution for tools
# This injects the 'tools' directory context straight into the execution path
tools_directory = str(Path(__file__).parent.resolve())
if tools_directory not in sys.path:
    sys.path.insert(0, tools_directory)

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# 🔌 Now we can import the config module cleanly as a direct local script resource
import config
settings = config.settings

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    """Singleton connection routine ensuring a single persistent disk handle."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def _embedding_fn() -> SentenceTransformerEmbeddingFunction:
    """Initializes local embedding weights matching your verified configuration layer."""
    return SentenceTransformerEmbeddingFunction(model_name=settings.chroma_model)


def search_documents(query: str, collection_name: str, top_k: int = 5) -> list[dict]:
    """
    Queries local persistent vector stores and normalizes output arrays 
    into standardized dictionary formats with calculated similarity metrics.
    """
    client = _get_client()
    
    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=_embedding_fn(),
        )
        results = collection.query(query_texts=[query], n_results=top_k)

        docs = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        output = []
        for doc, meta, dist in zip(docs, metadatas, distances):
            # Transform distance arrays into clean 0.0 - 1.0 Similarity Scores
            score = round(1 - dist, 4) if dist is not None else None
            
            source_file = meta.get("source_file", meta.get("source", "Unknown_Document"))
            page_num = meta.get("page", "?")
            
            output.append({
                "document_id": source_file,
                "title": f"{source_file} (halaman {page_num})",
                "excerpt": doc[:400] if doc else "",
                "score": score,
            })
        return output
        
    except Exception as e:
        print(f"⚠️ Vector search operational failure: {str(e)}")
        return [{"error": f"Vector Store Failure: {str(e)}"}]