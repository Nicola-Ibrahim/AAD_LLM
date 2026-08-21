#!/usr/bin/env python3
"""
env_check.py
Helper CLI for inspecting Python environment health, llama-cpp-python CUDA imports, etc.
"""

import argparse
import importlib.util


def cmd_check_llama_cpp():
    spec = importlib.util.find_spec("llama_cpp")
    if spec is None:
        print("NOT_INSTALLED")
    else:
        try:
            from llama_cpp import llama_cpp as lib

            _ = getattr(lib, "_lib_base_name", "unknown")
            print("FOUND")
        except OSError as e:
            print(f"LOAD_ERROR:{e}")
        except Exception as e:
            print(f"ERROR:{e}")


def main():
    parser = argparse.ArgumentParser(description="Environment Diagnostics Helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check-llama-cpp
    subparsers.add_parser("check-llama-cpp")

    args = parser.parse_args()

    if args.command == "check-llama-cpp":
        cmd_check_llama_cpp()


if __name__ == "__main__":
    main()
