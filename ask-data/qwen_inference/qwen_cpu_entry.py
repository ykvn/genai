import os
import sys
import subprocess
from pathlib import Path

def resolve_qwen_dir() -> Path:
    """Robustly finds the qwen_inference directory regardless of where CML launches the script."""
    cwd = Path.cwd()
    
    # Generate a list of probable locations for the app folder
    candidates = [
        Path(__file__).parent.resolve() if '__file__' in globals() else cwd,
        cwd / "qwen_inference",
        cwd / "ask-data" / "qwen_inference",
    ]
    
    # Return the first path that actually contains app/main.py
    for c in candidates:
        if (c / "app" / "main.py").exists():
            return c
            
    print(f"❌ Critical Error: Could not locate 'app/main.py'. Are you sure the 'app' folder exists?")
    return cwd

def main() -> None:
    # 1. Use the robust resolver to lock in the correct directory
    qwen_dir = resolve_qwen_dir()
    os.chdir(qwen_dir)
    
    # 2. Enforce the dynamically allocated port
    app_port = int(os.environ.get("CDSW_APP_PORT"))
    
    # 3. Inject PYTHONPATH
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{qwen_dir}:{pythonpath}" if pythonpath else str(qwen_dir)
    
    # 4. Standardized Uvicorn call pointing directly to app/main.py
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
    print(f"📍 Resolved Working Directory: {qwen_dir}")
    
    # Launch Uvicorn safely in its own process
    process = subprocess.Popen(cmd, cwd=str(qwen_dir), env=env)
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Inference Server...")
        process.terminate()

if __name__ == "__main__":
    main()