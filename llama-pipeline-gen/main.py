import platform
from src.llama_cpp_pipeline import LlamaCppPipelineGenerator

if __name__ == "__main__":
    # Автоматический выбор пути к модели
    if platform.system() == "Windows":
        model_path = r"D:\models\codellama-7b-instruct.Q4_K_M.gguf"
    else:
        model_path = "/models/codellama-7b-instruct.Q4_K_M.gguf"

    generator = LlamaCppPipelineGenerator(model_path)
    req = {
        "instruction": "Generate a Jenkins pipeline for the given project configuration",
        "input": {
            "project": {
                "type": "python",
                "buildTool": "pip",
                "testFrameworks": ["pytest"],
                "dockerfilePresent": False,
                "files": ["main.py", "setup.py", "requirements.txt"],
                "dependencies": ["pytest==7.1.0", "requests==2.27.1"],
                "scripts": {
                    "build": {"unix": "pip install -r requirements.txt", "windows": "pip install -r requirements.txt"},
                    "test": {"unix": "pytest", "windows": "pytest"},
                }
            }
        }
    }
    pipeline_code = generator.generate_pipeline(req, max_tokens=200)
    print(pipeline_code)
