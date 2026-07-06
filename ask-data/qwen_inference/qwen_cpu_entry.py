import os
import sys
import torch
import subprocess
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. Self-heal basic server dependencies
print("📦 Validating API container dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "transformers", "accelerate"])

app = FastAPI(title="Qwen 1.5B CPU OpenAI-Aligned Inference Engine")

# 2. Resolve local CPU-compatible model paths
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model_weights_cpu")

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
    
    # Extract the system context and user question directly from your translator's array layout
    system_prompt = ""
    user_question = ""
    
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
    
    # Return structured formatting to exactly match your translator's result["choices"][0] reader
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": response.strip()
            }
        }]
    }

if __name__ == "__main__":
    app_port = int(os.getenv("CDSW_APP_PORT", 8001))
    print(f"🌐 Starting Aligned CPU Inference Server on http://localhost:{app_port}")
    
    uvicorn.run(app, host="localhost", port=app_port, log_level="info")