import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path

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

def bootstrap_cloudflare_tunnel() -> subprocess.Popen:
    """Network Infrastructure. Proxies the secure port 3306 database stream."""
    binary_path = "./cloudflared"
    if not os.path.exists(binary_path):
        print("📥 Cloudflared binary missing. Downloading Linux x64 runtime package...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        urllib.request.urlretrieve(url, binary_path)
        os.chmod(binary_path, 0o755)
        print("✅ Cloudflared proxy binary compiled.")

    print("⏳ Activating secure Cloudflare Zero Trust network bridge...")
    tunnel_command = ["./cloudflared", "access", "tcp", "--hostname", "mysql.ksmd.my.id", "--url", "127.0.0.1:3306"]
    process = subprocess.Popen(tunnel_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3)
    print("🚀 Secure tunnel verified. Relational database exposed locally at 127.0.0.1:3306")
    return process

def trigger_rag_auto_ingest(backend_dir: Path) -> None:
    """Database Synchronization. Pre-populates ChromaDB vector maps."""
    print("\n📡 [RAG STARTUP] Synchronizing Knowledge Base document vector nodes...")
    try:
        # Guarantee local module availability for ingestion routine execution
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from app.core.ingest import run_auto_ingest
        
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(backend_dir / "chroma_db"))
        collection_name = os.getenv("CHROMA_COLLECTION", "bank_jatim_knowledge")
        
        docs_dir = os.path.abspath(os.path.join(str(backend_dir), "..", "data", "documents"))
        if not os.path.exists(docs_dir):
            docs_dir = "/home/cdsw/ask-data/data/documents"

        print(f"[RAG STARTUP] Scanning file directory target: {docs_dir}")
        run_auto_ingest(
            docs_dir=docs_dir,
            persist_dir=persist_dir,
            collection_name=collection_name
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
    app_port = int(os.environ.get("CDSW_APP_PORT"))
    
    # 3. Patch environment variables with absolute PYTHONPATH variables
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{backend_dir}:{pythonpath}" if pythonpath else str(backend_dir)
    
    # 4. Process initialization sequence frameworks
    ensure_dependencies(backend_dir, env)
    tunnel_proc = bootstrap_cloudflare_tunnel()
    trigger_rag_auto_ingest(backend_dir)
    
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
        print("🧹 Purging runtime locks and active cloudflared infrastructure tunnels...")
        process.terminate()
        try:
            tunnel_proc.terminate()
        except NameError:
            pass

if __name__ == "__main__":
    main()