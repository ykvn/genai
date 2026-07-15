import os
import sys
import subprocess

def ensure_proxy_dependencies():
    """
    Validates and installs the mandatory routing proxy framework package 
    directly into the CML application container runtime environment.
    """
    print("📦 Validating LiteLLM application dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "litellm[proxy]"])
        print("✅ LiteLLM gateway utilities verified successfully.")
    except Exception as e:
        print(f"❌ Critical Error: Failed to configure LiteLLM dependencies: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 🔍 DYNAMIC CONFIGURATION PATH DISCOVERY ENGINE
    # Resolves path issues when running inside interactive CML notebook cells
    base_cwd = os.getcwd()
    candidate_paths = [
        os.path.join(base_cwd, "litellm_config.yaml"),
        os.path.join(base_cwd, "litellm_proxy", "litellm_config.yaml"),
        "/home/cdsw/ask-data/litellm_proxy/litellm_config.yaml"
    ]

    config_path = None
    for path in candidate_paths:
        if os.path.exists(path):
            config_path = os.path.abspath(path)
            break

    if not config_path:
        print("❌ CRITICAL SETUP ERROR: Could not locate 'litellm_config.yaml' on disk.")
        print(f"Searched target locations: {candidate_paths}")
        print("Please verify that the configuration file exists in your workspace directory.")
        sys.exit(1)

    # Automatically synchronize working directory to where the config actually lives
    os.chdir(os.path.dirname(config_path))
    print(f"📍 Successfully located configuration file at: {config_path}")
    
    # 🔒 ENTERPRISE BOUNDARY GUARD: Assert variable configuration before thread generation
    if "QWEN_APP_URL" not in os.environ:
        print("❌ CRITICAL PLATFORM ERROR: 'QWEN_APP_URL' environment variable is missing!")
        print("Please configure this variable in the CML Project Application Dashboard settings.")
        sys.exit(1)
        
    print(f"🔗 Target routing context successfully bound to: {os.environ['QWEN_APP_URL']}")

    # Run auto-healing dependency validation routine
    ensure_proxy_dependencies()
    
    # Enforce your strict CML Application Port and Host routing requirements
    app_port = int(os.getenv("CDSW_APP_PORT", 8100))
    print(f"\n📡 Launching Standalone CML LiteLLM Proxy Gateway service...")
    print(f"🔒 Network Bound: http://localhost:{app_port}")
    
    # Standardized operational startup parameters
    proxy_command = [
        "litellm",
        "--config", config_path,               # 🎯 Pass the absolute, verified path string
        "--port", str(app_port),
        "--host", "localhost"                   # Locked strictly to localized loopback core interface
    ]
    
    try:
        # Run process synchronously to hold the CML container runtime execution active
        subprocess.run(proxy_command, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Gateway loop execution interrupted. Purging active proxy sockets...")