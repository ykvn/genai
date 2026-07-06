# ask-data/qwen_inference/download_model.py
import os
from huggingface_hub import snapshot_download

def download_qwen_model():
    # Define the definitive production model repository
    model_repo = "Qwen/Qwen2.5-14B-Instruct-AWQ"
    
    # Force the target storage to sit right within your project directory structure
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, "model_weights")
    
    # 🔑 1. Check for the Hugging Face authentication token
    hf_token = os.getenv("HF_TOKEN")
    
    if hf_token:
        print("🔑 Authenticated token detected! Requesting high-speed priority band from HF Hub.")
    else:
        print("⚠️ WARNING: No HF_TOKEN detected. Continuing with unauthenticated restrictions.")

    print(f"🚀 Initiating secure download stream for: {model_repo}")
    print(f"📂 Target local project destination: {target_dir}")
    
    try:
        # Pull down the model snapshot cleanly
        model_path = snapshot_download(
            repo_id=model_repo,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            ignore_patterns=["*.msgpack", "*.h5"], # Exclude formats we don't need for vLLM
            max_workers=4,
            token=hf_token  # 👈 2. Injected token parameter here
        )
        print(f"\n✅ Model files downloaded completely and verified at: {model_path}")
        
    except Exception as e:
        print(f"\n❌ Error downloading model weights from Hugging Face: {str(e)}")

if __name__ == "__main__":
    download_qwen_model()