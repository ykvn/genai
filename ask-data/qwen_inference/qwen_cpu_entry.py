import os
import sys
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import torch
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer

if __name__ == "__main__":
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

    print(f"📍 Using model weights from: {model_path}")

    # --- SERVER INITIALIZATION ---
    app = FastAPI(title="Qwen CPU OpenAI-Aligned Inference Engine")

    print("⏳ Loading model weights into RAM...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="cpu",              
        torch_dtype=torch.float32,     
        low_cpu_mem_usage=True
    )
    print("✅ Model loaded successfully.")

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

    # --- DIRECT EXECUTION ---
    app_port = int(os.getenv("CDSW_APP_PORT"))
    print(f"🌐 Starting Aligned CPU Inference Server on http://localhost:{app_port}")
    uvicorn.run(app, host="localhost", port=app_port, log_level="info")