from __future__ import annotations

import os
import sys
import httpx
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from app.tools.config import settings

_client: QdrantClient | None = None
_embedding_model: SentenceTransformer | None = None


def _get_client() -> QdrantClient:
    """Singleton connection routine ensuring a single Qdrant client connection."""
    global _client
    if _client is None:
        qdrant_url = settings.qdrant_server_url
        cml_token = (
            os.getenv("CML_TOKEN") 
            or os.getenv("CDSW_API_KEY") 
            or os.getenv("QDRANT_SERVER_TOKEN") 
            or None
        )
        
        print(f"QdrantClient connecting to: {qdrant_url}")
        
        # 1. Force the exact Authorization header required by CML Ingress Proxies
        custom_headers = {}
        if cml_token:
            custom_headers["Authorization"] = f"Bearer {cml_token}"
            
        # 2. Build a highly resilient HTTP client for CML network environments
        http_client = httpx.Client(
            verify=False,          # Bypass internal CML SSL issues
            timeout=60.0,          # Prevent premature proxy timeouts
            headers=custom_headers # Pass the CML Bearer Token correctly
        )
        
        # 3. Initialize Qdrant using the custom CML-compliant HTTP client
        _client = QdrantClient(
            url=qdrant_url, 
            check_compatibility=False,
            httpx_client=http_client
        )
    return _client


def _get_embedding_model() -> SentenceTransformer:
    """Initializes local embedding weights matching your verified configuration layer."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.qdrant_model)
    return _embedding_model


def search_documents(query: str, collection_name: str, top_k: int = 5) -> list[dict]:
    """
    Queries local persistent vector stores and normalizes output arrays 
    into standardized dictionary formats with calculated similarity metrics.
    """
    client = _get_client()
    embedder = _get_embedding_model()
    
    try:
        query_vector = embedder.encode(query).tolist()

        # Modern Qdrant API: query_points replaces search
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )

        results = response.points

        output = []
        for point in results:
            payload = point.payload or {}
            score = round(float(point.score), 4) if point.score is not None else None
            
            source_file = payload.get("source_file", payload.get("title", "Unknown_Document"))
            page_num = payload.get("page", "?")
            doc_text = payload.get("page_content", payload.get("excerpt", ""))
            
            output.append({
                "document_id": str(point.id),
                "title": f"{source_file} (halaman {page_num})" if page_num != "?" else source_file,
                "excerpt": doc_text[:400] if doc_text else "",
                "score": score,
            })
        return output
        
    except Exception as e:
        print(f"⚠️ Vector search operational failure: {str(e)}")
        return [{"error": f"Vector Store Failure: {str(e)}"}]