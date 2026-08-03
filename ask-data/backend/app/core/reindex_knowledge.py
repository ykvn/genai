import os
import sys
from pathlib import Path

from app.core.ingest_knowledge import build_ingest_config, run_auto_ingest


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    env = os.environ.copy()
    config = build_ingest_config(backend_dir=backend_dir, env=env)

    print("🔄 Re-indexing knowledge base...", flush=True)
    print(f"- docs dir: {config['docs_dir']}", flush=True)
    print(f"- Qdrant server URL: {config['qdrant_server_url']} (SSL: {config['qdrant_ssl']})", flush=True)
    print(f"- collection: {config['collection_name']}", flush=True)
    print(f"- embedding model: {config['embedding_model_name']}", flush=True)
    if config.get("cml_token"):
        print("- CML Authentication: Token loaded successfully", flush=True)

    run_auto_ingest(
        docs_dir=config["docs_dir"],
        qdrant_server_url=config["qdrant_server_url"],
        qdrant_ssl=config["qdrant_ssl"],
        collection_name=config["collection_name"],
        embedding_model_name=config["embedding_model_name"],
        cml_token=config["cml_token"],
    )


if __name__ == "__main__":
    main()