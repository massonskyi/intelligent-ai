import os, json, random, uuid, hashlib, re, asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Dict, Any, List

#  (помещаем сюда большой список PROJECT_SIGNATURES - без изменений)
from .signatures import PROJECT_SIGNATURES          # чтобы main.py не раздулся

_EXEC = ThreadPoolExecutor(max_workers=2)            # reuse thread-pool


# ───────── helpers ────────────────────────────────────────────────────────────
def _read_file(path: Path, limit: int = 50) -> str:
    try:
        return "".join(path.read_text(encoding="utf-8").splitlines(True)[:limit]).strip()
    except Exception:
        return ""


def _extract_deps(cfg: Path, pattern: str, ptype: str) -> List[str]:
    if not cfg.exists():
        return []
    txt = cfg.read_text(encoding="utf-8", errors="ignore")
    if ptype == "nodejs":
        m = re.search(pattern, txt, re.M)
        if not m:
            return []
        return [seg.split(":")[0].strip().strip('"') for seg in m.group(1).split(",") if seg.strip()]
    if ptype == "java":
        return [f"{g}:{a}" for g, a in re.findall(pattern, txt, re.M)]
    return re.findall(pattern, txt, re.M)


# ───────── публичная функция ─────────────────────────────────────────────────
def analyze_repository(repo_root: str = ".") -> Tuple[Dict[str, Any], str]:
    """
    Обходит папку `repo_root`, собирает JSON-описание проекта **в формате,
    который ждёт ваша модель**, и возвращает кортеж (json_dict, hash).
    """
    root = Path(repo_root).resolve()
    files = [str(p) for p in root.rglob("*") if p.is_file()]
    docker = any(p.lower().endswith("dockerfile") for p in files)

    # определяем тип проекта
    sig = next((s for s in PROJECT_SIGNATURES
                if any(any(k in f.lower() for f in files) for k in s["signature_files"])), None)
    if not sig:
        raise RuntimeError("Cannot detect project type")

    build_tool = random.choice(sig["build_tools"])
    suffix = random.randint(1000, 9999)

    # deps
    cfg = next((Path(p) for p in files if sig["dependencies_file"].lower() in p.lower()), None)
    deps = _extract_deps(cfg, sig["dependency_pattern"], sig["type"]) if cfg else []
    if not deps and sig["dependencies"]:
        deps = random.sample(sig["dependencies"], random.randint(1, min(2, len(sig["dependencies"]))))

    # sample source files (до 5 шт.)
    sample: List[Dict[str, str]] = []
    for f in files:
        if any(tok.format("")[:-1] in f for tok in build_tool["files"]):
            txt = _read_file(Path(f))
            if txt:
                sample.append({"path": f, "content": txt})
            if len(sample) == 5:
                break

    env = random.choice(["", f"export APP_ENV={random.choice(['dev','test','prod'])}; "])

    pj = {
        "project": {
            "type": sig["type"],
            "build_tool": build_tool["name"],
            "test_frameworks": [random.choice(sig["test_frameworks"])],
            "dockerfile_present": docker,
            "files": sample,
            "dependencies": deps,
            "scripts": {
                "build": {
                    "unix": env + random.choice(build_tool["build_script_unix"]),
                    "windows": env + random.choice(build_tool["build_script_win"]),
                },
                "test": {
                    "unix": env + random.choice(build_tool["test_script_unix"]),
                    "windows": env + random.choice(build_tool["test_script_win"]),
                },
            },
        }
    }
    if "lint_script_unix" in build_tool:
        pj["project"]["scripts"]["lint"] = {
            "unix": env + random.choice(build_tool["lint_script_unix"]),
            "windows": env + random.choice(build_tool["lint_script_win"]),
        }

    h = hashlib.sha256(json.dumps(pj, sort_keys=True).encode()).hexdigest()
    return pj, h


# ───────── asyncio-friendly wrapper ───────────────────────────────────────────
async def analyze_async(repo_root: str = ".") -> Tuple[Dict[str, Any], str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXEC, analyze_repository, repo_root)
