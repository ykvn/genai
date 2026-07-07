import os
from huggingface_hub import snapshot_download

def download_qwen_cpu_model():
    # 🎯 Swapped to the 3B instruct model to fit your 4 vCPU / 8GB RAM footprint perfectly!
    model_repo = "Qwen/Qwen2.5-3B-Instruct"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Saved to a dedicated 3B directory to keep your disk environment perfectly sorted
    target_dir = os.path.join(current_dir, "model_weights_cpu_3b")
    
    hf_token = os.getenv("HF_TOKEN")
    
    print(f"🚀 Initiating secure download stream for CPU-optimized model: {model_repo}")
    print(f"📂 Target destination: {target_dir}")
    
    try:
        model_path = snapshot_download(
            repo_id=model_repo,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            ignore_patterns=["*.msgpack", "*.h5"],
            max_workers=2,  # Bumped to 2 to maximize your 4 vCPU download capacity safely
            token=hf_token  
        )
        print(f"\n✅ 3B CPU Model files downloaded completely at: {model_path}")
        print("👉 Next step: Remember to update your qwen_cpu_entry.py path parameter to read this folder!")
        
    except Exception as e:
        print(f"\n❌ Error downloading model weights: {str(e)}")

if __name__ == "__main__":
    download_qwen_cpu_model()