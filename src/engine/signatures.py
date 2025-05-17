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
