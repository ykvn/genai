from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

def _find_env_file() -> str:
    """
    Dynamically finds the .env configuration file inside the workspace context.
    Looks in mcp_server/, ask-data/, or the execution working directory.
    """
    candidates = [
        Path(__file__).parents[1] / ".env",   # app/../.env (mcp_server/.env)
        Path(__file__).parents[2] / ".env",   # app/../../.env (ask-data/.env)
        Path(".env"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_find_env_file(), extra="ignore")

    # Cloudera Impala Credentials
    impala_host: str = Field(alias="IMPALA_HOST")
    impala_port: int = Field(default=443, alias="IMPALA_PORT")
    impala_http_path: str = Field(default="cliservice", alias="IMPALA_HTTP_PATH")
    cdp_user: str = Field(alias="CDP_USER")
    cdp_pass: str = Field(alias="CDP_PASS")
    db_name: str = Field(default="cai_sdx_se_indonesia", alias="DB_NAME")

    # ChromaDB & Vector Embedding Storage
    chroma_persist_dir: str = Field(default="./chroma_db", alias="CHROMA_PERSIST_DIR")
    chroma_collection: str = Field(default="bankjatim_docs", alias="CHROMA_COLLECTION")
    embed_model: str = Field(default="nomic-embed-text", alias="EMBED_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

settings = Settings()  # type: ignore[call-arg]