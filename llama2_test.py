from src.models.llama2 import Llama2Model


if __name__ == "__main__":
    llama = Llama2Model("meta-llama/Llama-2-7b-chat-hf")
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
    pipeline_code = llama.generate_pipeline(req)
    print(pipeline_code)
