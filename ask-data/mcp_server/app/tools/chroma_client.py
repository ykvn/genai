from __future__ import annotations

import sys
import os
import importlib.util
from pathlib import Path

# 🩹 ENTERPRISE RUNTIME PATCH 1: Force modern SQLite layers immediately
try:
    import pysqlite3  # type: ignore
    sys.modules["sqlite3"] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# 🩹 ENTERPRISE RUNTIME PATCH 2: Bulletproof Direct File System Module Loader
# Bypasses package resolution anomalies entirely by parsing the sibling file directly from disk
config_file_path = Path(__file__).parent.resolve() / "config.py"
if not config_file_path.exists():
    print(f"❌ Critical Configuration Error: Sibling script missing at absolute location: {config_file_path}")
    sys.exit(1)

# Dynamically compile and mount the file contents into memory
spec = importlib.util.spec_from_file_location("local_mcp_config", str(config_file_path))
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
settings = config_module.settings

# --- Core Dependencies ---
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

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