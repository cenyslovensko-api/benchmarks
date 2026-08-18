#!/usr/bin/env python3
"""Append a single benchmark data point to the per-client, per-metric store.

Data layout:
  docs/data/index.json                    – manifest: {"clients": ["python", "go", ...]}
  docs/data/<client>/index.json           – {"client": "<client>", "benchmarks": ["latency", ...]}
  docs/data/<client>/<benchmark>.json     – {"name": "...", "client": "...", "entries": [...]}

For submitting multiple metrics at once, use bulk_upload.py instead.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _storage import record_entry  # noqa: E402

DATA_DIR_DEFAULT = "docs/data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a single benchmark data point.")
    parser.add_argument("--client", required=True, help="Client/app name (e.g. python, go, rust)")
    parser.add_argument("--benchmark", required=True, help="Benchmark metric name")
    parser.add_argument("--value", type=float, required=True, help="Numeric value")
    parser.add_argument("--unit", required=True, help="Unit of measurement (e.g. ms, req/s, MB)")
    parser.add_argument("--repository", default="", help="Source repository (e.g. org/repo)")
    parser.add_argument("--commit", default="", help="Source commit SHA")
    parser.add_argument(
        "--data-dir",
        default=DATA_DIR_DEFAULT,
        help="Root data directory (default: docs/data)",
    )
    args = parser.parse_args()

    record_entry(
        data_dir=args.data_dir,
        client=args.client,
        benchmark=args.benchmark,
        value=args.value,
        unit=args.unit,
        repository=args.repository,
        commit=args.commit,
    )
    print(f"✓ Recorded [{args.client}] {args.benchmark} = {args.value} {args.unit}")


if __name__ == "__main__":
    main()
