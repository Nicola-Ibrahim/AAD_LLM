# Custom Model Configuration Guide

Our scripts and environment templates are fully decoupled from hardcoded models. This guide details how to change the model, explains each configuration variable, and provides pre-set configurations for alternative model sizes.

---

## 🛠️ Environment Variables Explained

All configurations are read from the project root `.env` file. To change the active model, open your `.env` file and modify these three variables:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `HF_REPO` | The Hugging Face repository path. | `Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF` |
| `HF_FILE` | The exact GGUF file name inside that repository to download. | `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf` |
| `LOCAL_LLM_MODEL` | The model name string LLaMEA will use in API requests. | `qwen2.5-coder-1.5b-instruct-q4_k_m` |
| `LLM_SERVER_HOST` | Local server network interface host IP. | `0.0.0.0` |
| `LLM_SERVER_PORT` | Local server network port. | `1234` |
| `LLM_SERVER_N_CTX` | Context window token size for candidate algorithm evolution. | `8192` |
| `LLM_SERVER_N_THREADS` | Number of CPU threads assigned to model inference. | `8` |

---

## 📋 Ready-to-Use Model Presets (Small to Medium)

Here are 6 ready-to-use configurations from small to medium sizes. Simply copy and paste any of these blocks into your `.env` file.

### ─── QWEN CODER MODELS ───

#### 1. Qwen2.5-Coder-1.5B-Instruct (Small / Fast CPU Prototyping)
*Size: ~1.6 GB | Recommended RAM: >= 4 GB*
*Best for fast local smoke-tests to verify pipeline logic without waiting for heavy inference.*
```ini
LLM_PROVIDER=local
HF_REPO=Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF
HF_FILE=qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
LOCAL_LLM_MODEL=qwen2.5-coder-1.5b-instruct-q4_k_m
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_API_KEY=not-needed
```

#### 2. Qwen2.5-Coder-3B-Instruct (Small-Medium / Balanced Performance)
*Size: ~3.2 GB | Recommended RAM: >= 6 GB*
*A sweet spot for slightly better reasoning than 1.5B while staying extremely fast and lightweight.*
```ini
LLM_PROVIDER=local
HF_REPO=Qwen/Qwen2.5-Coder-3B-Instruct-GGUF
HF_FILE=qwen2.5-coder-3b-instruct-q4_k_m.gguf
LOCAL_LLM_MODEL=qwen2.5-coder-3b-instruct-q4_k_m
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_API_KEY=not-needed
```

#### 3. Qwen2.5-Coder-7B-Instruct (Medium / Default Recommendation)
*Size: ~4.8 GB | Recommended RAM: >= 8 GB (M-series Mac or GPU recommended)*
*Excellent coding capability and the standard baseline for LLaMEA optimization.*
```ini
LLM_PROVIDER=local
HF_REPO=Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
HF_FILE=qwen2.5-coder-7b-instruct-q4_k_m.gguf
LOCAL_LLM_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_API_KEY=not-needed
```

---

### ─── ALTERNATIVE / ADVERSARIAL MODELS ───

#### 4. DeepSeek-Coder-1.5B-Instruct (Small Alternative / Fast Coder)
*Size: ~1.6 GB | Recommended RAM: >= 4 GB*
*DeepSeek's highly optimized lightweight model for code generation tasks.*
```ini
LLM_PROVIDER=local
HF_REPO=DeepSeek-Coder-1.5B-Instruct-GGUF
HF_FILE=deepseek-coder-1.5b-instruct-q4_k_m.gguf
LOCAL_LLM_MODEL=deepseek-coder-1.5b-instruct-q4_k_m
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_API_KEY=not-needed
```

#### 5. DeepSeek-Coder-6.7B-Instruct (Medium Alternative / Strong Coding Benchmarks)
*Size: ~4.8 GB | Recommended RAM: >= 8 GB*
*A very strong open-source alternative to Qwen-7B with a deep understanding of complex code structures.*
```ini
LLM_PROVIDER=local
HF_REPO=DeepSeek-Coder-6.7B-Instruct-GGUF
HF_FILE=deepseek-coder-6.7b-instruct-q4_k_m.gguf
LOCAL_LLM_MODEL=deepseek-coder-6.7b-instruct-q4_k_m
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_API_KEY=not-needed
```

#### 6. Meta-Llama-3.1-8B-Instruct (Medium Alternative / General Purpose Reasoner)
*Size: ~4.9 GB | Recommended RAM: >= 8 GB*
*The Llama-3.1 architecture. Excellent general reasoning, instruction following, and logical code generation.*
```ini
LLM_PROVIDER=local
HF_REPO=QuantFactory/Meta-Llama-3.1-8B-Instruct-GGUF
HF_FILE=Meta-Llama-3.1-8B-Instruct.Q4_K_M.gguf
LOCAL_LLM_MODEL=Meta-Llama-3.1-8B-Instruct.Q4_K_M
LOCAL_LLM_BASE_URL=http://localhost:8080/v1
LOCAL_LLM_API_KEY=not-needed
```

---

## ⚡ Quantization Guide (Which file to download?)

GGUF models come in different quantization levels (bits), marked in the filename (e.g. `q4_k_m`, `q5_k_m`). Selecting the correct quantization is key to preventing out-of-memory crashes on server nodes:

*   **`Q4_K_M` (4-bit, Medium) - *Recommended Default***:
    *   **RAM Required**: ~1.5x model size.
    *   **Trade-off**: Fast inference, low resource consumption, and minimal quality loss.
*   **`Q5_K_M` (5-bit, Medium)**:
    *   **Trade-off**: Slightly slower than 4-bit, but has marginally better reasoning accuracy.
*   **`Q8_0` (8-bit, High)**:
    *   **Trade-off**: Lossless quality, but slower and double the memory requirement. Not recommended for quick testing on normal CPU nodes.
