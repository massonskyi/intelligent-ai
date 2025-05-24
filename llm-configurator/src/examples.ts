// src/examples/promptExamples.ts
import { PromptExample } from "./components/PromptExamples";

const EXAMPLES: PromptExample[] = [
  {
    label: "Jenkins pipeline для Python (unittest, lint)",
    prompt: `Generate a Jenkins pipeline for a Python project.
Requirements:
- Install dependencies from requirements.txt using pip and virtualenv
- Run tests with unittest
- Run lint with flake8
- Output only the Jenkinsfile code, nothing else.`,
    description: "Python, pip, unittest, flake8, только Jenkinsfile"
  },
  {
    label: "Jenkins pipeline для PySide6 GUI-проекта",
    prompt: `Generate a Jenkins pipeline for the given project configuration:
{
  "project": {
    "type": "python",
    "buildTool": "pip",
    "testFrameworks": ["unittest"],
    "dockerfilePresent": false,
    "files": ["config/cfg.py", "gui/main_window.py", "gui/Threads/CallbackThread.py"],
    "dependencies": ["PySide6==6.7.2", "numpy==2.0.0", "opencv-python==4.10.0.84", "pandas==2.2.2"],
    "scripts": {
      "build": {"unix": "pip install -r requirements.txt", "windows": "pip install -r requirements.txt"},
      "test": {"unix": "pytest", "windows": "pytest"},
      "lint": {"unix": "flake8 .", "windows": "flake8 ."}
    }
  }
}
Only return Jenkinsfile code.`,
    description: "Реальный PySide6 проект с зависимостями и разными скриптами"
  },
  {
    label: "Jenkins pipeline для Docker-based Python backend",
    prompt: `Generate a Jenkins pipeline (Jenkinsfile) for a Python backend project which uses Docker for deployment. It should:
- Build docker image
- Run unit tests inside docker
- Lint with flake8
- Push image to DockerHub if tests pass
Jenkinsfile only, no explanations.`,
    description: "Backend на Python, dockerized, unit-test, flake8, push"
  },
  {
    label: "Jenkins pipeline (pyinstaller, build, test, lint)",
    prompt: `Generate a Jenkins pipeline for a Python application that must be built into an executable using pyinstaller, tested with pytest, and linted with flake8. Only Jenkinsfile code, please.`,
    description: "Pyinstaller + pytest + flake8 пайплайн"
  },
  {
    label: "Jenkins pipeline для многоплатформенного Python",
    prompt: `Create a Jenkins pipeline for a cross-platform Python project. Use matrix build for Linux/Windows:
- Install dependencies from requirements.txt
- Run tests (pytest)
- Run lint (flake8)
- Archive build artifacts
Show only the Jenkinsfile.`,
    description: "Matrix build: Windows + Linux, архивирование артефактов"
  },
  {
    label: "Jenkins pipeline для ML проекта",
    prompt: `Generate a Jenkins pipeline for a Python machine learning project:
- Install dependencies (numpy, pandas, scikit-learn)
- Train model (python train.py)
- Test (pytest)
- Save metrics as artifacts
Jenkinsfile only.`,
    description: "ML pipeline: train, test, save metrics"
  },
  {
    label: "Jenkins pipeline с deployment через SSH",
    prompt: `Generate a Jenkins pipeline for a Python project that, after passing tests and lint, deploys to a remote Linux server via SSH. Jenkinsfile only.`,
    description: "Auto deploy через ssh после тестов"
  },
  {
    label: "Jenkins pipeline для FastAPI + Pytest",
    prompt: `Generate a Jenkinsfile for a FastAPI backend project:
- Install dependencies (pip)
- Run tests with pytest
- Lint with flake8
- Only output Jenkinsfile code.`,
    description: "FastAPI + pytest"
  },
  {
    label: "Jenkins pipeline: только Bash steps",
    prompt: `Jenkinsfile for a Python project where all steps (install, test, lint) are implemented as Bash shell commands. Jenkinsfile only.`,
    description: "Все стадии — только sh"
  },
  {
    label: "Jenkins pipeline (prod/staging)",
    prompt: `Generate a Jenkinsfile with separate stages for deploy to staging and production environments after test and lint steps. Show only Jenkinsfile.`,
    description: "Деплой в staging и production"
  }
];

export default EXAMPLES;
