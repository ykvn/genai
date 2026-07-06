# ask-data/qwen_inference/download_model.py
import os
import time
import requests
from huggingface_hub import list_repo_files, hf_hub_url
from tqdm import tqdm

def download_qwen_model_throttled():
    model_repo = "Qwen/Qwen2.5-14B-Instruct-AWQ"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, "model_weights")
    os.makedirs(target_dir, exist_ok=True)
    
    hf_token = os.getenv("HF_TOKEN")
    headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
    
    print(f"🐢 Throttling Active: Limiting maximum download speed to ~50 MB/s.")
    
    # 1. Fetch the complete list of files inside the repository
    files = list_repo_files(repo_id=model_repo, token=hf_token)
    
    for file_name in files:
        # Skip unnecessary files
        if any(file_name.endswith(ext) for ext in [".msgpack", ".h5"]):
            continue
            
        local_file_path = os.path.join(target_dir, file_name)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        
        # Build the direct download endpoint URL
        url = hf_hub_url(repo_id=model_repo, filename=file_name)
        
        # 2. Stream the file chunk by chunk
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            # Capping speed: Write 5 Megabytes, then sleep 0.1 seconds (= ~50 MB/s Max)
            chunk_size = 5 * 1024 * 1024 
            
            with open(local_file_path, 'wb') as f, tqdm(
                desc=file_name, total=total_size, unit='B', unit_scale=True
            ) as pbar:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        time.sleep(0.1) # 🐌 The brake pedal forcing a 10x slowdown

if __name__ == "__main__":
    download_qwen_model_throttled()