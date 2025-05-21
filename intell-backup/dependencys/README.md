Варианты запуска:

1. Prebuilt бинарники

    Release page llama.cpp

    Есть Windows build для main.exe (CPU-only).

    Для CUDA — нужен билд с поддержкой GPU (можно собрать самому).

2. Сборка из исходников
CPU-only (AVX2/AVX512)

git clone <https://github.com/ggerganov/llama.cpp>
cd llama.cpp
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release

    Или просто:

    .\build\bin\Release\main.exe -m model.gguf -p "Write a Jenkins pipeline for a Python project"

Сборка с CUDA (GPU)

    Предварительно поставь CUDA toolkit (>=11.8), cmake >= 3.25.

cmake .. -DLLAMA_CUBLAS=ON -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release

    Получишь main.exe с поддержкой CUDA.

Сборка с DirectML (GPU на любых GPU Windows)

    Нужно Visual Studio, DirectML SDK:

cmake .. -DLLAMA_DML=ON -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release

3. Python binding (llama-cpp-python)

pip install llama-cpp-python --upgrade

    Работает с CPU/GPU (CUDA, Metal, OpenCL через переменные окружения).

    Запуск кода почти как transformers, пример:

from llama_cpp import Llama
llm = Llama(model_path="codellama-7b-instruct.Q4_K_M.gguf")
print(llm["Write a Jenkins pipeline for Python project"]["choices"](0)["text"])

Особенности:

    Поддержка quant (Q2, Q4, Q5, Q6, Q8), ultra-low RAM.

    CLI быстрый, RAM-экономный.

    Можно использовать вместе с webui, text-generation-webui и т.д.

    Нет интеграции с transformers API, prompt format специфичен для модели (иногда нужен system prompt/manual stop).

