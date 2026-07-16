import os
import sys
import subprocess
from pathlib import Path

def main() -> None:
    # Set up paths
    script_dir = Path(__file__).parent.resolve() if '__file__' in globals() else Path.cwd()
    os.chdir(script_dir)
    
    # strictly enforces the dynamically allocated port by the CML environment
    app_port = int(os.environ.get("CDSW_APP_PORT"))
    
    # Inject PYTHONPATH just like the mcp_entry.py and backend_entry.py scripts
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{script_dir}:{pythonpath}" if pythonpath else str(script_dir)
    
    # 🎯 Standardized Uvicorn call pointing directly to app/main.py
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
    
    print(f"🌐 Starting Aligned CPU Inference Server via subprocess on http://127.0.0.1:{app_port}")
    
    # Launch Uvicorn
    process = subprocess.Popen(cmd, cwd=str(script_dir), env=env)
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Inference Server...")
        process.terminate()

if __name__ == "__main__":
    main()