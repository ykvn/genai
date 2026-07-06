import os
from huggingface_hub import snapshot_download

def download_qwen_cpu_model():
    # 🎯 Swapped to the standard instruct model (No AWQ, fully CPU compatible!)
    model_repo = "Qwen/Qwen2.5-1.5B-Instruct"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Save it to a distinct folder so it doesn't mix with your AWQ files
    target_dir = os.path.join(current_dir, "model_weights_cpu")
    
    hf_token = os.getenv("HF_TOKEN")
    
    print(f"🚀 Initiating secure download stream for CPU-compatible model: {model_repo}")
    print(f"📂 Target destination: {target_dir}")
    
    try:
        model_path = snapshot_download(
            repo_id=model_repo,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            ignore_patterns=["*.msgpack", "*.h5"],
            max_workers=1,
            token=hf_token  
        )
        print(f"\n✅ CPU Model files downloaded completely at: {model_path}")
        
    except Exception as e:
        print(f"\n❌ Error downloading model weights: {str(e)}")

if __name__ == "__main__":
    download_qwen_cpu_model()