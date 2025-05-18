import json
import os
from pathlib import Path
import random
import uuid
import hashlib
import re

from typing import Final, List, Dict, Any
# Шаблоны проектов с поддержкой анализа кода и зависимостей
PROJECT_SIGNATURES: Final[List[Dict[str, Any]]] = [
    {
        "type": "java",
        "signature_files": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "build_tools": [
            {
                "name": "maven",
                "build_script_unix": ["mvn clean install", "mvn -B package", "mvn clean install -DskipTests"],
                "build_script_win": ["mvn.cmd clean install", "mvn.cmd -B package", "mvn.cmd clean install -DskipTests"],
                "test_script_unix": ["mvn test", "mvn verify", "mvn test -DskipTests=false"],
                "test_script_win": ["mvn.cmd test", "mvn.cmd verify", "mvn.cmd test -DskipTests=false"],
                "files": ["pom.xml", "src/main/java/App{}.java", "src/test/java/AppTest{}.java"],
                "artifacts": ["**/target/*.jar", "**/target/*.war"]
            },
            {
                "name": "gradle",
                "build_script_unix": ["./gradlew build", "./gradlew assemble", "./gradlew build --parallel"],
                "build_script_win": ["gradlew.bat build", "gradlew.bat assemble", "gradlew.bat build --parallel"],
                "test_script_unix": ["./gradlew test", "./gradlew check", "./gradlew test --rerun"],
                "test_script_win": ["gradlew.bat test", "gradlew.bat check", "gradlew.bat test --rerun"],
                "files": ["build.gradle", "src/main/java/Main{}.java", "src/test/java/MainTest{}.java"],
                "artifacts": ["**/build/libs/*.jar", "**/build/distributions/*.zip"]
            }
        ],
        "test_frameworks": ["junit5", "testng", "spock"],
        "dependencies_file": "pom.xml",
        "dependency_pattern": r'<dependency>\s*<groupId>(.*?)</groupId>\s*<artifactId>(.*?)</artifactId>',
        "dependencies": ["spring-boot", "log4j", "spring-core", "hibernate", "guava", "jackson", "apache-commons"],
    },
    {
        "type": "python",
        "signature_files": ["requirements.txt", "setup.py", "pyproject.toml"],
        "build_tools": [
            {
                "name": "pip",
                "build_script_unix": ["pip install -r requirements.txt", "pip install .", "pip install -r requirements.txt --no-cache-dir"],
                "build_script_win": ["pip install -r requirements.txt", "pip install .", "pip install -r requirements.txt --no-cache-dir"],
                "test_script_unix": ["pytest --verbose", "pytest -v tests/", "pytest --cov"],
                "test_script_win": ["pytest --verbose", "pytest -v tests/", "pytest --cov"],
                "lint_script_unix": ["flake8 .", "pylint src/", "flake8 --max-line-length=100"],
                "lint_script_win": ["flake8 .", "pylint src/", "flake8 --max-line-length=100"],
                "files": ["requirements{}.txt", "app{}.py", "tests/test_app{}.py"],
                "artifacts": ["*.whl", "dist/*.tar.gz"]
            }
        ],
        "test_frameworks": ["pytest", "unittest", "nose2"],
        "dependencies_file": "requirements.txt",
        "dependency_pattern": r'^([a-zA-Z0-9_-]+)(?:[>=<]+.*)?$',
        "dependencies": ["flask", "requests", "django", "pandas", "numpy", "fastapi", "sqlalchemy"],
    },
    {
        "type": "nodejs",
        "signature_files": ["package.json"],
        "build_tools": [
            {
                "name": "npm",
                "build_script_unix": ["npm install", "npm ci", "npm install --production=false"],
                "build_script_win": ["npm install", "npm ci", "npm install --production=false"],
                "test_script_unix": ["npm test", "npm run test:unit", "npm test -- --coverage"],
                "test_script_win": ["npm test", "npm run test:unit", "npm test -- --coverage"],
                "lint_script_unix": ["npm run lint", "eslint src/", "npm run lint -- --fix"],
                "lint_script_win": ["npm run lint", "eslint src/", "npm run lint -- --fix"],
                "files": ["package{}.json", "server{}.js", "test/test{}.js"],
                "artifacts": ["dist/*.js", "build/*.js"]
            }
        ],
        "test_frameworks": ["jest", "mocha", "cypress"],
        "dependencies_file": "package.json",
        "dependency_pattern": r'"dependencies":\s*{([^}]*)}',
        "dependencies": ["express", "lodash", "axios", "react", "vue", "webpack", "babel"],
    },
    {
        "type": "rust",
        "signature_files": ["Cargo.toml"],
        "build_tools": [
            {
                "name": "cargo",
                "build_script_unix": ["cargo build --release", "cargo build", "cargo build --locked"],
                "build_script_win": ["cargo build --release", "cargo build", "cargo build --locked"],
                "test_script_unix": ["cargo test", "cargo test --all", "cargo test --no-fail-fast"],
                "test_script_win": ["cargo test", "cargo test --all", "cargo test --no-fail-fast"],
                "lint_script_unix": ["cargo fmt -- --check && cargo clippy", "cargo clippy -- -D warnings"],
                "lint_script_win": ["cargo fmt -- --check && cargo clippy", "cargo clippy -- -D warnings"],
                "files": ["Cargo{}.toml", "src/main{}.rs", "tests/test{}.rs"],
                "artifacts": ["target/release/*", "target/debug/*"]
            }
        ],
        "test_frameworks": ["cargo-test"],
        "dependencies_file": "Cargo.toml",
        "dependency_pattern": r'^\s*([a-zA-Z0-9_-]+)\s*=\s*".*"',
        "dependencies": ["serde", "tokio", "reqwest", "clap", "log"],
    },
    {
        "type": "go",
        "signature_files": ["go.mod"],
        "build_tools": [
            {
                "name": "go",
                "build_script_unix": ["go build -o bin/app{}", "go build -v", "go build -o bin/app{} -ldflags '-s -w'"],
                "build_script_win": ["go build -o bin/app{}.exe", "go build -v", "go build -o bin/app{}.exe -ldflags '-s -w'"],
                "test_script_unix": ["go test ./...", "go test -v ./...", "go test -cover"],
                "test_script_win": ["go test ./...", "go test -v ./...", "go test -cover"],
                "lint_script_unix": ["golangci-lint run", "go vet ./..."],
                "lint_script_win": ["golangci-lint run", "go vet ./..."],
                "files": ["go{}.mod", "main{}.go", "main_test{}.go"],
                "artifacts": ["bin/*", "bin/app{}"]
            }
        ],
        "test_frameworks": ["testing", "testify"],
        "dependencies_file": "go.mod",
        "dependency_pattern": r'require\s+([a-zA-Z0-9_/.-]+)\s+v.*',
        "dependencies": ["gin", "mux", "logrus"],
    },
]

