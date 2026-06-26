#!/usr/bin/env python3
"""inventory_metadata.py — 列出低代码应用资产清单（应用根目录下，新结构去掉 metadata 层）.

兼容老结构：若传入路径下直接有 codeitem/mis/... 子目录，按新结构处理；
若传入路径形如 `<apptag>/metadata/`，也能识别（向后兼容）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import json_load, print_err, print_warn, yaml_load  # noqa: E402


ASSET_DIRS = ["codeitem", "mis", "module", "event", "api", "workflow", "page"]


def load_any(path: Path):
    try:
        if path.suffix.lower() == ".json":
            return json_load(path)
        return yaml_load(path)
    except Exception:
        return None


def clean_name(path: Path) -> str:
    return re.sub(r"\.(codeitem|mis|module|event|workflow|page|api)$", "", path.stem)


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
        elif asset_type == "page":
            item["name"] = data.get("title") or item["name"]
            item["pageId"] = data.get("pageId") or data.get("id")
            item["nodeCount"] = len(data.get("children") or [])
    return item


def inventory(app_root: Path) -> dict:
    result = {
        "appRoot": str(app_root),
        "appinfo": str(app_root / "appinfo.lowcode.yml") if (app_root / "appinfo.lowcode.yml").is_file() else None,
        "assets": {asset_type: [] for asset_type in ASSET_DIRS},
    }
    for asset_type in ASSET_DIRS:
        asset_dir = app_root / asset_type
        if not asset_dir.is_dir():
            continue
        patterns = ["*.json"] if asset_type == "page" else ["*.yml", "*.yaml"]
        for pattern in patterns:
            for path in sorted(asset_dir.glob(pattern)):
                result["assets"][asset_type].append(summarize_file(asset_type, path))
    return result


def print_text(data: dict) -> None:
    print(f"appRoot: {data['appRoot']}")
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
    parser = argparse.ArgumentParser(description="列出应用资产清单（新结构去掉 metadata 层）")
    parser.add_argument("--app-root", "--metadata", dest="app_root", required=True,
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir():
        print_err(f"应用根目录不存在: {app_root}")
        return 1
    # 兼容老结构：若传入路径自身名字是 metadata 且其内部含 codeitem/mis/...，给提示但仍按它处理
    if app_root.name == "metadata":
        print_warn(
            f"检测到老结构路径 {app_root}（结尾是 metadata/）。新结构已去掉 metadata 层，"
            "建议传入 <apptag>/ 而非 <apptag>/metadata/。本次按老结构兼容处理。"
        )
    data = inventory(app_root)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
