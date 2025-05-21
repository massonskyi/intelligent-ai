from typing import List, Dict, Any

def retrieve_context(question: str, top_k: int = 3) -> List[Dict[str, Any]]:
    # Заглушка для примера (дальше подключишь свой vector search/Chroma/FAISS)
    return [
        {
            "title": "Jenkins Pipeline Basics",
            "snippet": "Jenkins pipelines can be written in Groovy and define stages.",
            "url": "https://www.jenkins.io/doc/book/pipeline/syntax/",
            "score": 0.93
        },
        {
            "title": "Python in Jenkins Pipelines",
            "snippet": "Use the 'sh' step to run pip commands for Python projects.",
            "url": "https://www.jenkins.io/doc/pipeline/steps/workflow-durable-task-step/",
            "score": 0.89
        },
        {
            "title": "Windows Agents",
            "snippet": "Use the 'bat' step to run Windows batch scripts in Jenkins.",
            "url": "https://www.jenkins.io/doc/pipeline/steps/workflow-durable-task-step/#bat-batch-script",
            "score": 0.84
        }
    ][:top_k]
