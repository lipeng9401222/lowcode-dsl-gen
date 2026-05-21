#!/usr/bin/env python3
"""inventory_metadata.py — 列出低代码应用 metadata 目录内的资产清单."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import json_load, print_err, yaml_load  # noqa: E402


ASSET_DIRS = ["codeitem", "mis", "module", "event", "api", "workflow", "pagedesigne"]


def load_any(path: Path):
    try:
        if path.suffix.lower() == ".json":
            return json_load(path)
        return yaml_load(path)
    except Exception:
        return None


def clean_name(path: Path) -> str:
    return re.sub(r"\.(codeitem|mis|module|event|workflow|pagedesigne|api)$", "", path.stem)


def summarize_file(asset_type: str, path: Path) -> dict:
    data = load_any(path)
    item = {
        "file": str(path),
        "filename": path.name,
        "assetType": asset_type,
        "name": clean_name(path),
    }
    if isinstance(data, dict):
        if asset_type == "codeitem":
            item["name"] = data.get("name") or item["name"]
            item["itemCount"] = len(data.get("items") or [])
        elif asset_type == "mis":
            item["name"] = data.get("tableName") or data.get("name") or item["name"]
            item["fieldCount"] = len(data.get("fields") or [])
        elif asset_type == "module":
            item["name"] = data.get("name") or item["name"]
            item["code"] = data.get("code")
            item["subModuleCount"] = len(data.get("items") or [])
        elif asset_type == "event":
            app = data.get("app") or {}
            item["name"] = app.get("name") or app.get("sign") or item["name"]
            item["sign"] = app.get("sign")
        elif asset_type == "workflow":
            wf = data.get("workFlow") or data.get("WorkFlow") or {}
            process = wf.get("workflowProcess") or wf.get("WorkflowProcess") or {}
            item["name"] = process.get("processname") or process.get("processName") or item["name"]
        elif asset_type == "pagedesigne":
            item["name"] = data.get("title") or item["name"]
            item["pageId"] = data.get("id")
            item["nodeCount"] = len(data.get("children") or [])
    return item


def inventory(metadata_dir: Path) -> dict:
    result = {
        "metadata": str(metadata_dir),
        "appinfo": str(metadata_dir / "appinfo.lowcode.yml") if (metadata_dir / "appinfo.lowcode.yml").is_file() else None,
        "assets": {asset_type: [] for asset_type in ASSET_DIRS},
    }
    for asset_type in ASSET_DIRS:
        asset_dir = metadata_dir / asset_type
        if not asset_dir.is_dir():
            continue
        patterns = ["*.yml", "*.yaml", "*.json"] if asset_type == "pagedesigne" else ["*.yml", "*.yaml"]
        for pattern in patterns:
            for path in sorted(asset_dir.glob(pattern)):
                result["assets"][asset_type].append(summarize_file(asset_type, path))
    return result


def print_text(data: dict) -> None:
    print(f"metadata: {data['metadata']}")
    print(f"appinfo: {data['appinfo'] or '缺失'}")
    for asset_type in ASSET_DIRS:
        items = data["assets"][asset_type]
        print(f"{asset_type}: {len(items)}")
        for item in items:
            detail = item["name"]
            if item.get("code"):
                detail += f" (code={item['code']})"
            if item.get("sign"):
                detail += f" (sign={item['sign']})"
            if item.get("pageId"):
                detail += f" (id={item['pageId']})"
            print(f"  - {detail} :: {item['filename']}")


def cli():
    parser = argparse.ArgumentParser(description="列出 metadata 资产清单")
    parser.add_argument("--metadata", required=True, help="metadata 目录路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    metadata_dir = Path(args.metadata).resolve()
    if not metadata_dir.is_dir():
        print_err(f"metadata 目录不存在: {metadata_dir}")
        return 1
    data = inventory(metadata_dir)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
