import os
import sys
import subprocess
from pathlib import Path


def _resolve_frontend_dir() -> Path:
    """Resolve the frontend directory for CML and local execution."""
    candidates = []

    if "__file__" in globals():
        current_file = Path(__file__).resolve()
        candidates.extend([
            current_file.parent,
            current_file.parent.parent,
        ])

    cwd = Path.cwd()
    candidates.extend([
        cwd,
        cwd / "frontend",
        cwd / "ask-data" / "frontend",
        cwd / "ask-data",
        Path("/home/cdsw/ask-data/frontend"),
        Path("/home/cdsw/frontend"),
        Path("/home/cdsw"),
    ])

    for candidate in candidates:
        candidate_path = candidate.resolve() if hasattr(candidate, "resolve") else Path(candidate)
        if (candidate_path / "frontend_entry.py").exists():
            return candidate_path

    if "__file__" in globals():
        return Path(__file__).resolve().parent
    return cwd


FRONTEND_DIR = _resolve_frontend_dir()
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))


def ensure_dependencies(frontend_dir: Path, env: dict) -> None:
    """Install frontend dependencies if requirements.txt exists."""
    req_file = frontend_dir / "requirements.txt"
    if not req_file.exists():
        print(f"⚠️ No requirements.txt found at {req_file}. Skipping dependency installation.")
        return

    print(f"📦 Validating frontend dependencies from {req_file}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
            check=True,
            env=env,
        )
        print("✅ Frontend dependencies verified successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Critical Error: Failed to configure frontend dependencies: {str(e)}")
        sys.exit(1)


def _coerce_backend_payload(response):
    """Normalize backend responses so empty or non-JSON bodies are surfaced clearly."""
    try:
        return response.json(), None
    except ValueError as exc:
        status_code = getattr(response, "status_code", None)
        text = (getattr(response, "text", "") or "").strip()

        if not text:
            return None, f"Backend returned an empty response body (status {status_code or 'unknown'})."
        if status_code is not None and status_code >= 400:
            return None, f"Backend returned HTTP {status_code}: {text}"
        return None, f"Backend returned unexpected content: {text[:500]}"


def build_ui() -> object:
    import gradio as gr
    import requests

    backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8090/ask")

    def ask_backend(question: str):
        if not question.strip():
            return "Please enter a question."

        try:
            response = requests.post(
                backend_url,
                json={"question": question},
                timeout=120,
            )
            response.raise_for_status()
            payload, error = _coerce_backend_payload(response)
            if error:
                return f"Error contacting backend: {error}"
            if isinstance(payload, dict):
                if payload.get("response"):
                    return payload["response"]
                if payload.get("data"):
                    return payload["data"]
                return str(payload)
            if payload:
                return str(payload)
            return "Backend returned an empty response."
        except requests.RequestException as exc:
            return f"Error contacting backend: {exc}"
        except Exception as exc:
            return f"Error contacting backend: {exc}"

    with gr.Blocks(title="Bank ABC Q&A") as demo:
        gr.Markdown("# Bank ABC Question Assistant")
        gr.Markdown("Ask a question and it will be sent to the backend API.")

        question_box = gr.Textbox(label="Question", lines=3)
        submit_btn = gr.Button("Ask")
        output_box = gr.Textbox(label="Answer", lines=10)

        submit_btn.click(fn=ask_backend, inputs=question_box, outputs=output_box)

    return demo


def main() -> None:
    frontend_dir = _resolve_frontend_dir()
    os.chdir(frontend_dir)

    env = os.environ.copy()
    ensure_dependencies(frontend_dir, env)

    demo = build_ui()
    port = int(os.environ.get("CDSW_APP_PORT"))
    print(f"🌐 Starting Gradio UI on http://127.0.0.1:{port}")
    demo.launch(server_name="127.0.0.1", server_port=port, share=False)


if __name__ == "__main__":
    main()
