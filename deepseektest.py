from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer, util
import torch
import json
import os

# Конфигурация для вашего железа
model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

# Инициализация моделей
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quant_config,
    device_map="auto",
    use_flash_attention_2=True
)
retriever = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# База знаний Jenkins-пайплайнов (дополняйте своими примерами)
rag_examples = [
    {
        "description": "Python project with pip and unittest",
        "pipeline": """pipeline {
            agent any
            stages {
                stage('Install dependencies') {
                    steps {
                        sh 'pip install -r requirements.txt'
                    }
                }
                stage('Run tests') {
                    steps {
                        sh 'python -m unittest discover -s tests -p "*_test.py"'
                    }
                }
            }
        }"""
    },
    {
        "description": "Python project with Docker",
        "pipeline": """pipeline {
            agent any
            stages {
                stage('Build Docker image') {
                    steps {
                        script {
                            docker.build("my-image:${env.BUILD_ID}")
                        }
                    }
                }
            }
        }"""
    }
]

def generate_jenkins_pipeline(config):
    # 1. Retrieval: Поиск релевантных примеров
    query = f"""
        Project type: {config['project']['type']}
        Build tool: {config['project']['buildTool']}
        Test frameworks: {', '.join(config['project']['testFrameworks'])}
        Docker: {config['project']['dockerfilePresent']}
    """
    example_texts = [ex["description"] + " " + ex["pipeline"] for ex in rag_examples]
    
    # Поиск по сходству
    query_embedding = retriever.encode(query, convert_to_tensor=True)
    doc_embeddings = retriever.encode(example_texts, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, doc_embeddings)[0]
    top_examples = [rag_examples[i] for i in torch.topk(scores, k=2).indices.tolist()]

    # 2. Генерация с использованием RAG-контекста
    system_prompt = """Ты эксперт по Jenkins. Сгенерируй pipeline на основе примера и конфигурации проекта."""
    
    user_prompt = f"""
    Конфигурация проекта:
    {json.dumps(config, indent=2)}
    
    Примеры похожих пайплайнов:
    {json.dumps(top_examples, indent=2)}
    
    Сгенерируй Jenkinsfile для этой конфигурации. Учти:
    - Используй declarative pipeline syntax
    - Добавь этапы для установки зависимостей, тестов и линтинга
    - Учитывай ОС-специфичные команды из конфига
    - Docker stages только если dockerfilePresent=true
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=1024,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Пример использования
config = {
    "instruction": "Generate a Jenkins pipeline...",
    "input": {
        "project": {
            # ... ваш конфиг из примера ...
        }
    }
}

pipeline = generate_jenkins_pipeline(config["input"])
print("Сгенерированный пайплайн:\n", pipeline)