#!/usr/bin/env python3
"""
Environment and LLM connection check for the AAD_LLM framework.
Checks dependencies, env vars, connection to LLM server, and problem executor sanity.
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_ok(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")


def print_failed(msg: str):
    print(f"{RED}[FAILED]{RESET} {msg}")


def print_warning(msg: str):
    print(f"{YELLOW}[WARNING]{RESET} {msg}")


def run_diagnostics(exit_on_failure: bool = True) -> bool:
    print("=" * 65)
    print(f"{BOLD}{BLUE}AAD_LLM Framework Health & Diagnostics Check{RESET}")
    print("=" * 65)

    # 1. Resolve Project Root
    project_root = Path(__file__).resolve().parent.parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    print(f"Project Root: {project_root}")
    print(f"Source Dir:   {src_path}")
    print("-" * 65)

    has_errors = False

    # 2. Check Python Dependencies
    print(f"{BOLD}Stage 1: Python Dependencies Check{RESET}")
    deps = ["numpy", "scipy", "ioh", "func_timeout", "joblib", "llamea", "openai"]
    for dep in deps:
        try:
            mod = __import__(dep)
            version = getattr(mod, "__version__", "N/A")
            print_ok(f"Dependency '{dep}' successfully imported (Version: {version})")
        except ImportError as e:
            print_failed(f"Dependency '{dep}' is missing: {e}")
            has_errors = True
    print("-" * 65)

    # 3. Environment Variables Resolution
    print(f"{BOLD}Stage 2: Environment Variables Check{RESET}")
    # Load defaults if not set, matching notebooks / runners behavior
    os.environ.setdefault("LLM_PROVIDER", "local")
    os.environ.setdefault("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
    os.environ.setdefault("LOCAL_LLM_MODEL", "qwen2.5-coder-1.5b-instruct-q4_k_m")
    os.environ.setdefault("LOCAL_LLM_API_KEY", "not-needed")

    provider = os.environ.get("LLM_PROVIDER")
    print(f"  LLM_PROVIDER:       {provider}")

    if provider in ["local", "lmstudio"]:
        base_url = os.environ.get(
            "LOCAL_LLM_BASE_URL" if provider == "local" else "LLM_STUDIO_BASE_URL"
        )
        model_name = os.environ.get(
            "LOCAL_LLM_MODEL" if provider == "local" else "LLM_STUDIO_MODEL"
        )
        print(f"  Endpoint Base URL:  {base_url}")
        print(f"  Model Name:         {model_name}")
    elif provider == "gemini":
        base_url = "https://generativelanguage.googleapis.com"
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        print(f"  Endpoint Base URL:  {base_url}")
        print(f"  Model Name:         {model_name}")
        if "GOOGLE_API_KEY" not in os.environ:
            print_warning("GOOGLE_API_KEY environment variable is not defined.")
    else:
        base_url = None
        model_name = None
        print_warning(f"Unknown provider '{provider}' configured.")
    print("-" * 65)

    # 4. Connection & Models Endpoint Check
    server_online = True
    if provider in ["local", "lmstudio"] and base_url:
        print(f"{BOLD}Stage 3: LLM Server Endpoint Connection Check{RESET}")
        models_url = f"{base_url.rstrip('/')}/models"
        print(f"Sending HTTP GET request to: {models_url} ...")
        try:
            start_t = time.time()
            req = urllib.request.Request(models_url, headers={"User-Agent": "AAD-LLM-Health-Check"})
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                body = json.loads(response.read().decode("utf-8"))
                elapsed = time.time() - start_t
            print_ok(f"Server responded in {elapsed:.3f} seconds (status: {status})")

            # Check if target model is loaded / available in the server list
            available_models = [m.get("id") for m in body.get("data", []) if isinstance(m, dict)]
            print(f"  Available models in server: {available_models}")
            if model_name in available_models:
                print_ok(f"Target model '{model_name}' is loaded and ready!")
            else:
                print_warning(
                    f"Target model '{model_name}' was not found in the list of available models. "
                    "Make sure it is loaded in the server UI or config file."
                )
        except Exception as e:
            print_failed(f"HTTP Connection failed: {e}")
            print(f"\n{YELLOW}Troubleshooting:{RESET}")
            print(
                "  1. Is your model server running? (Start it using: bash scripts/03_serve_model.sh)"
            )
            print(f"  2. Check if port is correct: {base_url}")
            print("  3. Check if your proxy or VPN is interfering with localhost endpoints.")
            has_errors = True
            server_online = False
        print("-" * 65)

    # 5. Build LLM & Run test completion
    print(f"{BOLD}Stage 4: LLM Client Query Sanity Check{RESET}")
    if provider in ["local", "lmstudio"] and not server_online:
        print_warning("Skipping LLM completion query because the server is offline.")
        has_errors = True
    else:
        try:
            from llm.providers import get_llm_client

            llm = get_llm_client(provider)
            test_messages = [{"role": "user", "content": "Return exactly the word: hello"}]
            print("Sending simple 1-token query completion check...")
            start_t = time.time()
            response_text = llm.query(test_messages)
            elapsed = time.time() - start_t
            print_ok(f"LLM responded in {elapsed:.3f}s: '{response_text.strip()}'")
        except Exception as e:
            print_failed(f"LLM Client query execution failed: {e}")
            has_errors = True
    print("-" * 65)

    # 7. Final Status Report
    if has_errors:
        print(f"\n{BOLD}{RED}❌ HEALTH CHECK FAILED.{RESET}")
        print("Please address the issues highlighted in red above before continuing.")
        if exit_on_failure:
            sys.exit(1)
        return False
    else:
        print(f"\n{BOLD}{GREEN}✔ HEALTH CHECK PASSED. YOU CAN KEEP GOING!{RESET}")
        if exit_on_failure:
            sys.exit(0)
        return True


if __name__ == "__main__":
    run_diagnostics(exit_on_failure=True)
