#!/usr/bin/env python3
"""ir_to_workflow_args.py — 将 workflow IR 片段转换为 add_workflow.py 参数 JSON."""
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
    candidates = [a for a in assets if isinstance(a, dict) and a.get("type") == "workflow"]
    if asset_id:
        for asset in candidates:
            if asset.get("id") == asset_id:
                return asset
        raise ValueError(f"找不到 workflow asset: {asset_id}")
    if len(candidates) != 1:
        raise ValueError("IR 中 workflow asset 数量不是 1，请传 --asset-id")
    return candidates[0]


def workflow_args_from_ir(ir: dict, asset_id: str | None = None) -> dict[str, Any]:
    asset = _find_asset(ir, asset_id)
    spec = asset.get("spec") or {}
    activities = spec.get("activities") or []
    approvers = [
        str(a.get("name")).strip()
        for a in activities
        if isinstance(a, dict) and a.get("type") in {"approve", "route"}
    ]
    if not approvers:
        raise ValueError("workflow.spec.activities 至少需要一个 approve/route 活动")
    args: dict[str, Any] = {
        "name": spec.get("processName") or spec.get("name"),
        "approvers": ",".join(approvers),
        "material": spec.get("material") or "申请表单",
        "sql_tablename": spec.get("sqlTableName") or spec.get("sql_tablename") or "",
        "process_mode": spec.get("processMode") or spec.get("process_mode") or "normal",
        "pagetag_form": spec.get("pageTagForm") or spec.get("pagetagForm") or spec.get("pagetag_form") or "",
        "pagetag_detail": spec.get("pageTagDetail") or spec.get("pagetagDetail") or spec.get("pagetag_detail") or "",
        "methods_json": spec.get("methods") or [],
        "events_json": spec.get("events") or [],
        "contexts_json": spec.get("contexts") or [],
        "conditions_json": spec.get("conditions") or [],
        "activity_materials_json": spec.get("activityMaterials") or spec.get("activity_materials") or [],
        "activity_extra_json": spec.get("activityExtra") or spec.get("activity_extra") or [],
        "approve_pass_rate_json": spec.get("approvePassRate") or spec.get("approve_pass_rate") or [],
        "free_activities": ",".join(spec.get("freeActivities") or spec.get("free_activities") or []),
        "custom_activities": ",".join(spec.get("customActivities") or spec.get("custom_activities") or []),
        "subprocess_guid": spec.get("subprocessGuid") or spec.get("subprocess_guid") or "",
        "subprocess_name": spec.get("subprocessName") or spec.get("subprocess_name") or "子流程",
        "filename": spec.get("filename") or "",
    }
    if not args["name"]:
        raise ValueError("workflow.spec.processName 必填")
    return args


def to_cli_args(args: dict[str, Any]) -> list[str]:
    mapping = {
        "name": "--name",
        "approvers": "--approvers",
        "material": "--material",
        "sql_tablename": "--sql-tablename",
        "process_mode": "--process-mode",
        "pagetag_form": "--pagetag-form",
        "pagetag_detail": "--pagetag-detail",
        "methods_json": "--methods-json",
        "events_json": "--events-json",
        "contexts_json": "--contexts-json",
        "conditions_json": "--conditions-json",
        "activity_materials_json": "--activity-materials-json",
        "activity_extra_json": "--activity-extra-json",
        "approve_pass_rate_json": "--approve-pass-rate-json",
        "free_activities": "--free-activities",
        "custom_activities": "--custom-activities",
        "subprocess_guid": "--subprocess-guid",
        "subprocess_name": "--subprocess-name",
        "filename": "--filename",
    }
    result: list[str] = []
    for key, flag in mapping.items():
        value = args.get(key)
        if value in (None, "", [], {}):
            continue
        if key.endswith("_json"):
            value = json.dumps(value, ensure_ascii=False)
        result.extend([flag, str(value)])
    return result


def cli() -> int:
    parser = argparse.ArgumentParser(description="workflow IR -> add_workflow.py 参数")
    parser.add_argument("ir", help="IR yaml 文件")
    parser.add_argument("--asset-id", help="workflow asset id；多个 workflow 时必填")
    parser.add_argument("--format", choices=["json", "shell"], default="json")
    args = parser.parse_args()
    try:
        ir = yaml_load(Path(args.ir))
        converted = workflow_args_from_ir(ir, args.asset_id)
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
