import platform
import multiprocessing
import psutil
from llama_cpp import Llama

class LlamaCppPipelineGenerator:
    def __init__(self, model_path: str, n_ctx: int = 4096, n_threads: int = None, n_gpu_layers: int = 20):
        self.model_path = model_path
        if n_threads is None:
            n_threads = multiprocessing.cpu_count()
        # GPU-ускорение, если твой билд llama.cpp это поддерживает
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=True
        )

    def build_prompt(self, request: dict) -> str:
        instruction = request.get("instruction", "Generate a Jenkins pipeline for the given project configuration")
        project = request.get("input", {}).get("project", {})
        parts = [instruction.strip(), ""]
        if project.get("type"):
            parts.append(f"Project type: {project['type']}")
        if project.get("buildTool"):
            parts.append(f"Build tool: {project['buildTool']}")
        if "testFrameworks" in project and project["testFrameworks"]:
            parts.append(f"Test frameworks: {', '.join(project['testFrameworks'])}")
        if "dockerfilePresent" in project:
            parts.append(f"Dockerfile present: {project['dockerfilePresent']}")
        if "files" in project:
            files_short = ', '.join(project["files"][:5])
            if len(project["files"]) > 5:
                files_short += f", ... (+{len(project['files'])-5} files)"
            parts.append(f"Project files: {files_short}")
        if "dependencies" in project and project["dependencies"]:
            deps_short = ', '.join(project["dependencies"][:8])
            if len(project["dependencies"]) > 8:
                deps_short += f", ... (+{len(project['dependencies'])-8} deps)"
            parts.append(f"Dependencies: {deps_short}")
        if "scripts" in project and project["scripts"]:
            script_lines = []
            for name, scripts in project["scripts"].items():
                script_lines.append(f"{name.capitalize()} (unix): {scripts.get('unix','')}; (windows): {scripts.get('windows','')}")
            parts.append("Project scripts:\n" + "\n".join(script_lines))
        prompt = "\n".join(parts).strip()
        return prompt

    def inference(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7, top_p: float = 0.95):
        res = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            echo=False,
            stop=["</s>", "<|endoftext|>"]
        )
        return res["choices"][0]["text"]

    def generate_pipeline(self, request: dict, **gen_kwargs) -> str:
        prompt = self.build_prompt(request)
        response = self.inference(prompt, **gen_kwargs)
        # Выделим только Jenkins pipeline
        import re
        match = re.search(r'(pipeline\s*\{.*)', response, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
