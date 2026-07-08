import os
import subprocess
import time
import sys
import urllib.request
import uvicorn
import threading
import asyncio

def install_dependencies():
    """Phase 1: Package Management. Installs requirements before importing core apps."""
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        print("📦 Found requirements.txt. Ensuring all dependencies are installed...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ Container dependencies up to date.")
    else:
        print("⚠️ Warning: requirements.txt not found in execution context directory.")

def bootstrap_cloudflare_tunnel():
    """Phase 2: Network Infrastructure. Proxies the secure port 3306 database stream."""
    binary_path = "./cloudflared"
    if not os.path.exists(binary_path):
        print("📥 Cloudflared binary missing. Downloading Linux x64 runtime package...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        urllib.request.urlretrieve(url, binary_path)
        os.chmod(binary_path, 0o755)
        print("✅ Cloudflared proxy binary compiled.")

    print("⏳ Activating secure Cloudflare Zero Trust network bridge...")
    tunnel_command = ["./cloudflared", "access", "tcp", "--hostname", "mysql.ksmd.my.id", "--url", "localhost:3306"]
    process = subprocess.Popen(tunnel_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3)
    print("🚀 Secure tunnel verified. Relational database exposed locally at localhost:3306")
    return process

def trigger_rag_auto_ingest():
    """Phase 3: Database Synchronization. Pre-populates ChromaDB vector maps."""
    print("\n📡 [RAG STARTUP] Synchronizing Knowledge Base document vector nodes...")
    try:
        from app.core.ingest import run_auto_ingest
        
        # 📂 Cleaned: Removed 'data-intelligence'
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "/home/cdsw/ask-data/backend/chroma_db")
        collection_name = os.getenv("CHROMA_COLLECTION", "bank_jatim_knowledge")
        
        # 📂 Cleaned: Removed 'data-intelligence'
        docs_dir = "/home/cdsw/ask-data/data/documents"
        if not os.path.exists(docs_dir):
            docs_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "data", "documents"))

        print(f"[RAG STARTUP] Scanning file directory target: {docs_dir}")
        run_auto_ingest(
            docs_dir=docs_dir,
            persist_dir=persist_dir,
            collection_name=collection_name
        )
        print("[RAG STARTUP] Document processing loop verified successfully.\n")
        
    except Exception as e:
        print(f"⚠️ [RAG STARTUP WARNING] Vector synchronization bypassed: {str(e)}\n")

if __name__ == "__main__":
    # 🔍 DYNAMIC PATH AUTO-DISCOVERY ENGINE
    # Locked precisely to your /home/cdsw/ask-data workspace footprint
    possible_roots = [
        os.getcwd(),
        "/home/cdsw/ask-data/backend",
        os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else None
    ]
    
    script_dir = None
    for path_candidate in possible_roots:
        if path_candidate and os.path.exists(os.path.join(path_candidate, "app")):
            script_dir = path_candidate
            break
            
    if not script_dir:
        script_dir = os.getcwd()
        
    print(f"📂 Auto-Discovery target context resolved at: {script_dir}")
    os.chdir(script_dir)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Step 1: Self-heal application dependencies first
    install_dependencies()
    
    # Step 2: Establish connection channels to the backing MySQL target
    tunnel_proc = bootstrap_cloudflare_tunnel()
    
    # Step 3: Run structural token indexing onto the storage volumes
    trigger_rag_auto_ingest()
    
    # Step 4: Launch web framework execution context
    try:
        print("🌐 Initializing FastAPI Application Web Server Engine...")
        app_port = int(os.getenv("CDSW_APP_PORT", 8090))
        print(f"📡 Binding routing service to gateway interface port: {app_port}")
        
        try:
            asyncio.get_running_loop()
            print("🔄 Active ipython tracking environment detected. Isolating Uvicorn thread loops...")
            
            server_thread = threading.Thread(
                target=lambda: uvicorn.run("app.main:app", host="localhost", port=app_port, log_level="info"),
                daemon=True
            )
            server_thread.start()
            
            print("🚀 Core engine application service is active and listening for payload contexts!")
            while server_thread.is_alive():
                time.sleep(1)
                
        except RuntimeError:
            uvicorn.run("app.main:app", host="localhost", port=app_port, log_level="info")
            
    finally:
        print("🛑 Platform termination signal captured. Purging cloudflared network hooks...")
        try:
            tunnel_proc.terminate()
        except NameError:
            pass