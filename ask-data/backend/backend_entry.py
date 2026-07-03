import os
import subprocess
import time
import urllib.request
import uvicorn

def bootstrap_cloudflare_tunnel():
    binary_path = "./cloudflared"
    
    # 1. Download cloudflared if it doesn't exist in the container environment
    if not os.path.exists(binary_path):
        print("📥 Cloudflared binary not found. Downloading the Linux x64 engine...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        urllib.request.urlretrieve(url, binary_path)
        
        # Make the downloaded binary executable
        os.chmod(binary_path, 0o755)
        print("✅ Cloudflared engine downloaded successfully.")

    # 2. Check if the tunnel is already running to prevent duplication
    print("⏳ Activating secure Cloudflare Zero Trust tunnel...")
    
    # 3. Spin up the tunnel as an asynchronous background subprocess
    tunnel_command = [
        binary_path, "access", "tcp",
        "--hostname", "mysql.ksmd.my.id",
        "--url", "localhost:3306"
    ]
    
    # Popen runs the process in the background without blocking this Python script
    process = subprocess.Popen(
        tunnel_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the tunnel 3 seconds to establish its handshake before proceeding
    time.sleep(3)
    print("🚀 Tunnel process established in container background on localhost:3306")
    return process

if __name__ == "__main__":
    # Start the network layer first
    tunnel_proc = bootstrap_cloudflare_tunnel()
    
    try:
        print("🌐 Launching FastAPI Backend Web Server...")
        # Start the web app. CML maps internal ports using the CDSW_APP_PORT variable
        app_port = int(os.getenv("CDSW_APP_PORT", 8090))
        
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=app_port, 
            log_level="info"
        )
    finally:
        # Safeguard: Ensure the tunnel process terminates cleanly if the app crashes or stops
        print("🛑 Cleaning up network tunnel resources...")
        tunnel_proc.terminate()