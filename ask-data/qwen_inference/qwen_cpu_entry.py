import os
import sys
import torch
import subprocess
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. 📦 Standard Dependency Installer
def install_dependencies():
    """Automatically installs packages from requirements.txt on startup"""
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        print("📦 Found requirements.txt. Ensuring all inference dependencies are installed...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ Dependencies up to date.")
    else:
        print("⚠️ Warning: requirements.txt not found in current directory.")

# Run your installer immediately upon boot
install_dependencies()

# 2. 📂 Bulletproof Directory Search for Model Weights
# This scans all potential nested directory locations to locate your downloaded weights
base_cwd = os.getcwd()
candidate_paths = [
    os.path.join(base_cwd, "ask-data", "qwen_inference", "model_weights_cpu"),
    os.path.join(base_cwd, "qwen_inference", "model_weights_cpu"),
    os.path.join(base_cwd, "model_weights_cpu")
]

model_path = None
for path in candidate_paths:
    if os.path.exists(path) and os.path.isdir(path):
        # Double check that the folder isn't empty and contains the model files
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
    device_map="cpu",              # Forces the model to sit entirely in CPU memory
    torch_dtype=torch.float32,     # Standard floating point format for CPU mathematical precision
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
    
    # Extract the system context and user question from your translator's array layout
    for msg in payload.messages:
        if msg.role == "system":
            system_prompt = msg.content
        elif msg.role == "user":
            user_question = msg.content

    # Re-assemble them into Qwen's internal token format
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

if __name__ == "__main__":
    # Fetch the Cloudera-assigned environment port
    app_port = int(os.getenv("CDSW_APP_PORT", 8001))
    print(f"🌐 Starting Aligned CPU Inference Server on http://localhost:{app_port}")
    
    # Bound tightly to localhost to respect your enterprise proxy requirements
    uvicorn.run(app, host="localhost", port=app_port, log_level="info")