"""Print the most recently updated workflow diagnostic log without finding its dated folder."""

import argparse
from collections import deque
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=("evolution", "benchmark"), default="evolution")
    parser.add_argument("--lines", type=int, default=40)
    args = parser.parse_args(argv)
    if args.lines < 1:
        parser.error("--lines must be positive")
    directory = Path(__file__).resolve().parents[1] / "logs" / args.workflow
    files = directory.glob("*/diagnostics.log")
    latest = max(files, key=lambda path: path.stat().st_mtime_ns, default=None)
    if latest is None:
        print(f"No diagnostic logs found in {directory}.")
        return 1
    print(f"Most recently updated log: {latest}", flush=True)
    with latest.open(encoding="utf-8", errors="replace") as stream:
        print("".join(deque(stream, maxlen=args.lines)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
