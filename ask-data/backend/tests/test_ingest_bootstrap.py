import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "app" / "core" / "ingest.py"

spec = importlib.util.spec_from_file_location("ingest_module", MODULE_PATH)
ingest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_module)


def test_build_ingest_config_uses_environment_defaults():
    config = ingest_module.build_ingest_config(
        backend_dir=ROOT,
        env={"CHROMA_PERSIST_DIR": "/tmp/chroma", "CHROMA_COLLECTION": "bank_abc_knowledge"},
    )

    assert config["persist_dir"] == "/tmp/chroma"
    assert config["collection_name"] == "bank_abc_knowledge"
    assert config["docs_dir"].endswith("data/documents")


def test_build_ingest_config_reads_dotenv_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("CHROMA_PERSIST_DIR=/tmp/from-dotenv\nCHROMA_COLLECTION=bank_abc_knowledge\n", encoding="utf-8")

    config = ingest_module.build_ingest_config(backend_dir=tmp_path, env={})

    assert config["persist_dir"] == "/tmp/from-dotenv"
    assert config["collection_name"] == "bank_abc_knowledge"