def read_file_content(file_path, max_lines=50):
    """Читает содержимое файла, ограничивая количество строк."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[:max_lines]
            return "".join(lines).strip()
    except (UnicodeDecodeError, IOError):
        return ""

def extract_dependencies(file_path, pattern, project_type):
    """Извлекает зависимости из конфигурационного файла."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if project_type == "nodejs":
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                deps_str = match.group(1)
                deps = [dep.split(":")[0].strip().strip('"') for dep in deps_str.split(",") if dep.strip()]
                return [dep for dep in deps if dep]
        else:
            matches = re.findall(pattern, content, re.MULTILINE)
            if project_type == "java":
                return [f"{group}:{artifact}" for group, artifact in matches]
            return [match for match in matches]
        return []
    except (UnicodeDecodeError, IOError):
        return []

def generate_unique_files(template_files, suffix):
    """Генерирует уникальные имена файлов с суффиксом."""
    return [f.format(suffix) if "{}" in f else f for f in template_files]

def generate_unique_artifact(artifacts, suffix):
    """Генерирует уникальный артефакт с суффиксом."""
    artifact = random.choice(artifacts)
    return artifact.format(suffix) if "{}" in artifact else artifact

def analyze_repository(repo_path="."):
    """Анализирует репозиторий и собирает данные о проекте."""
    repo_path = Path(repo_path)
    project_type = None
    project_files = []
    dockerfile_present = False
    dependencies = []
    suffix = random.randint(1000, 9999)

    # Сканирование всех файлов
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = str(Path(root) / file)
            project_files.append(file_path)
            if file.lower() == "dockerfile":
                dockerfile_present = True

    # Определение типа проекта
    for template in PROJECT_SIGNATURES:
        if any(any(f.lower() in p.lower() for f in template["signature_files"]) for p in project_files):
            project_type = template["type"]
            break

    if not project_type:
        print("Проект не распознан: ключевые файлы не найдены.")
        return None

    template = next(t for t in PROJECT_SIGNATURES if t["type"] == project_type)
    build_tool = random.choice(template["build_tools"])

    # Извлечение зависимостей
    dep_file = next((f for f in project_files if template["dependencies_file"].lower() in f.lower()), None)
    if dep_file:
        dependencies = extract_dependencies(dep_file, template["dependency_pattern"], project_type)

    # Формирование списка файлов с содержимым
    files_with_content = []
    for file_path in project_files:
        if any(ext.lower() in file_path.lower() for ext in build_tool["files"]):
            content = read_file_content(file_path)
            if content:
                files_with_content.append({"path": file_path, "content": content})
        if len(files_with_content) >= 5:  # Ограничение до 5 файлов
            break

    # Генерация уникальных скриптов
    env_vars = random.choice([
        "",
        f"export APP_ENV={random.choice(['dev', 'test', 'prod'])}; ",
        f"export BUILD_ID={random.randint(1000, 9999)}; "
    ])

    # Исправление логики зависимостей
    project_analysis = {
        "project": {
            "type": project_type,
            "build_tool": build_tool["name"],
            "test_frameworks": [random.choice(template["test_frameworks"])],
            "dockerfile_present": dockerfile_present,
            "files": files_with_content,
            "dependencies": dependencies if dependencies else (
                random.sample(
                    template.get("dependencies", []),
                    random.randint(1, min(2, len(template.get("dependencies", []))))
                ) if template.get("dependencies", []) else []
            ),
            "scripts": {
                "build": {
                    "unix": env_vars + random.choice(build_tool["build_script_unix"]),
                    "windows": env_vars + random.choice(build_tool["build_script_win"])
                },
                "test": {
                    "unix": env_vars + random.choice(build_tool["test_script_unix"]),
                    "windows": env_vars + random.choice(build_tool["test_script_win"])
                }
            }
        }
    }

    if "lint_script_unix" in build_tool:
        project_analysis["project"]["scripts"]["lint"] = {
            "unix": env_vars + random.choice(build_tool["lint_script_unix"]),
            "windows": env_vars + random.choice(build_tool["lint_script_win"])
        }

    return project_analysis, build_tool, suffix

