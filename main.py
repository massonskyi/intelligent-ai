import argparse
import json
import sys
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import time
import functools
import sys
import os
print(f"[PYTHON EXECUTABLE] {sys.executable}", flush=True)
print(f"[VIRTUAL ENV] {os.environ.get('VIRTUAL_ENV')}", flush=True)

# Timer decorator
def time_it(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken for {func.__name__}: {end_time - start_time:.2f} seconds", file=sys.stderr)
        return result
    return wrapper

# ---- 1. Настройка устройства ----
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Используемое устройство: {device}", file=sys.stderr)

# ---- 2. Загрузка модели и токенизатора ----
@time_it
def load_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    model = model.to(device)
    return tokenizer, model

# ---- 3. Подготовка входа ----
@time_it
def prepare_input(input_dict):
    if isinstance(input_dict, dict):
        if "instruction" in input_dict and "input" in input_dict:
            formatted_input = f"{input_dict['instruction']}\n\n{input_dict['input']}"
        else:
            formatted_input = json.dumps(input_dict, ensure_ascii=False)
        print(f"Prepared input: {formatted_input[:100]}...", file=sys.stderr)
        return formatted_input
    elif isinstance(input_dict, str):
        return input_dict
    else:
        raise ValueError(f"Unsupported input type: {type(input_dict)}")

# ---- 4. Токенизация ----
@time_it
def tokenize_input(tokenizer, text):
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    print(f"Tokenized input keys: {list(inputs.keys())}, shapes: {[v.shape for v in inputs.values()]}", file=sys.stderr)
    return {key: value.to(device) for key, value in inputs.items()}

# ---- 5. Генерация ----
@time_it
def generate_pipeline(model, tokenizer, inputs):
    outputs = model.generate(**inputs, max_length=512, num_beams=4)
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated_text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-path", default="./codet5p_finetuned")
    args = parser.parse_args()

    try:
        # Загрузка модели
        tokenizer, model = load_model(args.model_path)

        # Чтение input.json
        with open(args.input, "r", encoding="utf-8") as f:
            input_json = json.load(f)

        # Подготовка текста для генерации
        formatted_input = prepare_input(input_json)

        # Токенизация
        inputs = tokenize_input(tokenizer, formatted_input)

        # Генерация pipeline
        generated_pipeline = generate_pipeline(model, tokenizer, inputs)

        # Запись результата
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(generated_pipeline)

        print(json.dumps({"status": "success"}))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"error": str(e), "status": "error"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
