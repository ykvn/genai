import os
import sys
import torch
import subprocess
import time
import threading
import asyncio
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer

def install_dependencies():
    """Automatically installs packages from requirements.txt on startup"""
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        print("📦 Found requirements.txt. Ensuring all inference dependencies are installed...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ Dependencies up to date.")
    else:
        print("⚠️ Warning: requirements.txt not found in current directory.")

if __name__ == "__main__":
    # 🛠️ Safe Path Correction Layer (Matching your backend configuration)
    if '__file__' in globals():
        script_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        cml_default_inference = "/home/cdsw/ask-data/qwen_inference"
        script_dir = cml_default_inference if os.path.exists(cml_default_inference) else os.getcwd()
        
    os.chdir(script_dir)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # 1. Self-heal inference dependencies first!
    install_dependencies()

    # 2. Bulletproof Directory Search for Model Weights
    base_cwd = os.getcwd()
    candidate_paths = [
        os.path.join(base_cwd, "model_weights_cpu"),
        os.path.join(base_cwd, "ask-data", "qwen_inference", "model_weights_cpu"),
        os.path.join(base_cwd, "qwen_inference", "model_weights_cpu")
    ]

    model_path = None
    for path in candidate_paths:
        if os.path.exists(path) and os.path.isdir(path):
            if "config.json" in os.listdir(path):
                model_path = path
                break

    if not model_path:
        print("❌ Critical Error: Could not locate 'model_weights_cpu' directory on disk.")
        print(f"Searched target locations: {candidate_paths}")
        sys.exit(1)

    print(f"📍 Successfully located model weights folder at: {model_path}")

    # --- SERVER INITIALIZATION ---

    app = FastAPI(title="Qwen 1.5B CPU OpenAI-Aligned Inference Engine")

    print("⏳ Loading Qwen 1.5B model weights into system RAM...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="cpu",              
        torch_dtype=torch.float32,     
        low_cpu_mem_usage=True
    )
    print("✅ Model successfully mapped to CPU layers.")

    # --- ALIGNMENT SCHEMA MATCHING YOUR TRANSLATOR ---
    class ChatMessage(BaseModel):
        role: str
        content: str

    class OpenAIPayload(BaseModel):
        model: str
        messages: List[ChatMessage]
        temperature: float = 0.0

    @app.post("/v1/chat/completions")
    def generate_sql_on_cpu(payload: OpenAIPayload):
        """Natively unpacks your translator's OpenAI messages payload on CPU threads"""
        system_prompt = ""
        user_question = ""
        
        for msg in payload.messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                user_question = msg.content

        formatted_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        text = tokenizer.apply_chat_template(formatted_messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer([text], return_tensors="pt").to("cpu")
        
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=False
            )
        
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response.strip()
                }
            }]
        }

    # --- EXECUTION ENGINE BOUND TO LOGIC PARADIGM ---
    app_port = int(os.getenv("CDSW_APP_PORT", 8001))
    print(f"🌐 Starting Aligned CPU Inference Server on http://localhost:{app_port}")
    
    try:
        asyncio.get_running_loop()
        print("🔄 Active CML event loop detected. Launching inference server on isolated thread...")
        
        server_thread = threading.Thread(
            target=lambda: uvicorn.run(app, host="localhost", port=app_port, log_level="info"),
            daemon=True
        )
        server_thread.start()
        
        print("🚀 Model Server is live and listening!")
        while server_thread.is_alive():
            time.sleep(1)
            
    except RuntimeError:
        # Fallback if context shifts to standard terminal environments
        uvicorn.run(app, host="localhost", port=app_port, log_level="info")