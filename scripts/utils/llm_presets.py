#!/usr/bin/env python3
"""
llm_presets.py
Helper CLI for parsing LLM TOML presets, Hugging Face downloads, and server queries.
"""

import argparse
import json
import sys
from pathlib import Path

def parse_toml_fallback(content: str) -> dict:
    """Fallback parser for configs/llms.toml if tomllib is unavailable."""
    data = {}
    current_section = None
    current_obj = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[[') and line.endswith(']]'):
            header = line[2:-2].strip()
            parts = header.split('.')
            section = parts[0]
            if section not in data:
                data[section] = {'llms': []}
            current_obj = {}
            data[section]['llms'].append(current_obj)
            current_section = None
        elif line.startswith('[') and line.endswith(']'):
            header = line[1:-1].strip()
            if header not in data:
                data[header] = {'llms': []}
            current_section = header
            current_obj = None
        elif '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if current_obj is not None:
                current_obj[k] = v
            elif current_section is not None:
                data[current_section][k] = v
    return data


def load_toml(toml_path: str) -> dict:
    path = Path(toml_path)
    if not path.is_file():
        sys.stderr.write(f"Error: Preset file not found: {toml_path}\n")
        sys.exit(1)
        
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        with open(path, "r", encoding="utf-8") as f:
            return parse_toml_fallback(f.read())


def cmd_list_categories(args):
    data = load_toml(args.toml)
    categories = []
    for cat_name, cat_data in data.items():
        desc = cat_data.get("description", "")
        categories.append({"name": cat_name, "description": desc})
    print(json.dumps(categories))


def cmd_list_models(args):
    data = load_toml(args.toml)
    filtered = data.get(args.category, {}).get("llms", [])
    print(json.dumps(filtered))


def cmd_download(args):
    try:
        from huggingface_hub import hf_hub_download
        cache_path = hf_hub_download(repo_id=args.repo, filename=args.file)
        print(cache_path)
    except Exception as e:
        sys.stderr.write(f"Error downloading model: {e}\n")
        sys.exit(1)


def cmd_get_active_model(args):
    import urllib.request
    models_url = f"{args.url.rstrip('/')}/models"
    try:
        req = urllib.request.Request(models_url, headers={"User-Agent": "AAD-LLM-Model-Check"})
        with urllib.request.urlopen(req, timeout=args.timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                model_id = payload.get("data", [{}])[0].get("id", "(unknown)")
                print(model_id)
                return
    except Exception:
        pass
    print("(none/server offline)")


def main():
    parser = argparse.ArgumentParser(description="LLM Presets and API Helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-categories
    p_cats = subparsers.add_parser("list-categories")
    p_cats.add_argument("--toml", default="configs/llms.toml", help="Path to llms.toml")

    # list-models
    p_models = subparsers.add_parser("list-models")
    p_models.add_argument("--category", required=True, help="Category name")
    p_models.add_argument("--toml", default="configs/llms.toml", help="Path to llms.toml")

    # download
    p_dl = subparsers.add_parser("download")
    p_dl.add_argument("--repo", required=True, help="Hugging Face repo ID")
    p_dl.add_argument("--file", required=True, help="GGUF filename")

    # get-active-model
    p_act = subparsers.add_parser("get-active-model")
    p_act.add_argument("--url", default="http://localhost:1234/v1", help="Server base URL")
    p_act.add_argument("--timeout", type=float, default=2.0, help="HTTP timeout")

    args = parser.parse_args()

    if args.command == "list-categories":
        cmd_list_categories(args)
    elif args.command == "list-models":
        cmd_list_models(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "get-active-model":
        cmd_get_active_model(args)


if __name__ == "__main__":
    main()
