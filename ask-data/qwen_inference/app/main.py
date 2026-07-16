import os
import sys
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ⚡ CPU INFERENCE OPTIMIZATION LAYER
torch.set_num_threads(4)
torch.set_num_interop_threads(4)

# 📂 Simplified Weights Directory Resolution
base_cwd = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else base_cwd
parent_dir = os.path.dirname(script_dir) # Looks up one level from app/

candidate_paths = [
    os.path.join(base_cwd, "model_weights_cpu"),
    os.path.join(base_cwd, "ask-data", "qwen_inference", "model_weights_cpu"),
    os.path.join(base_cwd, "qwen_inference", "model_weights_cpu"),
    os.path.join(parent_dir, "model_weights_cpu") # Resolves when executed via app.main:app
]

model_path = next((p for p in candidate_paths if os.path.isdir(p) and "config.json" in os.listdir(p)), None)
if not model_path:
    print(f"❌ Critical Error: Could not locate 'model_weights_cpu' at: {candidate_paths}")
    sys.exit(1)

print(f"📍 Target model weights located at: {model_path}")

global_model = None
global_tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global global_model, global_tokenizer
    print("⏳ [Lifespan Event] Loading Qwen weights into system RAM...")
    global_tokenizer = AutoTokenizer.from_pretrained(model_path)
    global_model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="cpu",              
        dtype=torch.float32,           
        low_cpu_mem_usage=True
    )
    print("✅ [Lifespan Event] Model successfully loaded and ready for inference.")
    yield  
    print("🧹 [Lifespan Event] Shutting down and clearing RAM...")
    global_model = None
    global_tokenizer = None

app = FastAPI(title="Qwen CPU OpenAI-Aligned Inference Engine", lifespan=lifespan)

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
        "choices": [{"message": {"role": "assistant", "content": response.strip()}}]
    }

@app.get("/")
def health_check():
    """Satisfies CML platform health checks to prevent 404 logs."""
    return {"status": "ok", "message": "Qwen Inference Engine is running"}