#!/usr/bin/env python3
"""
llm_presets.py
Helper CLI for parsing LLM TOML presets, Hugging Face downloads, server queries,
and scanning/sorting local cached models by parameter size and disk usage.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ─── Colors ────────────────────────────────────────────────
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


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


# ─── Model Scanning & Sorting ─────────────────────────────────

def extract_param_size(name: str) -> tuple[float | None, str]:
    """Extract parameter count in billions from model name (e.g. '1.5B' -> 1.5, '7B' -> 7.0)."""
    match = re.search(r'(?:^|[^0-9a-zA-Z])([0-9]+(?:\.[0-9]+)?)[bB](?:[^0-9a-zA-Z]|$)', name)
    if match:
        val = float(match.group(1))
        tag = f"{val:g}B"
        return val, tag
    return None, ""


def get_path_size(path: Path) -> int:
    """Calculates size in bytes of a file or directory tree."""
    if not path.exists():
        return 0
    if path.is_file() or path.is_symlink():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    try:
        for p in path.rglob('*'):
            if p.is_file() and not p.is_symlink():
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def format_size_bytes(bytes_val: int) -> str:
    if bytes_val >= 1024**3:
        return f"{bytes_val / (1024**3):.2f} GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / (1024**2):.1f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.0f} KB"
    else:
        return f"{bytes_val} B"


def shorten_path(path_str: str) -> str:
    home_dir = str(Path.home())
    if path_str.startswith(home_dir):
        return "~" + path_str[len(home_dir):]
    return path_str


def cmd_scan_models(args):
    target_dir = Path(os.path.expanduser(args.target_dir))
    hf_cache_dir = Path(os.path.expanduser(args.hf_cache_dir))

    models = []
    seen_paths = set()

    # 1. Scan target directory (~/models)
    if target_dir.is_dir():
        if args.gguf_only:
            items = list(target_dir.glob("*.gguf"))
        else:
            items = [p for p in target_dir.iterdir() if p.name != ".DS_Store"]

        for item in items:
            abs_path = str(item.resolve())
            if abs_path in seen_paths:
                continue
            seen_paths.add(abs_path)

            raw_name = item.name
            param_val, param_tag = extract_param_size(raw_name)
            size_bytes = get_path_size(item)

            models.append({
                "source": "Local File / Symlink",
                "name": raw_name,
                "display_name": raw_name,
                "param_val": param_val,
                "param_tag": param_tag,
                "size_bytes": size_bytes,
                "size_formatted": format_size_bytes(size_bytes),
                "path": str(item),
                "short_path": shorten_path(str(item))
            })

    # 2. Scan Hugging Face cache
    if hf_cache_dir.is_dir():
        if args.gguf_only:
            items = list(hf_cache_dir.rglob("*.gguf"))
            for item in items:
                abs_path = str(item.resolve())
                if abs_path in seen_paths:
                    continue
                seen_paths.add(abs_path)

                raw_name = item.name
                param_val, param_tag = extract_param_size(raw_name)
                size_bytes = get_path_size(item)

                models.append({
                    "source": "Hugging Face Cache",
                    "name": raw_name,
                    "display_name": raw_name,
                    "param_val": param_val,
                    "param_tag": param_tag,
                    "size_bytes": size_bytes,
                    "size_formatted": format_size_bytes(size_bytes),
                    "path": str(item),
                    "short_path": shorten_path(str(item))
                })
        else:
            items = list(hf_cache_dir.glob("models--*"))
            for item in items:
                abs_path = str(item.resolve())
                if abs_path in seen_paths:
                    continue
                seen_paths.add(abs_path)

                clean_name = item.name.replace("models--", "").replace("--", "/")
                param_val, param_tag = extract_param_size(clean_name)
                size_bytes = get_path_size(item)

                models.append({
                    "source": "Hugging Face Cache",
                    "name": item.name,
                    "display_name": clean_name,
                    "param_val": param_val,
                    "param_tag": param_tag,
                    "size_bytes": size_bytes,
                    "size_formatted": format_size_bytes(size_bytes),
                    "path": str(item),
                    "short_path": shorten_path(str(item))
                })

    # Sort models by parameter count ascending (0.5B -> 1.5B -> 7B -> 14B -> 32B), then by disk size
    models.sort(key=lambda m: (
        m["param_val"] if m["param_val"] is not None else float("inf"),
        m["size_bytes"],
        m["display_name"].lower()
    ))

    # Add 1-based index
    for idx, m in enumerate(models, 1):
        m["index"] = idx

    if args.format == "json":
        print(json.dumps(models))
        return

    # Formatted Card output
    if not models:
        print(f"  {GREEN}✓ No models found in scanned directories.{NC}\n")
        return

    print(f"  {CYAN}[i] Scanned & Sorted Local Models ({len(models)} total):{NC}")
    print(f"  {CYAN}----------------------------------------------------------------------{NC}")

    for m in models:
        idx_str = f"[{m['index']:2d}]"
        param_str = f" ({YELLOW}{m['param_tag']}{NC})" if m['param_tag'] else ""
        print(f"  {CYAN}{BOLD}{idx_str}{NC} {BOLD}{m['display_name']}{NC}{param_str}")
        print(f"       • {BOLD}Source:{NC}    {m['source']}")
        print(f"       • {BOLD}Disk Size:{NC} {GREEN}{m['size_formatted']}{NC}")
        print(f"       • {BOLD}Location:{NC}  {m['short_path']}")
        print("")

    print(f"  {CYAN}----------------------------------------------------------------------{NC}\n")


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

    # scan-models
    p_scan = subparsers.add_parser("scan-models")
    p_scan.add_argument("--target-dir", default="~/models", help="Target models directory")
    p_scan.add_argument("--hf-cache-dir", default="~/.cache/huggingface/hub", help="HF cache directory")
    p_scan.add_argument("--gguf-only", action="store_true", help="Scan GGUF files only for serving")
    p_scan.add_argument("--format", choices=["card", "json"], default="json", help="Output format")

    args = parser.parse_args()

    if args.command == "list-categories":
        cmd_list_categories(args)
    elif args.command == "list-models":
        cmd_list_models(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "get-active-model":
        cmd_get_active_model(args)
    elif args.command == "scan-models":
        cmd_scan_models(args)


if __name__ == "__main__":
    main()
