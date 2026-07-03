import os
import subprocess
import time
import sys
import urllib.request
import uvicorn

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
    # 1. Self-heal dependencies first!
    install_dependencies()
    
    # 2. Boot up the secure database pipeline
    tunnel_proc = bootstrap_cloudflare_tunnel()
    
    try:
        print("🌐 Launching FastAPI Backend Web Server...")
        
        # 1. Look for the CML environment port, defaulting to 8055
        app_port = int(os.getenv("CDSW_APP_PORT", 8055))
        
        # 2. Hard guard: If the environment forces a conflict port inside the session workbench, override it
        if app_port in [8000, 8090]:
            print(f"⚠️ Port {app_port} is system-reserved. Diverting traffic...")
            app_port = 8055
            
        print(f"📡 Binding server to safe port: {app_port}")
        
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=app_port, 
            log_level="info"
        )
    finally:
        print("🛑 Cleaning up network tunnel resources...")
        tunnel_proc.terminate()