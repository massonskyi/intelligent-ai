import os
from huggingface_hub import login

def setup_hf_auth():
    # Читай токен из переменных окружения или .env (как тебе удобно)
    hf_token = os.environ.get("HUGGINGFACE_TOKEN")
    if hf_token:
        login(token=hf_token)
        print("[INFO] HuggingFace auth: OK")
    else:
        print("[WARN] HuggingFace token not set (HUGGINGFACE_TOKEN). Private models may not load.")

