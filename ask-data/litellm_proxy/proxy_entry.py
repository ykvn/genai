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
        # Installs the proxy core along with standard networking features
        subprocess.check_call([sys.executable, "-m", "pip", "install", "litellm[proxy]"])
        print("✅ LiteLLM gateway utilities verified successfully.")
    except Exception as e:
        print(f"❌ Critical Error: Failed to configure LiteLLM dependencies: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure correct runtime workspace directory context
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    os.chdir(script_dir)
    
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
        "--config", "litellm_config.yaml",
        "--port", str(app_port),
        "--host", "localhost"                   # Locked strictly to localized loopback core interface
    ]
    
    try:
        # Run process synchronously to hold the CML container runtime execution active
        subprocess.run(proxy_command, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Gateway loop execution interrupted. Purging active proxy sockets...")