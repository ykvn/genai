import os
from huggingface_hub import snapshot_download

def download_qwen_cpu_model():
    # 🎯 Swapped back to the ultra-fast 1.5B instruct model
    model_repo = "Qwen/Qwen2.5-1.5B-Instruct"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Saved to a dedicated 1.5B folder to keep your disk completely organized
    target_dir = os.path.join(current_dir, "model_weights_cpu")
    
    hf_token = os.getenv("HF_TOKEN")
    
    print(f"🚀 Initiating secure download stream for lightweight CPU model: {model_repo}")
    print(f"📂 Target destination: {target_dir}")
    
    try:
        model_path = snapshot_download(
            repo_id=model_repo,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            ignore_patterns=["*.msgpack", "*.h5"],
            max_workers=2,  # Optimized for 4 vCPU environment
            token=hf_token  
        )
        print(f"\n✅ 1.5B CPU Model files downloaded completely at: {model_path}")
        print("👉 Next step: Update your qwen_cpu_entry.py path parameters to read this new folder!")
        
    except Exception as e:
        print(f"\n❌ Error downloading model weights: {str(e)}")

if __name__ == "__main__":
    download_qwen_cpu_model()