import re

def extract_jenkinsfile_block(text: str) -> str:
    # Находит первый pipeline-блок и возвращает его содержимое
    match = re.search(r"(pipeline\s*{[\s\S]+?})", text)
    if match:
        return match.group(1)
    # Если pipeline { ... } нет, ищем весь groovy-код
    code_match = re.search(r"(?<=```)([\s\S]+?)(?=```)", text)
    if code_match:
        return code_match.group(1).strip()
    # Если ничего не найдено — возвращаем весь текст (fallback)
    return text.strip()
