#!/usr/bin/env python3
"""Bulk-upload a full benchmark suite report from a JSON file.

The JSON file must conform to schemas/benchmark-report.schema.json.

Usage::

    python scripts/bulk_upload.py report.json
    python scripts/bulk_upload.py report.json --data-dir docs/data
    python scripts/bulk_upload.py --stdin          # read JSON from stdin
    echo '{"client":"go",...}' | python scripts/bulk_upload.py --stdin

All entries in the report share the same client, repository, and commit.
A single timestamp is recorded for all entries in the run (the time of
ingestion), unless the report itself carries a top-level ``timestamp`` field.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _storage import record_entry  # noqa: E402

DATA_DIR_DEFAULT = "docs/data"
SCHEMA_URL = (
    "https://raw.githubusercontent.com/cenyslovensko-api/benchmarks"
    "/main/schemas/benchmark-report.schema.json"
)


def _validate(report: dict[str, Any]) -> None:
    """Minimal structural validation without requiring jsonschema."""
    missing = [k for k in ("client", "benchmarks") if k not in report]
    if missing:
        raise ValueError(f"Report is missing required fields: {missing}")
    if not isinstance(report["benchmarks"], list) or not report["benchmarks"]:
        raise ValueError("'benchmarks' must be a non-empty array.")
    for i, entry in enumerate(report["benchmarks"]):
        missing_entry = [k for k in ("name", "value", "unit") if k not in entry]
        if missing_entry:
            raise ValueError(f"benchmarks[{i}] is missing fields: {missing_entry}")
        if not isinstance(entry["value"], (int, float)):
            raise ValueError(f"benchmarks[{i}].value must be a number, got {type(entry['value']).__name__}")


def ingest(report: dict[str, Any], data_dir: str) -> int:
    client     = report["client"]
    repository = report.get("repository", "")
    commit     = report.get("commit", "")
    timestamp  = report.get("timestamp", "")  # empty → storage uses utcnow

    count = 0
    for entry in report["benchmarks"]:
        record_entry(
            data_dir=data_dir,
            client=client,
            benchmark=entry["name"],
            value=float(entry["value"]),
            unit=entry["unit"],
            repository=repository,
            commit=commit,
            timestamp=timestamp,
        )
        print(f"  ✓ [{client}] {entry['name']} = {entry['value']} {entry['unit']}")
        count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk-upload a benchmark suite report (see schemas/benchmark-report.schema.json)."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("report_file", nargs="?", metavar="FILE", help="Path to a benchmark report JSON file.")
    source.add_argument("--stdin", action="store_true", help="Read the JSON report from stdin.")
    parser.add_argument(
        "--data-dir",
        default=DATA_DIR_DEFAULT,
        help="Root data directory (default: docs/data)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Parse and validate the report but do not write any data.",
    )
    args = parser.parse_args()

    if args.stdin:
        raw = sys.stdin.read()
        source_label = "<stdin>"
    else:
        path = Path(args.report_file)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        raw = path.read_text(encoding="utf-8")
        source_label = str(path)

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {source_label}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        _validate(report)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        print(f"✓ Report is valid ({len(report['benchmarks'])} entries for client '{report['client']}').")
        return

    print(f"Ingesting {len(report['benchmarks'])} benchmark(s) for client '{report['client']}'…")
    count = ingest(report, args.data_dir)
    print(f"\n✓ Done — {count} entries recorded.")
    print(f"  Schema: {SCHEMA_URL}")


if __name__ == "__main__":
    main()
