import os
import subprocess
import time
import sys
import urllib.request
import uvicorn
import threading
import asyncio

def install_dependencies():
    """Automatically installs packages from requirements.txt on startup"""
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        print("📦 Found requirements.txt. Ensuring all dependencies are installed...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ Dependencies up to date.")
    else:
        print("⚠️ Warning: requirements.txt not found in current directory.")

def bootstrap_cloudflare_tunnel():
    binary_path = "./cloudflared"
    if not os.path.exists(binary_path):
        print("📥 Cloudflared binary not found. Downloading the Linux x64 engine...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        urllib.request.urlretrieve(url, binary_path)
        os.chmod(binary_path, 0o755)
        print("✅ Cloudflared engine downloaded successfully.")

    print("⏳ Activating secure Cloudflare Zero Trust tunnel...")
    tunnel_command = ["./cloudflared", "access", "tcp", "--hostname", "mysql.ksmd.my.id", "--url", "localhost:3306"]
    process = subprocess.Popen(tunnel_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3)
    print("🚀 Tunnel process established in container background on localhost:3306")
    return process

if __name__ == "__main__":
    # 🛠️ Safe Path Correction Layer
    # Uses __file__ if running as a pure script, or falls back to Cloudera's home directory if inside CML's wrapper
    if '__file__' in globals():
        script_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        cml_default_backend = "/home/cdsw/ask-data/backend"
        script_dir = cml_default_backend if os.path.exists(cml_default_backend) else os.getcwd()
        
    os.chdir(script_dir)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # 1. Self-heal dependencies first!
    install_dependencies()
    
    # 2. Boot up the secure database pipeline
    tunnel_proc = bootstrap_cloudflare_tunnel()
    
    try:
        print("🌐 Launching FastAPI Backend Web Server...")
        app_port = int(os.getenv("CDSW_APP_PORT", 8090))
        print(f"📡 Binding server to Cloudera Assigned Port: {app_port}")
        
        # 🛠️ Dynamic Loop Handler for CML Application Engine
        # Since CML runs applications inside an active IPython event loop wrapper,
        # spin Uvicorn up on a separate execution thread to bypass the conflict.
        try:
            asyncio.get_running_loop()
            print("🔄 Active CML event loop detected. Launching web server on isolated thread...")
            
            server_thread = threading.Thread(
                target=lambda: uvicorn.run("app.main:app", host="0.0.0.0", port=app_port, log_level="info"),
                daemon=True
            )
            server_thread.start()
            
            # Keep the parent container process alive while the web server runs
            print("🚀 Application is live and listening!")
            while server_thread.is_alive():
                time.sleep(1)
                
        except RuntimeError:
            # Fallback if Cloudera changes its runtime engine to a pure terminal context
            uvicorn.run("app.main:app", host="localhost", port=app_port, log_level="info")
            
    finally:
        print("🛑 Cleaning up network tunnel resources...")
        try:
            tunnel_proc.terminate()
        except NameError:
            pass