from typing import Any
from llama_cpp import Dict, List


PROMPT_TEMPLATES = {
    "default": (
        "You are a DevOps assistant. Use ONLY the provided context to answer user questions. "
        "List sources if relevant.\n"
        "{context_block}\n"
        "---\n"
        "User question: {question}\n"
        "Answer in markdown:"
    ),
    "codellama-7b-instruct": (
        "### System:\nYou are a helpful DevOps AI assistant.\n"
        "### Context:\n{context_block}\n"
        "### User:\n{question}\n"
        "### Assistant (markdown):"
    ),
    # Можно добавить свои шаблоны для deepseek, mistral и т.д.
}

def get_prompt_template(model_name):
    for key in PROMPT_TEMPLATES:
        if key in model_name.lower():
            return PROMPT_TEMPLATES[key]
    return PROMPT_TEMPLATES["default"]

def format_context_block(context_docs: List[Dict[str, Any]], max_length: int = 2048) -> str:
    # Markdown + meta
    blocks = []
    total_length = 0
    for i, doc in enumerate(context_docs):
        block = (
            f"**[{doc['title']}]({doc['url']})**\n"
            f"> {doc['snippet']}\n"
            f"_Score: {doc['score']:.2f}_\n"
        )
        block_len = len(block)
        if total_length + block_len > max_length:
            break
        blocks.append(block)
        total_length += block_len
    return "\n---\n".join(blocks)

def truncate_prompt(prompt: str, tokenizer, max_tokens: int = 2048) -> str:
    tokens = tokenizer.encode(prompt)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
        prompt = tokenizer.decode(tokens)
    return prompt