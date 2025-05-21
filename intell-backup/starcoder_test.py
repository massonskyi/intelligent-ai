from src.models.starcoder import StarCoderModel


if __name__ == "__main__":
    model = StarCoderModel("HuggingFaceH4/starchat-alpha")  # Или bigcode/starcoderbase-7b
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
    pipeline_code = model.generate_pipeline(req)
    print(pipeline_code)
