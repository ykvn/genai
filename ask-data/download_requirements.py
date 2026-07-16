import os
import subprocess
import sys

def get_requirements_paths():
    """Locates all isolated requirements files across the microservices."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Map out the exact requirements files based on your project structure
    target_files = [
        os.path.join(base_dir, "backend", "requirements.txt"),
        os.path.join(base_dir, "mcp_server", "requirements.txt"),
        os.path.join(base_dir, "qwen_inference", "requirements.txt")
    ]
    
    # Filter only files that exist
    return [f for f in target_files if os.path.exists(f)]

def pre_download_dependencies():
    """Orchestrates a central pre-download phase into a local shared cache."""
    requirements_files = get_requirements_paths()
    
    if not requirements_files:
        print("❌ No requirements.txt files discovered in subdirectories.")
        sys.exit(1)
        
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pip_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    print("=======================================================================")
    print(f"📦 INITIALIZING CENTRAL PRE-DEPLOYMENT DOWNLOAD LAYER")
    print(f"📂 Target Cache Directory: {cache_dir}")
    print("=======================================================================\n")
    
    for req_file in requirements_files:
        submodule_name = os.path.basename(os.path.dirname(req_file))
        print(f"📥 Pre-fetching assets for submodule: [{submodule_name.upper()}]...")
        
        # Uses pip download to pull wheels/source binaries without installing them yet
        cmd = [
            sys.executable, "-m", "pip", "download",
            "-r", req_file,
            "-d", cache_dir,
            "--disable-pip-version-check"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✅ Successfully cached requirements from {os.path.basename(req_file)}\n")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed downloading dependencies for {submodule_name}:")
            print(f"   ⚠️ Error Details: {e.stderr}")
            sys.exit(1)

    print("=======================================================================")
    print("🎉 All dependencies successfully downloaded and cached locally!")
    print("🚀 Ready for safe, rapid isolated container deployment loops.")
    print("=======================================================================")

if __name__ == "__main__":
    pre_download_dependencies()