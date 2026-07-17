import os
import sys
import subprocess
from pathlib import Path

from app.core.ingest_knowledge import build_ingest_config, run_auto_ingest

def ensure_dependencies(backend_dir: Path, env: dict) -> None:
    """
    Validates and installs packages from requirements.txt directly 
    into the CML application container runtime environment.
    """
    req_file = backend_dir / "requirements.txt"
    if not req_file.exists():
        print(f"⚠️ No requirements.txt found at {req_file}. Skipping dependency installation.")
        return
        
    print(f"📦 Validating dependencies from {req_file}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
            check=True,
            env=env,
        )
        print("✅ Dependencies verified successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Critical Error: Failed to configure dependencies: {str(e)}")
        sys.exit(1)

def trigger_rag_auto_ingest(backend_dir: Path, env: dict | None = None) -> None:
    """Database Synchronization. Pre-populates ChromaDB vector maps."""
    print("\n📡 [RAG STARTUP] Synchronizing Knowledge Base document vector nodes...")
    try:
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))

        config = build_ingest_config(backend_dir=backend_dir, env=env)
        print(f"[RAG STARTUP] Scanning file directory target: {config['docs_dir']}")
        run_auto_ingest(
            docs_dir=config["docs_dir"],
            persist_dir=config["persist_dir"],
            collection_name=config["collection_name"],
        )
        print("[RAG STARTUP] Document processing loop verified successfully.\n")

    except Exception as e:
        print(f"⚠️ [RAG STARTUP WARNING] Vector synchronization bypassed: {str(e)}\n")

def resolve_backend_dir() -> Path:
    """Robustly finds the backend directory regardless of where CML launches the script."""
    cwd = Path.cwd()
    candidates = [
        Path(__file__).parent.resolve() if '__file__' in globals() else cwd,
        cwd / "backend",
        cwd / "ask-data" / "backend",
        Path("/home/cdsw/ask-data/backend")
    ]
    
    for c in candidates:
        if (c / "app" / "main.py").exists():
            return c
            
    print(f"❌ Critical Error: Could not locate 'app/main.py'. Defaulting context to root.")
    return cwd

def main() -> None:
    # 1. Lock execution environment down to the correct path context
    backend_dir = resolve_backend_dir()
    os.chdir(backend_dir)
    
    # 2. Extract port specifications allocated dynamically by the environment
    app_port = int(os.environ.get("CDSW_APP_PORT", 8090))
    
    # 3. Patch environment variables with absolute PYTHONPATH variables
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{backend_dir}:{pythonpath}" if pythonpath else str(backend_dir)
    
    # 4. Process initialization sequence frameworks
    ensure_dependencies(backend_dir, env)
    trigger_rag_auto_ingest(backend_dir, env=env)
    
    # 5. Build standardized command execution pattern targeting app.main:app
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",       
        "--host",
        "127.0.0.1",
        "--port",
        str(app_port),
        "--log-level",
        "info"
    ]
    
    print(f"🌐 Starting Aligned Production Backend Server via subprocess on http://127.0.0.1:{app_port}")
    print(f"📍 Resolved Working Directory: {backend_dir}")
    
    # Launch Uvicorn safely in its own completely isolated process context
    process = subprocess.Popen(cmd, cwd=str(backend_dir), env=env)
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown process triggered.")
    finally:
        print("🧹 Purging active production server execution sub-processes...")
        process.terminate()

if __name__ == "__main__":
    main()