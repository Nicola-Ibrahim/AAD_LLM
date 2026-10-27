"""Check the real UPB gateway adapter without starting synthesis or experiments.

Run: .venv/bin/python scripts/check_upb.py
"""

import argparse
import math
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import httpx
import openai
from dotenv import load_dotenv

# Allow direct execution from a checkout without installing the project package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evolution.application.exceptions import ProviderError
from evolution.infra.llm.gateway import GatewayLLM, GatewayRequestLimiter, provider_error


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("UPB_MODEL"), help="Override UPB_MODEL.")
    parser.add_argument("--list-only", action="store_true", help="List models without generation.")
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="HTTP timeout; pacing is additional."
    )
    args = parser.parse_args(argv)
    api_key = os.getenv("UPB_API_KEY", "").strip()
    base_url = os.getenv("UPB_API_BASE", "https://ai-gateway.uni-paderborn.de/v1/").rstrip("/")
    if not api_key or not args.model:
        print("Set UPB_API_KEY and UPB_MODEL in the project .env or environment.")
        return 2
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")

    print(f"Gateway adapter: GatewayLLM\nEndpoint: {base_url}\nModel: {args.model}", flush=True)
    print("Using shared request pacing; one HTTP attempt, no automatic retries.", flush=True)
    started = time.perf_counter()
    try:
        gateway = GatewayLLM(
            api_key=api_key,
            model=args.model,
            base_url=base_url,
            limiter=GatewayRequestLimiter.for_model(base_url, args.model),
        )
        try:
            gateway.client.timeout = httpx.Timeout(args.timeout, connect=5.0)
            print("Checking GatewayLLM.client.models.list() ...", flush=True)
            models = sorted(model.id for model in gateway.client.models.list())
            print(f"Accessible models: {len(models)}", flush=True)
            if args.list_only:
                print("\n".join(models))
                return 0
            if args.model not in models:
                print(
                    "Configured model is absent from the catalogue; testing it explicitly.",
                    flush=True,
                )
            print(
                "Calling GatewayLLM.query(): 'What is 2 + 2? Reply only with the answer.'",
                flush=True,
            )
            text = gateway.query(
                [{"role": "user", "content": "What is 2 + 2? Reply only with the answer."}],
                max_retries=0,
            )
            print(
                f"Response: {text.replace(api_key, '[REDACTED]')}\n[OK] Gateway adapter succeeded."
            )
            return 0
        finally:
            gateway.client.close()
    except openai.APIError as error:
        if isinstance(error, openai.APIStatusError):
            print(f"HTTP {error.status_code}")
        print(f"[FAIL] {provider_error(error, args.model)}")
    except ProviderError as error:
        if isinstance(error.__cause__, openai.APIStatusError):
            print(f"HTTP {error.__cause__.status_code}")
        print(f"[FAIL] {error}")
    except (ValueError, KeyError, IndexError, TypeError):
        print("[FAIL] Invalid gateway configuration or unexpected response format.")
    finally:
        print(f"Elapsed: {time.perf_counter() - started:.1f}s", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
