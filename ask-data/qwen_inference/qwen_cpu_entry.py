import os
import sys
import subprocess
from pathlib import Path


def ensure_dependencies(target_dir: Path, env: dict) -> None:
    """
    Validates and installs packages from requirements.txt directly 
    into the CML application container runtime environment.
    """
    req_file = target_dir / "requirements.txt"
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


def resolve_qwen_dir() -> Path:
    """Robustly finds the qwen_inference directory regardless of where CML launches the script."""
    cwd = Path.cwd()[cite: 3]
    
    # Generate a list of probable locations for the app folder
    candidates = [
        Path(__file__).parent.resolve() if '__file__' in globals() else cwd,
        cwd / "qwen_inference",
        cwd / "ask-data" / "qwen_inference",
    ][cite: 3]
    
    # Return the first path that actually contains app/main.py
    for c in candidates:
        if (c / "app" / "main.py").exists():
            return c
            
    print(f"❌ Critical Error: Could not locate 'app/main.py'. Are you sure the 'app' folder exists?")[cite: 3]
    return cwd[cite: 3]


def main() -> None:
    # 1. Use the robust resolver to lock in the correct directory
    qwen_dir = resolve_qwen_dir()[cite: 3]
    os.chdir(qwen_dir)[cite: 3]
    
    # 2. Enforce the dynamically allocated port
    app_port = int(os.environ.get("CDSW_APP_PORT", 8100))
    
    # 3. Inject PYTHONPATH
    env = os.environ.copy()[cite: 3]
    pythonpath = env.get("PYTHONPATH", "")[cite: 3]
    env["PYTHONPATH"] = f"{qwen_dir}:{pythonpath}" if pythonpath else str(qwen_dir)[cite: 3]
    
    # 4. Run standard dependency validation routine
    ensure_dependencies(qwen_dir, env)
    
    # 5. Standardized Uvicorn call pointing directly to app/main.py
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
    ][cite: 3]
    
    print(f"🌐 Starting Aligned CPU Inference Server via subprocess on http://127.0.0.1:{app_port}")[cite: 3]
    print(f"📍 Resolved Working Directory: {qwen_dir}")[cite: 3]
    
    # Launch Uvicorn safely in its own process
    process = subprocess.Popen(cmd, cwd=str(qwen_dir), env=env)[cite: 3]
    
    try:
        process.wait()[cite: 3]
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Inference Server...")[cite: 3]
        process.terminate()[cite: 3]


if __name__ == "__main__":
    main()[cite: 3]