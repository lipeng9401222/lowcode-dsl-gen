#!/usr/bin/env python3
"""update_workflow.py - 原地修改已有 workflow yml，保留流程 GUID 和版本标识.

用途:
    - 纠错/调整已有流程节点时使用，不能生成新的 processguid/processversionguid/version。
    - 根据目标活动链重排业务节点，保留未变化节点、按钮、变迁和配置 GUID。
    - 只有新增的真实节点、按钮、连线才生成新 GUID；删除项直接移除。

本脚本只处理规范 spec v2 结构: workFlow.workflowVersion 为单个对象。
新建流程仍使用 add_workflow.py。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _common import gen_uuid, parse_json_arg, print_err, print_info, print_ok, yaml_dump, yaml_load  # noqa: E402
from add_workflow import (  # noqa: E402
    build_approve_activity,
    build_pass_operation,
    build_reject_operation,
    build_transition,
)
from workflow_defaults import (  # noqa: E402
    FLOW_BROWSE_ICON_X,
    FLOW_BROWSE_ICON_Y,
    FLOW_END_ICON_Y,
    FLOW_MAIN_ICON_Y,
    FLOW_START_ICON_X,
    FLOW_START_ICON_Y,
    flow_iconx_sequence,
)


ENGINE_ACTIVITY_NAMES = {"开始", "结束", "浏览"}
ALLOWED_OPERATION_MODES = {"update-existing", "revise-plan"}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _workflow_parts(data: dict) -> tuple[dict, dict, dict]:
    wf = data.get("workFlow")
    if not isinstance(wf, dict):
        raise ValueError("workflow 顶层缺少 workFlow 对象")
    process = wf.get("workflowProcess")
    if not isinstance(process, dict):
        raise ValueError("workflow 缺少 workFlow.workflowProcess 对象")
    version = wf.get("workflowVersion")
    if isinstance(version, list):
        raise ValueError("workFlow.workflowVersion 必须是单个对象，不能是数组；请先迁移到 spec v2")
    if not isinstance(version, dict):
        raise ValueError("workflow 缺少 workFlow.workflowVersion 对象")
    return wf, process, version


def _process_identity(process: dict, version: dict) -> dict[str, Any]:
    pver = version.get("workflowProcessVersion")
    if not isinstance(pver, dict):
        raise ValueError("workflow 缺少 workflowVersion.workflowProcessVersion 对象")
    process_guid = process.get("processguid")
    process_version_guid = pver.get("processversionguid")
    if not process_guid:
        raise ValueError("workflowProcess.processguid 缺失")
    if not process_version_guid:
        raise ValueError("workflowProcessVersion.processversionguid 缺失")
    return {
        "processguid": process_guid,
        "processversionguid": process_version_guid,
        "version": pver.get("version"),
    }


def _load_ir_workflow_spec(ir_path: Path, asset_id: str | None) -> dict:
    ir = yaml_load(ir_path)
    assets = ir.get("assets") or []
    candidates = [a for a in assets if isinstance(a, dict) and a.get("type") == "workflow"]
    if asset_id:
        candidates = [a for a in candidates if a.get("id") == asset_id]
    if len(candidates) != 1:
        raise ValueError("IR 中 workflow asset 数量不是 1，请传 --asset-id")
    spec = candidates[0].get("spec") or {}
    return spec


def _activity_type(raw: dict) -> str:
    atype = raw.get("type")
    if atype in {"apply", "approve", "route", "subprocess"}:
        return atype
    if raw.get("activitytype") == 90:
        return "subprocess"
    return "approve"


def _target_business_activities(spec: dict, activities_json: str) -> list[dict]:
    if activities_json:
        activities = parse_json_arg(activities_json, expected_type=list, label="--activities-json")
    else:
        activities = spec.get("activities") or []
    if not isinstance(activities, list):
        raise ValueError("目标 activities 必须是数组")
    result: list[dict] = []
    for raw in activities:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or raw.get("activityname") or "").strip()
        atype = _activity_type(raw)
        if not name:
            raise ValueError("目标 activities 中存在空 name")
        if name in {"开始", "结束", "浏览"}:
            continue
        if atype not in {"apply", "approve", "route", "subprocess"}:
            raise ValueError(f"目标活动类型非法: {atype}")
        result.append({
            "name": name,
            "type": atype,
            "oldName": raw.get("oldName") or raw.get("sourceName") or raw.get("fromName") or "",
        })
    if not any(a["type"] == "apply" for a in result):
        result.insert(0, {"name": "申请", "type": "apply", "oldName": ""})
    if not any(a["type"] in {"approve", "route", "subprocess"} for a in result):
        raise ValueError("目标 activities 至少需要一个审批/路由/子流程节点")
    return result


def _rename_map(spec: dict, rename_map_json: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if spec.get("renameActivities"):
        raw = spec.get("renameActivities")
        if isinstance(raw, dict):
            mapping.update({str(k): str(v) for k, v in raw.items()})
        elif isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict) and item.get("from") and item.get("to"):
                    mapping[str(item["from"])] = str(item["to"])
    if rename_map_json:
        raw_map = parse_json_arg(rename_map_json, expected_type=dict, label="--rename-map-json")
        mapping.update({str(k): str(v) for k, v in raw_map.items()})
    return mapping


def _activity_by_name(activities: list[dict]) -> dict[str, dict]:
    return {
        str(act.get("activityname")): act
        for act in activities
        if isinstance(act, dict) and act.get("activityname")
    }


def _find_activity(activities: list[dict], *, name: str | None = None, atype: int | None = None) -> dict | None:
    for act in activities:
        if not isinstance(act, dict):
            continue
        if name is not None and act.get("activityname") != name:
            continue
        if atype is not None and act.get("activitytype") != atype:
            continue
        return act
    return None


def _extract_pagetag_from_handleurl(handleurl: str) -> str:
    match = re.search(r"[?&]pagetag=([^&]+)", handleurl or "")
    return match.group(1) if match else ""


def _next_vmlid(activities: list[dict]) -> int:
    used: list[int] = []
    for act in activities:
        try:
            value = int(act.get("vmlid"))
        except (TypeError, ValueError):
            continue
        if value >= 2:
            used.append(value)
    return (max(used) if used else 2) + 1


def _operation_guids(activities: list[dict]) -> set[str]:
    guids: set[str] = set()
    for act in activities:
        for op in _as_list(act.get("workflowActivityOperation")):
            if isinstance(op, dict) and op.get("operationguid"):
                guids.add(op["operationguid"])
    return guids


def _ensure_reject_configs(version: dict, activities: list[dict], process_version_guid: str) -> None:
    workflow_config = _as_list(version.get("workflowConfig"))
    existing_sources = {
        item.get("sourceguid")
        for item in workflow_config
        if isinstance(item, dict) and item.get("sourceguid")
    }
    live_operation_guids = _operation_guids(activities)
    cleaned = [
        item
        for item in workflow_config
        if isinstance(item, dict) and (not item.get("sourceguid") or item.get("sourceguid") in live_operation_guids)
    ]
    for act in activities:
        for op in _as_list(act.get("workflowActivityOperation")):
            if not isinstance(op, dict) or op.get("operationtype") != 30:
                continue
            op_guid = op.get("operationguid")
            if not op_guid or op_guid in existing_sources:
                continue
            cleaned.append({
                "rowguid": gen_uuid(),
                "processversionguid": process_version_guid,
                "belongto": 22,
                "configname": "backTargetScope",
                "configvalue": "1",
                "sourceguid": op_guid,
            })
            existing_sources.add(op_guid)
    version["workflowConfig"] = cleaned


def _transition_key(transition: dict) -> tuple[str, str] | None:
    from_guid = transition.get("fromactivityguid")
    to_guid = transition.get("toactivityguid")
    if not from_guid or not to_guid:
        return None
    return str(from_guid), str(to_guid)


def _rebuild_main_transitions(version: dict, seq: list[dict], process_version_guid: str) -> list[dict]:
    existing = {
        key: transition
        for transition in _as_list(version.get("transition"))
        if isinstance(transition, dict)
        for key in [_transition_key(transition)]
        if key
    }
    live_activity_guids = {act.get("activityguid") for act in seq if act.get("activityguid")}
    new_transitions: list[dict] = []
    next_vmlid = 2
    for index in range(len(seq) - 1):
        source = seq[index]
        target = seq[index + 1]
        key = (source["activityguid"], target["activityguid"])
        transition = existing.get(key)
        if transition:
            transition["processversionguid"] = process_version_guid
            transition["fromactivityguid"] = source["activityguid"]
            transition["toactivityguid"] = target["activityguid"]
            transition.setdefault("transitionname", target.get("activityname") or f"流转{index + 1}")
            transition.setdefault("transitiondispname", transition["transitionname"])
        else:
            transition = build_transition(
                from_guid=source["activityguid"],
                to_guid=target["activityguid"],
                process_version_guid=process_version_guid,
                name=target.get("activityname") or f"流转{index + 1}",
                vml_id=next_vmlid,
            )
        transition["vmlid"] = next_vmlid
        next_vmlid += 1
        new_transitions.append(transition)

    # Preserve non-main conditional/branch transitions only when both endpoints still exist.
    main_keys = {_transition_key(t) for t in new_transitions}
    for transition in _as_list(version.get("transition")):
        if not isinstance(transition, dict):
            continue
        key = _transition_key(transition)
        if not key or key in main_keys:
            continue
        if key[0] in live_activity_guids and key[1] in live_activity_guids:
            transition["processversionguid"] = process_version_guid
            if not transition.get("vmlid") or int(transition.get("vmlid", 0)) < 2:
                transition["vmlid"] = next_vmlid
                next_vmlid += 1
            new_transitions.append(transition)
    return new_transitions


def _apply_layout(start: dict, business: list[dict], end: dict, browse: dict | None) -> None:
    flow_nodes = []
    for act in business:
        flow_nodes.append((int(act.get("activitytype", 30)), str(act.get("activityname", ""))))
    flow_nodes.append((20, "结束"))
    iconxs = flow_iconx_sequence(flow_nodes)

    start["iconx"] = FLOW_START_ICON_X
    start["icony"] = FLOW_START_ICON_Y
    for index, act in enumerate(business):
        act["iconx"] = iconxs[index]
        act["icony"] = FLOW_MAIN_ICON_Y
    end["iconx"] = iconxs[len(business)]
    end["icony"] = FLOW_END_ICON_Y
    if browse:
        browse["iconx"] = FLOW_BROWSE_ICON_X
        browse["icony"] = FLOW_BROWSE_ICON_Y


def _new_approve_activity(name: str, process_version_guid: str, vml_id: int, page_tag_form: str) -> dict:
    activity_guid = gen_uuid()
    activity = build_approve_activity(
        name=name,
        activity_guid=activity_guid,
        process_version_guid=process_version_guid,
        vml_id=vml_id,
        icon_x="",
        page_tag_form=page_tag_form,
    )
    pass_op = build_pass_operation(activity_guid=activity_guid, process_version_guid=process_version_guid)
    reject_op = build_reject_operation(activity_guid=activity_guid, process_version_guid=process_version_guid)
    activity["workflowActivityOperation"] = [pass_op, reject_op]
    return activity


def _update_activity_name(activity: dict, new_name: str) -> None:
    old_name = activity.get("activityname")
    activity["activityname"] = new_name
    activity["activitydispname"] = new_name
    note = activity.get("note")
    if isinstance(note, str) and old_name and old_name in note:
        activity["note"] = note.replace(str(old_name), new_name)


def update_workflow(
    data: dict,
    *,
    target_business: list[dict],
    rename_map: dict[str, str],
) -> tuple[dict, dict[str, Any]]:
    _wf, process, version = _workflow_parts(data)
    before_identity = _process_identity(process, version)
    process_version_guid = before_identity["processversionguid"]

    activities = _as_list(version.get("activity"))
    start = _find_activity(activities, name="开始", atype=10)
    end = _find_activity(activities, name="结束", atype=20)
    browse = _find_activity(activities, name="浏览", atype=100)
    if not start or not end:
        raise ValueError("已有 workflow 必须包含开始(10)和结束(20)节点")

    by_name = _activity_by_name(activities)
    apply_existing = _find_activity(activities, name="申请", atype=30)
    page_tag_form = _extract_pagetag_from_handleurl((apply_existing or {}).get("handleurl", ""))

    old_for_new = {new: old for old, new in rename_map.items()}
    target_activities: list[dict] = []
    used_old_names: set[str] = set()
    next_vmlid = _next_vmlid(activities)
    change_log: list[str] = []

    for index, target in enumerate(target_business):
        name = target["name"]
        source_name = target.get("oldName") or old_for_new.get(name) or name
        existing = by_name.get(source_name)
        if existing and existing.get("activityname") != name:
            _update_activity_name(existing, name)
            change_log.append(f"rename:{source_name}->{name}")
        if existing:
            existing["processversionguid"] = process_version_guid
            target_activities.append(existing)
            used_old_names.add(source_name)
            continue
        if target["type"] == "apply":
            if apply_existing and apply_existing.get("activityname") != name:
                _update_activity_name(apply_existing, name)
                change_log.append(f"rename:申请->{name}")
            if not apply_existing:
                raise ValueError("已有 workflow 缺少申请节点，不能安全原地修改")
            target_activities.append(apply_existing)
            used_old_names.add("申请")
            continue
        new_activity = _new_approve_activity(name, process_version_guid, next_vmlid + index, page_tag_form)
        target_activities.append(new_activity)
        change_log.append(f"add:{name}")

    removed = [
        act.get("activityname")
        for act in activities
        if isinstance(act, dict)
        and act.get("activityname") not in ENGINE_ACTIVITY_NAMES
        and act.get("activityname") not in {a.get("activityname") for a in target_activities}
        and act.get("activityname") not in used_old_names
    ]
    for name in removed:
        change_log.append(f"remove:{name}")

    seq = [start] + target_activities + [end]
    version["activity"] = seq + ([browse] if browse else [])
    _ensure_reject_configs(version, version["activity"], process_version_guid)
    version["transition"] = _rebuild_main_transitions(version, seq, process_version_guid)
    _apply_layout(start, target_activities, end, browse)

    after_identity = _process_identity(process, version)
    if after_identity != before_identity:
        raise ValueError(
            "修改已有 workflow 时禁止改变 processguid/processversionguid/version: "
            f"before={before_identity}, after={after_identity}"
        )
    return data, {
        "identity": before_identity,
        "changes": change_log,
        "activityNames": [act.get("activityname") for act in version["activity"]],
    }


def cli() -> int:
    parser = argparse.ArgumentParser(description="原地修改已有 workflow yml（保留 processguid/processversionguid/version）")
    parser.add_argument("--workflow-file", required=True, help="已有 .workflow.yml 文件")
    parser.add_argument("--from-ir", help="兼容：从 lowcode-dsl-gen IR workflow spec 读取目标活动")
    parser.add_argument("--asset-id", help="兼容：IR 中 workflow asset id；多个 workflow 时必填")
    parser.add_argument("--activities-json", default="", help="目标业务活动数组 JSON；默认推荐，规划纠偏时可不依赖 IR")
    parser.add_argument("--rename-map-json", default="", help="节点改名映射 JSON，例如 {\"部门经理审批\":\"科室负责人审批\"}")
    parser.add_argument("--operation-mode", default="update-existing", choices=sorted(ALLOWED_OPERATION_MODES))
    parser.add_argument("--dry-run", action="store_true", help="只校验和打印变更摘要，不写回文件")
    parser.add_argument("--confirm", action="store_true",
                        help="确认写回。不加 --confirm 一律拒绝改文件，必须先 --dry-run 预览（落盘前确认红线）")
    args = parser.parse_args()

    workflow_path = Path(args.workflow_file).resolve()
    if not workflow_path.is_file():
        print_err(f"workflow 文件不存在: {workflow_path}")
        return 1
    if not args.from_ir and not args.activities_json:
        print_err("--from-ir 或 --activities-json 必须提供一个")
        return 1

    try:
        spec = _load_ir_workflow_spec(Path(args.from_ir).resolve(), args.asset_id) if args.from_ir else {}
        operation_mode = spec.get("operationMode") or args.operation_mode
        if operation_mode not in ALLOWED_OPERATION_MODES:
            raise ValueError(f"update_workflow.py 只允许 revise-plan/update-existing，不允许 {operation_mode}")
        target_business = _target_business_activities(spec, args.activities_json)
        renames = _rename_map(spec, args.rename_map_json)
        data = yaml_load(workflow_path)
        updated, report = update_workflow(data, target_business=target_business, rename_map=renames)
    except Exception as exc:
        print_err(str(exc))
        return 1

    print_ok(f"workflow 修改校验通过: {workflow_path}")
    print_info(
        "  - 保留标识: "
        f"processguid={report['identity']['processguid']}, "
        f"processversionguid={report['identity']['processversionguid']}, "
        f"version={report['identity']['version']}"
    )
    print_info("  - 活动列表: " + " -> ".join(str(x) for x in report["activityNames"]))
    print_info("  - 变更: " + (", ".join(report["changes"]) if report["changes"] else "无结构变化"))

    if args.dry_run:
        print_info("  - dry-run: 未写回文件")
        return 0

    if not args.confirm:
        print_err(
            "拒绝写回：修改工作流必须经人工预览确认后才能写入。\n"
            "请先用 --dry-run 预览变更摘要，确认无误后再加 --confirm 写回。\n"
            "（落盘前确认红线：禁止未经 dry-run 预览 + --confirm 确认直接改文件）"
        )
        return 1

    yaml_dump(updated, workflow_path)
    print_ok(f"workflow 已原地更新: {workflow_path}")
    print_info(f"  - 下一步校验: python3 scripts/validate_yml.py {workflow_path}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
