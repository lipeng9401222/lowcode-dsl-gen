#!/usr/bin/env python3
"""workflow_preview.py - 输出工作流业务节点 Mermaid 预览.

规划阶段用它让用户确认流程意图；默认隐藏引擎节点“开始/结束/浏览”。
支持从 activities JSON、lowcode-dsl-gen IR 或已生成的 workflow yml 提取。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import print_err, yaml_load  # noqa: E402


ENGINE_NAMES = {"开始", "结束", "浏览"}


def _node_id(name: str, index: int) -> str:
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    if not slug or slug[0].isdigit():
        slug = f"n{index}"
    return slug


def _mermaid_from_names(names: list[str]) -> str:
    lines = ["flowchart LR"]
    if not names:
        lines.append('  empty["未识别到业务节点"]')
        return "\n".join(lines)
    ids = [_node_id(name, i + 1) for i, name in enumerate(names)]
    for node_id, name in zip(ids, names):
        lines.append(f'  {node_id}["{name}"]')
    for prev_id, next_id in zip(ids, ids[1:]):
        lines.append(f"  {prev_id} --> {next_id}")
    return "\n".join(lines)


def _find_ir_asset(ir: dict, asset_id: str | None) -> dict:
    assets = ir.get("assets") or []
    candidates = [a for a in assets if isinstance(a, dict) and a.get("type") == "workflow"]
    if asset_id:
        candidates = [a for a in candidates if a.get("id") == asset_id]
    if len(candidates) != 1:
        raise ValueError("IR 中 workflow asset 数量不是 1，请传 --asset-id")
    return candidates[0]


def preview_from_ir(path: Path, asset_id: str | None) -> str:
    asset = _find_ir_asset(yaml_load(path), asset_id)
    spec = asset.get("spec") or {}
    names = [
        str(item.get("name") or item.get("activityname"))
        for item in spec.get("activities") or []
        if isinstance(item, dict)
        and (item.get("name") or item.get("activityname"))
        and str(item.get("name") or item.get("activityname")) not in ENGINE_NAMES
    ]
    return _mermaid_from_names(names)


def preview_from_activities_json(raw_json: str) -> str:
    try:
        activities = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--activities-json 不是合法 JSON: {exc}") from exc
    if not isinstance(activities, list):
        raise ValueError("--activities-json 必须是数组")
    names = []
    for index, item in enumerate(activities, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"--activities-json[{index}] 必须是对象")
        name = str(item.get("name") or item.get("activityname") or "").strip()
        if name and name not in ENGINE_NAMES:
            names.append(name)
    return _mermaid_from_names(names)


def preview_from_workflow(path: Path) -> str:
    data = yaml_load(path)
    wf = data.get("workFlow") or {}
    version = wf.get("workflowVersion") or {}
    activities = version.get("activity") or []
    transitions = version.get("transition") or []

    by_guid = {
        item.get("activityguid"): item
        for item in activities
        if isinstance(item, dict) and item.get("activityguid")
    }
    outgoing = {}
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        source = transition.get("fromactivityguid")
        target = transition.get("toactivityguid")
        if not source or not target:
            continue
        outgoing.setdefault(source, []).append(target)

    apply = next(
        (
            item
            for item in activities
            if isinstance(item, dict)
            and item.get("activitytype") == 30
            and item.get("activityname") not in ENGINE_NAMES
        ),
        None,
    )
    names = []
    seen = set()
    current = apply.get("activityguid") if apply else None
    while current and current not in seen:
        seen.add(current)
        activity = by_guid.get(current)
        if not activity:
            break
        name = activity.get("activityname")
        if name and name not in ENGINE_NAMES:
            names.append(str(name))
        next_candidates = [
            guid
            for guid in outgoing.get(current, [])
            if (by_guid.get(guid) or {}).get("activityname") != "结束"
            and (by_guid.get(guid) or {}).get("activityname") != "浏览"
        ]
        current = next_candidates[0] if next_candidates else None

    if not names:
        names = [
            str(item.get("activityname"))
            for item in activities
            if isinstance(item, dict)
            and item.get("activityname")
            and item.get("activityname") not in ENGINE_NAMES
        ]
    return _mermaid_from_names(names)


def cli() -> int:
    parser = argparse.ArgumentParser(description="输出 workflow 简易 Mermaid 预览")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--activities-json", help="目标业务活动数组 JSON；规划阶段可不依赖 IR 生成预览")
    source.add_argument("--from-ir", help="lowcode-dsl-gen IR 文件")
    source.add_argument("--workflow-file", help="已有 .workflow.yml 文件")
    parser.add_argument("--asset-id", help="IR 中 workflow asset id；多个 workflow 时必填")
    args = parser.parse_args()
    try:
        if args.activities_json:
            print(preview_from_activities_json(args.activities_json))
        elif args.from_ir:
            print(preview_from_ir(Path(args.from_ir).resolve(), args.asset_id))
        else:
            print(preview_from_workflow(Path(args.workflow_file).resolve()))
    except Exception as exc:
        print_err(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(cli())
