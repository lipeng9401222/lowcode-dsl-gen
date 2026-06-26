#!/usr/bin/env python3
"""ir_to_event_args.py — 将 event IR 片段转换为 add_event.py 参数 JSON."""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _common import print_err, yaml_load  # noqa: E402


def _find_asset(ir: dict, asset_id: str | None) -> dict:
    assets = ir.get("assets") or []
    candidates = [a for a in assets if isinstance(a, dict) and a.get("type") == "event"]
    if asset_id:
        for asset in candidates:
            if asset.get("id") == asset_id:
                return asset
        raise ValueError(f"找不到 event asset: {asset_id}")
    if len(candidates) != 1:
        raise ValueError("IR 中 event asset 数量不是 1，请传 --asset-id")
    return candidates[0]


def event_args_from_ir(ir: dict, asset_id: str | None = None) -> dict[str, Any]:
    app = ir.get("application") or {}
    asset = _find_asset(ir, asset_id)
    spec = asset.get("spec") or {}
    args = {
        "name": spec.get("name"),
        "sign": spec.get("sign"),
        "apptag": spec.get("apptag") or app.get("apptag"),
        "biz_action": spec.get("bizAction") or spec.get("biz_action"),
        "biz_title": spec.get("bizTitle") or spec.get("biz_title") or "业务执行",
        "context_class": spec.get("contextClass") or spec.get("context_class"),
        "webhook_url": spec.get("webhookUrl") or spec.get("webhook_url") or "",
        "filename": spec.get("filename") or "",
    }
    for key in ("name", "sign", "apptag", "biz_action", "context_class"):
        if not args.get(key):
            raise ValueError(f"event.spec 缺少标准三段式参数: {key}")
    return args


def to_cli_args(args: dict[str, Any]) -> list[str]:
    mapping = {
        "name": "--name",
        "sign": "--sign",
        "apptag": "--apptag",
        "biz_action": "--biz-action",
        "biz_title": "--biz-title",
        "context_class": "--context-class",
        "webhook_url": "--webhook-url",
        "filename": "--filename",
    }
    result: list[str] = []
    for key, flag in mapping.items():
        value = args.get(key)
        if value in (None, ""):
            continue
        result.extend([flag, str(value)])
    return result


def cli() -> int:
    parser = argparse.ArgumentParser(description="event IR -> add_event.py 参数")
    parser.add_argument("ir", help="IR yaml 文件")
    parser.add_argument("--asset-id", help="event asset id；多个 event 时必填")
    parser.add_argument("--format", choices=["json", "shell"], default="json")
    args = parser.parse_args()
    try:
        ir = yaml_load(Path(args.ir))
        converted = event_args_from_ir(ir, args.asset_id)
    except Exception as exc:
        print_err(str(exc))
        return 1
    if args.format == "shell":
        print(" ".join(shlex.quote(x) for x in to_cli_args(converted)))
    else:
        print(json.dumps(converted, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
