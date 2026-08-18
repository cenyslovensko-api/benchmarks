"""Shared storage helpers for benchmark data.

Layout::

    docs/data/index.json                  – {"clients": ["go", "python", ...]}
    docs/data/<client>/index.json         – {"client": "...", "benchmarks": [...]}
    docs/data/<client>/<benchmark>.json   – {"name": "...", "client": "...", "entries": [...]}
"""
import datetime
import json
import os
import re

_SAFE_RE = re.compile(r"[^a-zA-Z0-9_\-.]")


def safe(name: str) -> str:
    result = _SAFE_RE.sub("_", name)
    if not result:
        raise ValueError(f"Name {name!r} produces an empty path component.")
    return result


def load_json(path: str, default: dict) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _update_list_index(path: str, list_key: str, value: str) -> None:
    data = load_json(path, {list_key: []})
    if value not in data[list_key]:
        data[list_key].append(value)
        data[list_key].sort()
    save_json(path, data)


def record_entry(
    data_dir: str,
    client: str,
    benchmark: str,
    value: float,
    unit: str,
    repository: str = "",
    commit: str = "",
    timestamp: str = "",
) -> None:
    """Write one benchmark data point and update both index files."""
    if not timestamp:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    client_dir = os.path.join(data_dir, safe(client))

    _update_list_index(os.path.join(data_dir, "index.json"), "clients", client)
    _update_list_index(os.path.join(client_dir, "index.json"), "benchmarks", benchmark)

    metric_path = os.path.join(client_dir, safe(benchmark) + ".json")
    metric_data = load_json(metric_path, {"name": benchmark, "client": client, "entries": []})

    entry: dict = {"timestamp": timestamp, "value": value, "unit": unit}
    if repository:
        entry["repository"] = repository
    if commit:
        entry["commit"] = commit

    metric_data["entries"].append(entry)
    save_json(metric_path, metric_data)