def generate_jenkins_pipeline(project_analysis, build_tool, suffix):
    """Генерирует Jenkins pipeline на основе анализа проекта."""
    pipeline = [
        "pipeline {",
        "    agent any",
        f"    environment {{",
        f"        BUILD_TAG = '{uuid.uuid4().hex[:8]}'",
        f"    }}",
        "    stages {"
    ]

    is_windows = random.choice([True, False])
    platform = "windows" if is_windows else "unix"

    stages = []
    if "lint" in project_analysis["project"]["scripts"]:
        stages.append(("Lint", [
            "        stage('Lint') {",
            "            steps {",
            f"                // Running lint checks for {project_analysis['project']['type']} project",
            f"                {'bat' if is_windows else 'sh'} '{project_analysis['project']['scripts']['lint'][platform]}'",
            "            }",
            "        }"
        ]))

    stages.append(("Build", [
        "        stage('Build') {",
        "            steps {",
        f"                // Building {project_analysis['project']['type']} project",
        f"                {'bat' if is_windows else 'sh'} '{project_analysis['project']['scripts']['build'][platform]}'",
        "            }",
        "        }"
    ]))

    if project_analysis["project"]["test_frameworks"][0] != "none":
        stages.append(("Test", [
            "        stage('Test') {",
            "            steps {",
            f"                // Running tests with {project_analysis['project']['test_frameworks'][0]}",
            f"                {'bat' if is_windows else 'sh'} '{project_analysis['project']['scripts']['test'][platform]}'",
            "            }",
            "        }"
        ]))

    if project_analysis["project"]["dockerfile_present"]:
        docker_tag = random.choice(['latest', f'v{random.randint(1, 10)}.{random.randint(0, 9)}', f'dev-{uuid.uuid4().hex[:4]}'])
        stages.append(("Docker", [
            "        stage('Build Docker Image') {",
            "            steps {",
            f"                // Building Docker image for {project_analysis['project']['type']}",
            f"                {'bat' if is_windows else 'sh'} 'docker build -t {project_analysis['project']['type']}-app-{uuid.uuid4().hex[:6]}:{docker_tag} .'",
            "            }",
            "        }"
        ]))

    if build_tool and build_tool["artifacts"] != "none" and random.random() < 0.5:
        artifact = generate_unique_artifact(build_tool["artifacts"], suffix)
        stages.append(("Publish", [
            "        stage('Publish') {",
            "            steps {",
            f"                // Archiving artifacts: {artifact}",
            f"                archiveArtifacts artifacts: '{artifact}', allowEmptyArchive: true",
            "            }",
            "        }"
        ]))

    if random.random() < 0.3:
        stages.append(("Deploy", [
            "        stage('Deploy') {",
            "            when {",
            "                expression { env.BRANCH_NAME == 'main' }",
            "            }",
            "            steps {",
            f"                // Deploying {project_analysis['project']['type']} to {random.choice(['staging', 'production'])}",
            f"                {'bat' if is_windows else 'sh'} 'echo Deploying to {random.choice(['staging', 'production'])}'",
            "            }",
            "        }"
        ]))

    random.shuffle(stages)
    for _, stage_lines in stages:
        pipeline.extend(stage_lines)

    pipeline.extend([
        "    }",
        "    post {",
        "        always {",
        f"            // Clean up workspace for build {uuid.uuid4().hex[:8]}",
        "            cleanWs()",
        "        }",
        "        success {",
        f"            echo 'Build for {project_analysis['project']['type']} succeeded with tag $BUILD_TAG!'",
        "        }",
        "        failure {",
        f"            echo 'Build for {project_analysis['project']['type']} failed with tag $BUILD_TAG!'",
        "        }",
        "    }",
        "}"
    ])

    return "\n".join(pipeline)

def generate_training_entry(repo_path="."):
    """Генерирует запись для обучения на основе анализа репозитория."""
    result = analyze_repository(repo_path)
    if not result:
        return None, None

    project_analysis, build_tool, suffix = result
    pipeline = generate_jenkins_pipeline(project_analysis, build_tool, suffix)
    entry = {
        "instruction": f"Generate a Jenkins pipeline for the given project configuration {uuid.uuid4().hex[:8]}",
        "input": json.dumps(project_analysis, separators=(",", ":")),
        # "output": pipeline
    }

    entry_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
    return entry, entry_hash

def main():
    """Анализирует проект и сохраняет данные в JSONL-файл."""
    output_file = "project_analysis.jsonl"
    repo_path = "."
    generated_hashes = set()

    entry, entry_hash = generate_training_entry(repo_path)
    if not entry:
        print(f"Не удалось сгенерировать данные. Выходной файл {output_file} не создан.")
        return

    if entry_hash in generated_hashes:
        print("Сгенерирована дублирующая запись, пропускаем.")
        return

    generated_hashes.add(entry_hash)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"Анализ проекта завершен. Данные сохранены в {output_file}")

if __name__ == "__main__":
    main()