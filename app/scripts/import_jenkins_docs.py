# scripts/import_jenkins_docs.py
import sys
import os

# Убедись, что PYTHONPATH содержит корень проекта (чтобы импортировать retriever_service)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.retriever_service import retriever_service
docs = [
    {
        "id": "doc1",
        "text": "Jenkins pipelines can be written in Groovy using the 'pipeline' DSL. Define stages, steps, and use environment variables for configuration. Example:\n\npipeline {\n  agent any\n  stages {\n    stage('Build') {\n      steps {\n        sh 'make build'\n      }\n    }\n  }\n}",
        "metadata": {
            "title": "Jenkins Pipeline Basics",
            "url": "https://www.jenkins.io/doc/book/pipeline/syntax/"
        }
    },
    {
        "id": "doc2",
        "text": "To run Python tests in a Jenkins pipeline, add a stage with 'sh' or 'bat' steps. Example (Unix):\nstage('Test') {\n  steps {\n    sh 'pytest tests/'\n  }\n}\nFor Windows agents, use 'bat'.",
        "metadata": {
            "title": "Python Testing in Jenkins",
            "url": "https://www.jenkins.io/doc/pipeline/examples/"
        }
    },
    {
        "id": "doc3",
        "text": "For CI/CD with Docker, use the 'docker' agent in your Jenkinsfile. Example:\npipeline {\n  agent { docker { image 'python:3.11' } }\n  stages { ... } }",
        "metadata": {
            "title": "Docker Agent",
            "url": "https://www.jenkins.io/doc/book/pipeline/docker/"
        }
    },
    {
        "id": "doc4",
        "text": "Use environment variables in pipelines for secrets and configs. Example:\nenvironment {\n  SECRET_KEY = credentials('jenkins-secret')\n}\n",
        "metadata": {
            "title": "Environment Variables",
            "url": "https://www.jenkins.io/doc/book/pipeline/syntax/#environment"
        }
    },
    {
        "id": "doc5",
        "text": "To archive build artifacts in Jenkins:\npost {\n  success {\n    archiveArtifacts artifacts: '*.whl', allowEmptyArchive: true\n  }\n}",
        "metadata": {
            "title": "Archiving Artifacts",
            "url": "https://www.jenkins.io/doc/pipeline/steps/core/#archiveartifacts-archive-the-artifacts"
        }
    },
    {
        "id": "doc6",
        "text": "Matrix builds let you run tests across multiple environments:\nmatrix {\n  axes {\n    axis { name: 'PYTHON'; values: '3.8', '3.11' }\n  }\n  stages { ... }\n}",
        "metadata": {
            "title": "Matrix Builds",
            "url": "https://www.jenkins.io/doc/book/pipeline/syntax/#matrix"
        }
    },
    {
        "id": "doc7",
        "text": "Use 'bat' steps for Windows commands:\nstage('Build') {\n  steps {\n    bat 'python setup.py build'\n  }\n}",
        "metadata": {
            "title": "Windows Steps",
            "url": "https://www.jenkins.io/doc/pipeline/examples/"
        }
    },
    {
        "id": "doc8",
        "text": "Declarative vs Scripted Pipeline:\n- Declarative is recommended for most projects.\n- Scripted uses pure Groovy, Declarative is more structured.\nExample:\nscript {\n  // scripted pipeline logic\n}\n",
        "metadata": {
            "title": "Declarative vs Scripted",
            "url": "https://www.jenkins.io/doc/book/pipeline/syntax/"
        }
    },
    {
        "id": "doc9",
        "text": "To install dependencies in a Jenkins pipeline (Python):\nstage('Install') {\n  steps {\n    sh 'pip install -r requirements.txt'\n  }\n}",
        "metadata": {
            "title": "Dependency Installation",
            "url": "https://pip.pypa.io/en/stable/cli/pip_install/"
        }
    },
    {
        "id": "doc10",
        "text": "Best practices:\n- Always pin dependency versions\n- Use virtual environments\n- Add linting (e.g. flake8) as a pipeline stage\n- Archive artifacts and logs\n- Use post{} for notifications and cleanup",
        "metadata": {
            "title": "Jenkins Pipeline Best Practices",
            "url": "https://www.jenkins.io/doc/book/pipeline/best-practices/"
        }
    }
]
if __name__ == "__main__":
    print(f"Importing {len(docs)} Jenkins docs into ChromaDB...")
    retriever_service.add_docs(docs)
    print("Done.")