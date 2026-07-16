import os
import sys
import subprocess
from pathlib import Path
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ⚡ CPU INFERENCE OPTIMIZATION LAYER
torch.set_num_threads(4)
torch.set_num_interop_threads(4)

# 🛠️ Path Alignment Layer
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
os.chdir(script_dir)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 📂 Simplified Weights Directory Resolution
base_cwd = os.getcwd()
candidate_paths = [
    os.path.join(base_cwd, "model_weights_cpu"),
    os.path.join(base_cwd, "ask-data", "qwen_inference", "model_weights_cpu"),
    os.path.join(base_cwd, "qwen_inference", "model_weights_cpu")
]

model_path = next((p for p in candidate_paths if os.path.isdir(p) and "config.json" in os.listdir(p)), None)
if not model_path:
    print(f"❌ Critical Error: Could not locate 'model_weights_cpu' at: {candidate_paths}")
    sys.exit(1)

print(f"📍 Target model weights located at: {model_path}")

# =========================================================================
# 🧠 DEFERRED MODEL LOADING (Prevents double-execution in subprocess)
# =========================================================================
# Set global placeholders so the route can access them later
global_model = None
global_tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global global_model, global_tokenizer
    
    # This block ONLY runs inside the Uvicorn worker process, saving your RAM!
    print("⏳ [Lifespan Event] Loading Qwen weights into system RAM...")
    global_tokenizer = AutoTokenizer.from_pretrained(model_path)
    global_model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="cpu",              
        dtype=torch.float32,           
        low_cpu_mem_usage=True
    )
    print("✅ [Lifespan Event] Model successfully loaded and ready for inference.")
    
    yield  # The server handles requests while yielding here
    
    # Cleanup when Uvicorn shuts down
    print("🧹 [Lifespan Event] Shutting down and clearing RAM...")
    global_model = None
    global_tokenizer = None

# 🚀 Pass the lifespan to the FastAPI app initialization
app = FastAPI(title="Qwen CPU OpenAI-Aligned Inference Engine", lifespan=lifespan)

# --- OPENAI ALIGNMENT SCHEMAS ---
class ChatMessage(BaseModel):
    role: str
    content: str

class OpenAIPayload(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.0

@app.post("/v1/chat/completions")
def generate_sql_on_cpu(payload: OpenAIPayload):
    system_prompt = next((msg.content for msg in payload.messages if msg.role == "system"), "")
    user_question = next((msg.content for msg in payload.messages if msg.role == "user"), "")

    print("\n=== 🚨 INCOMING SYSTEM CONTEXT RECEIVED BY QWEN ===")
    print(system_prompt)
    print("==================================================\n")

    formatted_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
    
    text = global_tokenizer.apply_chat_template(formatted_messages, tokenize=False, add_generation_prompt=True)
    model_inputs = global_tokenizer([text], return_tensors="pt").to("cpu")
    
    with torch.no_grad():
        generated_ids = global_model.generate(
            **model_inputs,
            max_new_tokens=256,
            temperature=0.1,
            do_sample=False
        )
    
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
    response = global_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": response.strip()
            }
        }]
    }

# =========================================================================
# ⚙️ SUBPROCESS EXECUTION ENGINE
# =========================================================================
if __name__ == "__main__":
    # strictly enforces the dynamically allocated port by the CML environment
    app_port = int(os.environ["CDSW_APP_PORT"])
    
    # 🎯 Hardcoded, static path to avoid ASGI import errors.
    # Uvicorn will explicitly look for "app" inside "qwen_cpu_entry.py".
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "qwen_cpu_entry:app",       
        "--host",
        "127.0.0.1",
        "--port",
        str(app_port),
        "--log-level",
        "info"
    ]
    
    print(f"🌐 Starting Aligned CPU Inference Server via subprocess on http://127.0.0.1:{app_port}")
    
    # Launch Uvicorn in a brand new isolated process
    process = subprocess.Popen(cmd, cwd=script_dir, env=os.environ.copy())
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Inference Server...")
        process.terminate()