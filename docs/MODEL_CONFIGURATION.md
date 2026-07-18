# Custom Model Configuration Guide

Our scripts and environment templates are fully decoupled from hardcoded models. This guide details how local models are served and consumed dynamically without static configuration files.

---

## 🛠️ Environment Configuration & Dynamic Selection

1. **Connection & Runtime Settings** are defined statically in the project root `.env` file.
2. **Server Model Selection** happens dynamically when launching the model server.
3. **Python client discovery** queries the running local server endpoint `/v1/models` to discover which model is active.

### `.env` Variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | The LLM provider type (e.g. `local` or `gemini`). | `local` |
| `LLM_SERVER_HOST` | Local server network interface host IP. | `0.0.0.0` |
| `LLM_SERVER_PORT` | Local server network port. | `1234` |
| `LLM_SERVER_N_CTX` | Context window token size for candidate algorithm evolution. | `8192` |
| `LLM_SERVER_N_THREADS` | Number of CPU threads assigned to model inference. | `8` |

---

## 📋 Serving a Model

To start the model server, run the LLM Server management script:

```bash
bash scripts/llm_server.sh start
```

If multiple GGUF models are found in your `~/models` directory, the script will show an interactive selection menu allowing you to choose which model to start:

```
Select a GGUF model to serve:
1) qwen2.5-coder-7b-instruct-q4_k_m.gguf
2) deepseek-coder-1.5b-instruct-q4_k_m.gguf
3) Cancel
```

Once running, the active model name can be verified dynamically using:

```bash
bash scripts/llm_server.sh status
```

---

## 💾 Downloading and Managing Models

To download or clean up GGUF model files, use the Cache Manager script:

```bash
bash scripts/llm_manage.sh
```

This interactive tool lets you:
1. **Select and download a model preset**: Shows a categorised list of optimized models (from `configs/llms.toml`) and downloads the selection to `~/models`.
2. **Download from custom Hugging Face repo & file**: Prompts for repository ID and GGUF file name, and downloads it to `~/models`.
3. **Delete downloaded models**: Clean up cache disk space.
4. **List local cached models**: View cached GGUF models.

---

## ⚡ Quantization Guide (Which file to download?)

GGUF models come in different quantization levels (bits), marked in the filename (e.g. `q4_k_m`, `q5_k_m`). Selecting the correct quantization is key to preventing out-of-memory crashes:

*   **`Q4_K_M` (4-bit, Medium) - *Recommended Default***:
    *   **RAM Required**: ~1.5x model size.
    *   **Trade-off**: Fast inference, low resource consumption, and minimal quality loss.
*   **`Q5_K_M` (5-bit, Medium)**:
    *   **Trade-off**: Slightly slower than 4-bit, but has marginally better reasoning accuracy.
*   **`Q8_0` (8-bit, High)**:
    *   **Trade-off**: Lossless quality, but slower and double the memory requirement. Not recommended for quick testing on normal CPU nodes.
