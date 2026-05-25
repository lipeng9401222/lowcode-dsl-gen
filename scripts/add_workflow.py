#!/usr/bin/env python3
"""add_workflow.py — 创建符合《Epoint 工作流 YAML 定义规范》的工作流 yml.

骨架（红线）：
    必含 5 类节点：开始(10) + 申请(30) + N 个审批(30) + 结束(20) + 浏览(100, 孤立)
    开始节点不能填表单；申请节点必须独立；开始/结束名称固定为"开始"/"结束".

字段命名：全小写（如 processguid / activityguid / activitytype），
          activity/transition 列表项直接平铺，不再多一层 WorkflowActivity 包装.

用法：
    # 默认骨架：开始 + 申请 + 审批 + 结束 + 浏览
    python add_workflow.py \\
        --metadata /path/to/metadata \\
        --name "采购立项审核流程" \\
        --material "采购立项申请表"

    # 多审批节点（开始 + 申请 + 部门审核 + 主管审核 + 财务审核 + 结束 + 浏览）
    python add_workflow.py \\
        --metadata /path/to/metadata \\
        --name "费用报销审核流程" \\
        --approvers "部门审核,主管审核,财务审核" \\
        --material "费用报销申请单"

    # 关联具体表单与数据表（用于 workflowPvMaterial / workflowPvMisTableSet）
    python add_workflow.py \\
        --metadata /path/to/metadata \\
        --name "请假审批流程" \\
        --material "请假申请表" \\
        --form-id 159 --sql-tablename formtable20260112164507245 \\
        --sql-tablename formtable20260112164507245
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    gen_uuid,
    now_str,
    parse_json_arg,
    print_err,
    print_info,
    print_ok,
    print_warn,
    safe_filename,
    yaml_dump,
)


def _resolve_pagetags(app_root: Path, page_tag_form: str, page_tag_detail: str):
    """根据用户传参 + 同应用 pagedesigne 自动推断 pagetag.

    返回 (page_tag_form, page_tag_detail)：
        - 用户显式传值 → 直接用
        - 未传 + 同应用下仅 1 份 pagedesigne → 自动取该 pagetag（form/detail 都用它）
        - 未传 + 多份 pagedesigne → 给提示并返回 (None, None) 让 cli 退出
        - 没有 pagedesigne 目录或为空 → 返回 ("", "")，handleurl 回退到 [#=FirstMaterialUrl#]
    """
    if page_tag_form:
        return page_tag_form, page_tag_detail or page_tag_form

    page_dir = app_root / "pagedesigne"
    if not page_dir.is_dir():
        return "", ""

    import re as _re
    candidates: list[tuple[str, Path]] = []
    for path in list(page_dir.glob("*.pagedesigne.yml")) + list(page_dir.glob("*.json")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _re.search(r'"pagetag"\s*:\s*"([^"]+)"', text)
        if m:
            candidates.append((m.group(1), path))

    if not candidates:
        return "", ""
    if len(candidates) == 1:
        tag = candidates[0][0]
        print_info(f"自动推断 pagetag：{tag}（取自 {candidates[0][1].name}）")
        return tag, page_tag_detail or tag

    # 多份歧义
    print_err(
        f"检测到 {len(candidates)} 个 pagedesigne 文件，请通过 --pagetag-form / --pagetag-detail 显式指定 pagetag："
    )
    for tag, path in candidates:
        print_err(f"  - {path.name}: pagetag={tag}")
    return None, None


# ============================================================
# 节点构造
# ============================================================

def _common_emptyish_for_terminal_node() -> dict:
    """开始/结束/浏览节点的"应为空"字段（按规范红线）.

    multitransactormode/handleurl/mobilehandleurl/isallowaddattachfile/
    timelimitenable/earlywarning_enable/is_passwhennotransactor 设为 None.
    """
    return {
        "multitransactormode": None,
        "handleurl": None,
        "mobilehandleurl": None,
        "isallowaddattachfile": None,
        "timelimitenable": None,
        "earlywarning_enable": None,
        "is_passwhennotransactor": None,
    }


def build_start_activity(*, activity_guid: str, process_version_guid: str) -> dict:
    """开始节点（activitytype=10）：纯启动，不能填表单."""
    activity = {
        "activityguid": activity_guid,
        "activityname": "开始",
        "activitydispname": "开始",
        "processversionguid": process_version_guid,
        "activitytype": 10,
        "splittype": 30,
        "jointype": None,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": "-159",
        "icony": "123",
        "vmlid": -1,
        "note": "流程开始",
    }
    activity.update(_common_emptyish_for_terminal_node())
    activity["workflowActivityOperation"] = [{
        "operationguid": gen_uuid(),
        "activityguid": activity_guid,
        "processversionguid": process_version_guid,
        "operationname": "送下一步",
        "operationtype": 10,
        "is_requireopinion": 20,
        "is_checkmaterialsubmit": 20,
        "is_showoperationpage": 0,
        "operationvisiablecase": "10",
        "is_shownextactivity": 1,
        "is_showopiniontemplete": 0,
        "ordernumber": 0,
    }]
    return activity


def build_apply_activity(*, activity_guid: str, process_version_guid: str, vml_id: int = 2,
                         page_tag_form: str = "") -> dict:
    """申请节点（activitytype=30，独立于开始节点）：填报提交，必须绑表单."""
    handle_url = (
        f"home/vuepagedesigner/renderer/add?pagetag={page_tag_form}"
        if page_tag_form else "[#=FirstMaterialUrl#]"
    )
    return {
        "activityguid": activity_guid,
        "activityname": "申请",
        "activitydispname": "申请",
        "processversionguid": process_version_guid,
        "activitytype": 30,
        "splittype": 30,
        "jointype": 30,
        "multitransactormode": 10,
        "handleurl": handle_url,
        "mobilehandleurl": handle_url,
        "isallowaddattachfile": 20,
        "timelimitenable": 20,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_enable": 20,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_passwhennotransactor": 20,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": "26.5",
        "icony": "99",
        "vmlid": vml_id,
        "note": "申请人填写并提交申请信息",
    }


def build_approve_activity(
    *,
    name: str,
    activity_guid: str,
    process_version_guid: str,
    vml_id: int,
    icon_x: float,
    is_free: bool = False,
    page_tag_form: str = "",
) -> dict:
    """普通审批节点（activitytype=30）：可有多个."""
    handle_url = (
        f"home/vuepagedesigner/renderer/add?pagetag={page_tag_form}"
        if page_tag_form else "[#=FirstMaterialUrl#]"
    )
    return {
        "activityguid": activity_guid,
        "activityname": name,
        "activitydispname": name,
        "processversionguid": process_version_guid,
        "activitytype": 30,
        "splittype": 30,
        "jointype": 30,
        "multitransactormode": 25 if is_free else 10,
        "handleurl": handle_url,
        "mobilehandleurl": handle_url,
        "isallowaddattachfile": 20,
        "timelimitenable": 20,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_enable": 20,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_passwhennotransactor": 10 if is_free else 20,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": str(icon_x),
        "icony": "99",
        "vmlid": vml_id,
        "nopasshandlevalue": "10",
        "note": f"{name}人审核",
    }


def build_subprocess_activity(
    *,
    name: str,
    activity_guid: str,
    process_version_guid: str,
    vml_id: int,
    icon_x: float,
    callsubprocessguid: str,
    subprocesssynctype: int = 20,
    sub_multi_mode: int = 10,
    page_tag_form: str = "",
) -> dict:
    """子流程节点（activitytype=90）。"""
    handle_url = (
        f"home/vuepagedesigner/renderer/add?pagetag={page_tag_form}"
        if page_tag_form else "[#=FirstMaterialUrl#]"
    )
    return {
        "activityguid": activity_guid,
        "activityname": name,
        "activitydispname": name,
        "processversionguid": process_version_guid,
        "activitytype": 90,
        "splittype": 20,
        "jointype": 30,
        "callsubprocessguid": callsubprocessguid,
        "subprocesssynctype": subprocesssynctype,
        "multitransactormode": 10,
        "subProMultiTransctorMode": sub_multi_mode,
        "handleurl": handle_url,
        "mobilehandleurl": handle_url,
        "isallowaddattachfile": 20,
        "timelimitenable": 20,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_enable": 20,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_passwhennotransactor": 20,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": str(icon_x),
        "icony": "99",
        "vmlid": vml_id,
        "note": f"{name}子流程调用",
    }


def build_end_activity(
    *,
    activity_guid: str,
    process_version_guid: str,
    icon_x: float,
) -> dict:
    """结束节点（activitytype=20）."""
    activity = {
        "activityguid": activity_guid,
        "activityname": "结束",
        "activitydispname": "结束",
        "processversionguid": process_version_guid,
        "activitytype": 20,
        "splittype": None,
        "jointype": 30,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": str(icon_x),
        "icony": "123",
        "vmlid": 1,
        "note": "流程结束",
    }
    activity.update(_common_emptyish_for_terminal_node())
    return activity


def build_browse_activity(*, activity_guid: str, process_version_guid: str,
                          page_tag_detail: str = "") -> dict:
    """浏览节点（activitytype=100，孤立节点）：位置置于流程上方."""
    handle_url = (
        f"home/vuepagedesigner/renderer/add?pagetag={page_tag_detail}"
        if page_tag_detail else "[#=FirstMaterialUrl#]"
    )
    activity = {
        "activityguid": activity_guid,
        "activityname": "浏览",
        "activitydispname": "浏览",
        "processversionguid": process_version_guid,
        "activitytype": 100,
        "splittype": 30,
        "jointype": None,
        "handleurl": handle_url,
        "mobilehandleurl": handle_url,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "view",
        "iconx": "253",
        "icony": "-20",
        "vmlid": -2,
        "note": "已办流程浏览",
    }
    # 浏览节点的"应为空"字段
    empties = _common_emptyish_for_terminal_node()
    # 浏览节点 handleurl/mobilehandleurl 实际允许填写，去掉这两项的 None 覆盖
    empties.pop("handleurl", None)
    empties.pop("mobilehandleurl", None)
    activity.update(empties)
    return activity


# ============================================================
# 操作按钮（送下一步 / 退回）
# ============================================================

def build_pass_operation(
    *,
    activity_guid: str,
    process_version_guid: str,
    is_apply: bool = False,
    ordernumber: int = 0,
    state_level: int = 10,
) -> dict:
    """通过/送下一步按钮.

    - is_apply=True：申请节点上的提交按钮，强制校验表单
    - state_level：按钮重要程度（0/10/20/30），默认 10（主按钮，蓝色）
    """
    return {
        "operationguid": gen_uuid(),
        "activityguid": activity_guid,
        "processversionguid": process_version_guid,
        "operationname": "送下一步",
        "operationtype": 10,
        "is_requireopinion": 10,
        "is_checkmaterialsubmit": 10 if is_apply else 20,
        "is_showoperationpage": 1,
        "operationvisiablecase": "10",
        "is_shownextactivity": 1,
        "is_showopiniontemplete": 0,
        "ordernumber": ordernumber,
        "statelevel": state_level,
    }


def build_reject_operation(
    *,
    activity_guid: str,
    process_version_guid: str,
    ordernumber: int = 1,
    state_level: int = 30,
) -> dict:
    """退回按钮（operationtype=30）.

    必带 backtargetscope='1'、targetactivity='[#=AllBeforeActivity#]'、multitransctormode='OR'
    需配合 workflowConfig（belongto=22, configname=backTargetScope, sourceguid=该按钮 operationguid）.
    state_level 默认 30（危险按钮，红色）.
    """
    return {
        "operationguid": gen_uuid(),
        "activityguid": activity_guid,
        "processversionguid": process_version_guid,
        "operationname": "退回",
        "operationtype": 30,
        "is_requireopinion": 10,
        "is_checkmaterialsubmit": 20,
        "is_showoperationpage": 1,
        "operationvisiablecase": "1020",
        "is_shownextactivity": 0,
        "backtargetscope": "1",
        "targetactivity": "[#=AllBeforeActivity#]",
        "multitransctormode": "OR",
        "is_showopiniontemplete": 0,
        "ordernumber": ordernumber,
        "statelevel": state_level,
    }


def build_custom_design_operation(
    *,
    activity_guid: str,
    process_version_guid: str,
    ordernumber: int = 2,
) -> dict:
    """自定义流程设计按钮（operationtype=80）。"""
    return {
        "operationguid": gen_uuid(),
        "activityguid": activity_guid,
        "processversionguid": process_version_guid,
        "operationname": "流程设计",
        "operationtype": 80,
        "is_requireopinion": 20,
        "is_checkmaterialsubmit": 20,
        "is_showoperationpage": 1,
        "operationvisiablecase": "10",
        "is_shownextactivity": 0,
        "is_showopiniontemplete": 0,
        "ordernumber": ordernumber,
        "statelevel": 10,
        "operationpageurl": (
            '{"url":"frame/pages/epointworkflow/client/flowsetting?'
            'processVersionInstanceGuid=[#=ProcessVersionInstance_ProcessVersionInstanceGuid#]&'
            'workItemGuid=[#=WorkItem_WorkItemGuid#]&'
            'processversionguid=[#=ProcessVersion_ProcessVersionGuid#]",'
            '"dialog":{"fullscreen": true}}'
        ),
    }


def _parse_name_set(value: str) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}


def _parse_json_list_arg(value: str, label: str) -> list[dict]:
    if not value:
        return []
    return parse_json_arg(value, expected_type=list, label=label)


def _normalize_method(raw: dict, process_version_guid: str, index: int) -> dict:
    method_guid = raw.get("methodguid") or gen_uuid()
    item = {
        "methodguid": method_guid,
        "processversionguid": raw.get("processversionguid") or process_version_guid,
        "dllpath": raw.get("dllpath", ""),
        "typename": raw.get("typename", ""),
        "methodname": raw.get("methodname", raw.get("name", "")),
        "returnvaluetype": raw.get("returnvaluetype", "Void"),
        "note": raw.get("note", raw.get("description", "")),
        "ordernum": int(raw.get("ordernum", (index + 1) * 10)),
    }
    if raw.get("ruleguid"):
        item["ruleguid"] = raw.get("ruleguid")
    params = []
    for j, param in enumerate(raw.get("workflowMethodParameter") or raw.get("params") or []):
        if not isinstance(param, dict):
            continue
        params.append({
            "mpguid": param.get("mpguid") or param.get("mpguid") or gen_uuid(),
            "methodguid": method_guid,
            "mpname": param.get("mpname", param.get("name", "")),
            "mptype": int(param.get("mptype", 10)),
            "mpvalue": param.get("mpvalue", param.get("value", "")),
            "encrypt": str(param.get("encrypt", "0")),
            "processversionguid": param.get("processversionguid") or param.get("processversionguid") or process_version_guid,
            "ordernum": int(param.get("ordernum", param.get("ordernum", (j + 1) * 10))),
            "fieldguid": param.get("fieldguid", ""),
            "tenantguid": param.get("tenantguid", ""),
            "mpnamedescription": param.get("mpnamedescription", param.get("nameDescription", "")),
            "mpvaluedescription": param.get("mpvaluedescription", param.get("valueDescription", "")),
        })
    if params:
        item["workflowMethodParameter"] = params
    return item


def _normalize_event(raw: dict, process_version_guid: str, activity_lookup: dict[str, str], operation_lookup: dict[str, str], index: int) -> dict:
    belong_to = int(raw.get("belongto", 20))
    source_guid = (
        raw.get("sourceguid")
        or activity_lookup.get(raw.get("sourceActivity", ""))
        or operation_lookup.get(raw.get("sourceOperation", ""))
        or ""
    )
    item = {
        "eventguid": raw.get("eventguid") or gen_uuid(),
        "eventname": raw.get("eventname") or raw.get("name", f"流程事件{index + 1}"),
        "belongto": belong_to,
        "eventtype": int(raw.get("eventtype", 25 if belong_to == 20 else 55)),
        "sourceguid": source_guid,
        "processversionguid": raw.get("processversionguid") or process_version_guid,
        "synctype": int(raw.get("synctype", 0)),
        "ordernumber": int(raw.get("ordernumber", raw.get("ordernumber", (index + 1) * 100))),
    }
    if raw.get("eventmethodguid"):
        item["eventmethodguid"] = raw.get("eventmethodguid")
    if raw.get("ruleguid"):
        item["ruleguid"] = raw.get("ruleguid")
    if raw.get("baseouguid"):
        item["baseouguid"] = raw.get("baseouguid")
    return item


def _normalize_context(raw: dict, process_version_guid: str, material_guid: str, sql_tablename: str, index: int) -> dict:
    value_source = int(raw.get("valuesource", 10))
    item = {
        "fieldguid": raw.get("fieldguid") or gen_uuid(),
        "fieldname": raw.get("fieldname") or raw.get("name", f"context{index + 1}"),
        "belongto": int(raw.get("belongto", 10)),
        "fieldtype": int(raw.get("fieldtype", 10)),
        "valuesource": value_source,
        "fieldvalue": raw.get("fieldvalue", ""),
        "processversionguid": raw.get("processversionguid") or process_version_guid,
        "note": raw.get("note", raw.get("description", "")),
    }
    if value_source == 30:
        item["frommaterialguid"] = raw.get("frommaterialguid") or material_guid
        # spec v2: fromsqltablename 取代 fromMisTableId / fromFieldId
        # 入参兼容：优先 fromsqltablename，老入参 fromMisTableId / frommistableid 不再使用
        item["fromsqltablename"] = (
            raw.get("fromsqltablename")
            or raw.get("fromSqlTableName")
            or raw.get("from_sqltablename")
            or sql_tablename
            or ""
        )
        item["fromfieldname"] = raw.get("fromfieldname") or item["fieldname"]
    return item


def _normalize_condition(raw: dict, process_version_guid: str, transition_guid: str, index: int) -> dict:
    expression_type = int(raw.get("conditionexpressiontype", 10))
    item = {
        "conditionguid": raw.get("conditionguid") or gen_uuid(),
        "conditionname": raw.get("conditionname") or raw.get("name", f"流转条件{index + 1}"),
        "transitionguid": raw.get("transitionguid") or transition_guid,
        "conditionexpressiontype": expression_type,
        "processversionguid": raw.get("processversionguid") or process_version_guid,
        "ordernum": int(raw.get("ordernum", index)),
    }
    for key in (
        "leftvalue", "lefttext", "compareoperation", "rightvalue", "righttext",
        "valuetype", "conditionexpression", "methodguid", "ruleguid", "remark",
    ):
        alt = key[:1].lower() + key[1:]
        if key in raw or alt in raw:
            item[key] = raw.get(key, raw.get(alt))
    if expression_type == 10 and "valuetype" not in item:
        item["valuetype"] = 10
    return item


# ============================================================
# 变迁
# ============================================================

def build_transition(
    *,
    from_guid: str,
    to_guid: str,
    process_version_guid: str,
    name: str,
    vml_id: int,
) -> dict:
    """构造一条变迁（transition）.

    transitionname 通常用业务语义命名：申请、审批、结束等.
    """
    return {
        "transitionguid": gen_uuid(),
        "processversionguid": process_version_guid,
        "fromactivityguid": from_guid,
        "toactivityguid": to_guid,
        "transitionname": name,
        "transitiondispname": name,
        "is_sendtomessagecenter": 10,
        "priority": 60,
        "type": 10,
        "targetactivitytransactorsource": 10,
        "is_targettransactor_editable": 10,
        "is_default": 20,
        "is_showasoperationbutton": 20,
        "vmlid": vml_id,
    }


# ============================================================
# CLI
# ============================================================

def cli():
    parser = argparse.ArgumentParser(
        description="按《Epoint 工作流 YAML 定义规范》生成工作流 yml",
    )
    parser.add_argument("--app-root", "--metadata", dest="app_root", required=True,
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名，仍可用")
    parser.add_argument("--name", required=True, help="流程名称（中文）")
    parser.add_argument(
        "--approvers", default="审批",
        help="审批节点列表（逗号分隔，不含开始/申请/结束/浏览）[审批]",
    )
    parser.add_argument(
        "--material", default="申请表单",
        help="流程材料名称 [申请表单]",
    )
    parser.add_argument(
        "--form-id", default="",
        help="表单 ID，用于拼 pageurl_read/pageurl_readandwrite，默认留空交给设计器后填",
    )
    parser.add_argument(
        "--table-id", type=int, default=None,
        help="[已废弃 spec v2] 该参数仍接受但不再写入 yml；引擎根据 sql_tablename 自动绑定 mis 表",
    )
    parser.add_argument(
        "--sql-tablename", default="",
        help="数据库表名（workflowPvMisTableSet.sql_tablename）",
    )
    parser.add_argument(
        "--author", default="",
        help="创建人 GUID（workflowProcessVersion.author），默认自动生成",
    )
    parser.add_argument(
        "--process-mode",
        choices=["normal", "custom", "free", "subprocess"],
        default="normal",
        help="流程模式：normal 普通 / custom 自定义流程 / free 自由流程 / subprocess 主子流程 [normal]",
    )
    parser.add_argument("--methods-json", default="", help="外部方法数组 JSON，可包含 ruleguid 关联动作流")
    parser.add_argument("--events-json", default="", help="流程事件数组 JSON，可包含 ruleguid 关联动作流")
    parser.add_argument("--contexts-json", default="", help="相关数据 workflowContext 数组 JSON")
    parser.add_argument("--conditions-json", default="", help="流转条件数组 JSON，可按 transition/transitionname/transitionIndex 定位")
    parser.add_argument("--free-activities", default="", help="自由流程节点名称，逗号分隔；process-mode=free 时默认所有审批节点")
    parser.add_argument("--custom-activities", default="", help="需要加“流程设计”按钮的节点名称，逗号分隔；process-mode=custom 时默认第一个审批节点")
    parser.add_argument("--subprocess-guid", default="", help="子流程 processguid；process-mode=subprocess 时必填")
    parser.add_argument("--subprocess-name", default="子流程", help="子流程节点名称 [子流程]")
    parser.add_argument("--subprocess-sync-type", type=int, default=20, help="子流程调用方式：10 异步 / 20 同步 [20]")
    parser.add_argument("--subprocess-multi-transactor-mode", type=int, default=10, help="子流程多人处理方式 [10]")
    parser.add_argument("--revoke-option", type=int, default=20, help="发起人撤销设置 [20]")
    parser.add_argument("--revoke-allow-day", type=int, default=0, help="发起人允许撤销天数 [0]")
    parser.add_argument("--revoke-remind-option", type=int, default=20, help="发起人撤销提醒设置 [20]")
    parser.add_argument("--no-participator-option", type=int, default=10, help="预设处理人不存在时操作 [10]")
    parser.add_argument("--default-user-guid", default="", help="noparticipatoroption=30 时指定处理人 GUID")
    parser.add_argument("--pagetag-form", default="",
                        help="申请/审批节点 handleurl 拼接的表单页 pagetag；不填时自动扫 <app-root>/pagedesigne/ 推断（仅 1 份时自动取，多份时报错）")
    parser.add_argument("--pagetag-detail", default="",
                        help="浏览节点 handleurl 拼接的详情页 pagetag；不填时复用 --pagetag-form")
    parser.add_argument("--activity-materials-json", default="",
                        help="活动材料权限 JSON 数组（spec v2 可选）：按 activityName 匹配，"
                             "生成 workflowActivityMaterial + workflowActivityFieldAccess 嵌套结构。"
                             "格式见 references/workflow/工作流/基础骨架/02-活动按钮.md")
    parser.add_argument("--activity-extra-json", default="",
                        help="活动通用扩展字段 JSON 数组（spec v2 可选）：按 activityName 匹配，"
                             "支持 addattachfilesource / locktimewhenmultitransactor / smscontent / "
                             "overtimeremindcontent / mobileappletrules 等扩展字段")
    parser.add_argument("--approve-pass-rate-json", default="",
                        help="审批节点通过率 JSON 数组（spec v2 可选）：按 activityName 匹配，"
                             "支持 passrate (0-100) / passratecalculatemode (10或20) / nopasshandlevalue ('10'或'20')")
    parser.add_argument("--filename", help="自定义文件名（不含扩展名），默认用 name")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    # 兼容老的 --metadata 参数：若用户用了它，给一次 deprecation 提示
    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")
    # spec v2: --table-id 已废弃，仅作 alias 接受，不再写入 yml
    if "--table-id" in sys.argv:
        print_warn("--table-id 已废弃（spec v2），引擎根据 sql_tablename 自动绑定 mis 表，本次不会写入 yml")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir():
        print_err(f"应用根目录不存在: {app_root}")
        return 1

    # 自动扫 pagedesigne 推断 pagetag
    page_tag_form, page_tag_detail = _resolve_pagetags(
        app_root, args.pagetag_form, args.pagetag_detail
    )
    if page_tag_form is None:  # 多份歧义错误
        return 1
    args.pagetag_form_resolved = page_tag_form
    args.pagetag_detail_resolved = page_tag_detail or page_tag_form

    workflow_dir = app_root / "workflow"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    base_name = args.filename or safe_filename(args.name)
    target = workflow_dir / f"{base_name}.workflow.yml"

    if target.exists() and not args.force:
        print_err(f"文件已存在: {target}（--force 覆盖）")
        return 1

    # 解析审批节点列表
    approver_names = [n.strip() for n in args.approvers.split(",") if n.strip()]
    if not approver_names:
        print_err("--approvers 不能为空")
        return 1
    if args.process_mode == "subprocess" and not args.subprocess_guid:
        print_err("--process-mode subprocess 必须提供 --subprocess-guid")
        return 1
    try:
        methods_raw = _parse_json_list_arg(args.methods_json, "--methods-json")
        events_raw = _parse_json_list_arg(args.events_json, "--events-json")
        contexts_raw = _parse_json_list_arg(args.contexts_json, "--contexts-json")
        conditions_raw = _parse_json_list_arg(args.conditions_json, "--conditions-json")
        # spec v2 新增：活动材料权限 / 活动扩展字段 / 通过率
        activity_materials_raw = _parse_json_list_arg(args.activity_materials_json, "--activity-materials-json")
        activity_extra_raw = _parse_json_list_arg(args.activity_extra_json, "--activity-extra-json")
        approve_pass_rate_raw = _parse_json_list_arg(args.approve_pass_rate_json, "--approve-pass-rate-json")
    except ValueError as e:
        print_err(str(e))
        return 1

    free_activity_names = _parse_name_set(args.free_activities)
    if args.process_mode == "free" and not free_activity_names:
        free_activity_names = set(approver_names)
    custom_activity_names = _parse_name_set(args.custom_activities)
    if args.process_mode == "custom" and not custom_activity_names:
        custom_activity_names = {approver_names[0]}

    # 生成 GUID
    process_guid = gen_uuid()
    process_version_guid = gen_uuid()
    material_guid = gen_uuid()
    mistableset_guid = gen_uuid()
    table_guid = gen_uuid()
    author_guid = args.author or gen_uuid()

    start_guid = gen_uuid()
    apply_guid = gen_uuid()
    end_guid = gen_uuid()
    browse_guid = gen_uuid()
    approver_guids = [gen_uuid() for _ in approver_names]
    subprocess_activity_guid = gen_uuid() if args.process_mode == "subprocess" else ""

    # ============================================================
    # 活动列表（5 类节点完整骨架）
    # ============================================================
    activities = []

    # 1. 开始节点
    activities.append(build_start_activity(
        activity_guid=start_guid,
        process_version_guid=process_version_guid,
    ))

    # 2. 申请节点（vmlid=2）
    apply_activity = build_apply_activity(
        activity_guid=apply_guid,
        process_version_guid=process_version_guid,
        vml_id=2,
        page_tag_form=args.pagetag_form_resolved,
    )
    # 申请节点：送下一步（指向第一个审批节点）
    apply_activity["workflowActivityOperation"] = [
        build_pass_operation(
            activity_guid=apply_guid,
            process_version_guid=process_version_guid,
            is_apply=True,
        ),
    ]
    activities.append(apply_activity)

    next_vml_id = 3
    next_icon_x = 345.5
    if args.process_mode == "subprocess":
        activities.append(build_subprocess_activity(
            name=args.subprocess_name,
            activity_guid=subprocess_activity_guid,
            process_version_guid=process_version_guid,
            vml_id=next_vml_id,
            icon_x=next_icon_x,
            callsubprocessguid=args.subprocess_guid,
            subprocesssynctype=args.subprocess_sync_type,
            sub_multi_mode=args.subprocess_multi_transactor_mode,
            page_tag_form=args.pagetag_form_resolved,
        ))
        next_vml_id += 1
        next_icon_x += 200

    # 3. 审批节点（vmlid 从 3 开始递增；iconx 从 345.5 起每隔 200）
    reject_operation_guids: list[str] = []  # 收集退回按钮 GUID 用于生成 workflowConfig
    for i, name in enumerate(approver_names):
        guid = approver_guids[i]
        approve = build_approve_activity(
            name=name,
            activity_guid=guid,
            process_version_guid=process_version_guid,
            vml_id=next_vml_id + i,
            icon_x=next_icon_x + i * 200,
            is_free=name in free_activity_names,
            page_tag_form=args.pagetag_form_resolved,
        )
        pass_op = build_pass_operation(
            activity_guid=guid,
            process_version_guid=process_version_guid,
        )
        approve_ops = [pass_op]
        if args.process_mode != "free" and name not in free_activity_names:
            reject_op = build_reject_operation(
                activity_guid=guid,
                process_version_guid=process_version_guid,
            )
            reject_operation_guids.append(reject_op["operationguid"])
            approve_ops.append(reject_op)
        if name in custom_activity_names:
            approve_ops.append(build_custom_design_operation(
                activity_guid=guid,
                process_version_guid=process_version_guid,
                ordernumber=len(approve_ops),
            ))
        approve["workflowActivityOperation"] = approve_ops
        activities.append(approve)

    # 4. 结束节点
    end_icon_x = next_icon_x + len(approver_names) * 200 + 100
    activities.append(build_end_activity(
        activity_guid=end_guid,
        process_version_guid=process_version_guid,
        icon_x=end_icon_x,
    ))

    # 5. 浏览节点（孤立，置于流程上方）
    activities.append(build_browse_activity(
        activity_guid=browse_guid,
        process_version_guid=process_version_guid,
        page_tag_detail=args.pagetag_detail_resolved,
    ))

    # ============================================================
    # spec v2 可选增强：按 activityName 注入扩展字段、通过率、活动材料权限
    # ============================================================
    activity_name_lookup = {act.get("activityname"): act for act in activities}

    # F.activity-extra：按名字注入通用扩展字段
    EXTRA_ALLOWED_FIELDS = {
        "addattachfilesource", "joinmethodguid", "locktimewhenmultitransactor",
        "mobileappletrules", "smscontent", "overtimeremindcontent",
    }
    for entry in activity_extra_raw or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("activityName") or entry.get("activityname")
        if not name or name not in activity_name_lookup:
            print_warn(f"--activity-extra-json: 未找到名为 '{name}' 的活动节点，跳过")
            continue
        target_act = activity_name_lookup[name]
        for k, v in entry.items():
            if k in ("activityName", "activityname"):
                continue
            if k.lower() in EXTRA_ALLOWED_FIELDS:
                target_act[k.lower()] = v
            else:
                print_warn(f"--activity-extra-json: 字段 '{k}' 不在允许扩展字段集合，跳过")

    # F.approve-pass-rate：按名字注入审批通过率
    PASS_RATE_FIELDS = {"passrate", "passratecalculatemode", "nopasshandlevalue"}
    for entry in approve_pass_rate_raw or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("activityName") or entry.get("activityname")
        if not name or name not in activity_name_lookup:
            print_warn(f"--approve-pass-rate-json: 未找到名为 '{name}' 的活动节点，跳过")
            continue
        target_act = activity_name_lookup[name]
        if target_act.get("activitytype") != 30 or target_act.get("activityname") == "申请":
            print_warn(f"--approve-pass-rate-json: '{name}' 不是审批节点（activitytype=30），跳过")
            continue
        for k in PASS_RATE_FIELDS:
            if k in entry:
                target_act[k] = entry[k]

    # C.activity-materials：按名字注入 workflowActivityMaterial + workflowActivityFieldAccess
    for entry in activity_materials_raw or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("activityName") or entry.get("activityname")
        if not name or name not in activity_name_lookup:
            print_warn(f"--activity-materials-json: 未找到名为 '{name}' 的活动节点，跳过")
            continue
        target_act = activity_name_lookup[name]
        material = {
            "activitymaterialguid": entry.get("activitymaterialguid") or gen_uuid(),
            "processversionguid": process_version_guid,
            "activityguid": target_act["activityguid"],
            "materialguid": entry.get("materialguid") or material_guid,
            "accessright": int(entry.get("accessright", 20)),
            "is_mustsubmit": int(entry.get("is_mustsubmit", 20)),
            "submittype": int(entry.get("submittype", 10)),
        }
        if entry.get("configdata"):
            material["configdata"] = entry["configdata"]
        if entry.get("controlvisiablemethodguid"):
            material["controlvisiablemethodguid"] = entry["controlvisiablemethodguid"]

        field_access_list = entry.get("fieldAccess") or entry.get("fieldaccess") or []
        field_accesses = []
        for fa in field_access_list:
            if not isinstance(fa, dict):
                continue
            fa_item = {
                "rowguid": fa.get("rowguid") or gen_uuid(),
                "activitymaterialguid": material["activitymaterialguid"],
                "processversionguid": process_version_guid,
                "activityguid": target_act["activityguid"],
                "materialguid": material["materialguid"],
                "sqltablename": fa.get("sqltablename") or args.sql_tablename or "",
                "fieldname": fa.get("fieldname", ""),
                "fieldchinesename": fa.get("fieldchinesename", ""),
                "accessright": int(fa.get("accessright", 20)),
                "accesstype": int(fa.get("accesstype", 10)),
            }
            if fa.get("isallowattachwrite"):
                fa_item["isallowattachwrite"] = fa["isallowattachwrite"]
            field_accesses.append(fa_item)
        if field_accesses:
            material["workflowActivityFieldAccess"] = field_accesses

        existing_materials = target_act.get("workflowActivityMaterial") or []
        existing_materials.append(material)
        target_act["workflowActivityMaterial"] = existing_materials

    # ============================================================
    # workflowConfig：每个退回按钮 1 条
    # ============================================================
    workflow_config = [
        {
            "rowguid": gen_uuid(),
            "processversionguid": process_version_guid,
            "belongto": 22,
            "configname": "backTargetScope",
            "configvalue": "1",
            "sourceguid": op_guid,
        }
        for op_guid in reject_operation_guids
    ]

    # ============================================================
    # workflowPvMaterial / workflowPvMisTableSet（1:1）
    # ============================================================
    if args.form_id:
        page_read = f"epointtemp/epointsform/form/{args.form_id}/V1/recorddetail"
        page_rw = f"epointtemp/epointsform/form/{args.form_id}/V1/record"
        mobile_read = f"epointtemp/epointsform/form/{args.form_id}/V1/mobilerecorddetail"
        mobile_rw = f"epointtemp/epointsform/form/{args.form_id}/V1/mobilerecord"
    else:
        page_read = page_rw = mobile_read = mobile_rw = ""

    workflow_pv_material = [{
        "materialguid": material_guid,
        "processversionguid": process_version_guid,
        "materialname": args.material,
        "type": 10,
        "status": 10,
        "submittype": 10,
        "pageurl_read": page_read,
        "pageurl_readandwrite": page_rw,
        "mobilepageurl_read": mobile_read,
        "mobilepageurl_readandwrite": mobile_rw,
    }]

    workflow_pv_mistableset = [{
        "mistablesetguid": mistableset_guid,
        "processversionguid": process_version_guid,
        "materialguid": material_guid,
        "tableguid": table_guid,
        # spec v2: tableid 已废弃，引擎根据 sql_tablename 自动绑定 mis 表
        "sql_tablename": args.sql_tablename or "",
    }]

    # ============================================================
    # transition：开始→申请→审批1→审批2...→结束（浏览不参与流转）
    # ============================================================
    transitions: list[dict] = []
    seq = [("开始", start_guid), ("申请", apply_guid)]
    if args.process_mode == "subprocess":
        seq.append((args.subprocess_name, subprocess_activity_guid))
    seq += list(zip(approver_names, approver_guids))
    seq += [("结束", end_guid)]

    transition_names = [seq[i + 1][0] for i in range(len(seq) - 1)]
    for i in range(len(seq) - 1):
        from_name, from_guid_local = seq[i]
        to_name, to_guid_local = seq[i + 1]
        transitions.append(build_transition(
            from_guid=from_guid_local,
            to_guid=to_guid_local,
            process_version_guid=process_version_guid,
            name=transition_names[i],
            vml_id=2 + i,
        ))

    transition_lookup = {
        t["transitionname"]: t
        for t in transitions
        if isinstance(t, dict) and t.get("transitionname")
    }
    transition_guid_lookup = {
        t["transitionguid"]: t
        for t in transitions
        if isinstance(t, dict) and t.get("transitionguid")
    }
    for i, raw_condition in enumerate(conditions_raw):
        if not isinstance(raw_condition, dict):
            continue
        target_transition = None
        raw_guid = raw_condition.get("transitionguid") or raw_condition.get("transitionguid")
        if raw_guid:
            target_transition = transition_guid_lookup.get(raw_guid)
        if target_transition is None:
            raw_name = (
                raw_condition.get("transition")
                or raw_condition.get("transitionname")
                or raw_condition.get("transitionname")
                or raw_condition.get("name")
            )
            if raw_name:
                target_transition = transition_lookup.get(raw_name)
        if target_transition is None and "transitionIndex" in raw_condition:
            raw_index = int(raw_condition["transitionIndex"])
            if 0 <= raw_index < len(transitions):
                target_transition = transitions[raw_index]
            elif 1 <= raw_index <= len(transitions):
                target_transition = transitions[raw_index - 1]
        if target_transition is None:
            print_err(f"--conditions-json 第 {i + 1} 条无法定位 transition，请提供 transitionguid/transition/transitionIndex")
            return 1
        target_transition.setdefault("workflowTransitionCondition", []).append(
            _normalize_condition(raw_condition, process_version_guid, target_transition["transitionguid"], i)
        )

    activity_lookup = {
        act.get("activityname"): act.get("activityguid")
        for act in activities
        if isinstance(act, dict) and act.get("activityname") and act.get("activityguid")
    }
    operation_lookup: dict[str, str] = {}
    for act in activities:
        if not isinstance(act, dict):
            continue
        act_name = act.get("activityname", "")
        for op in act.get("workflowActivityOperation") or []:
            if not isinstance(op, dict):
                continue
            op_name = op.get("operationname", "")
            op_guid = op.get("operationguid", "")
            if not op_guid:
                continue
            if op_name:
                operation_lookup.setdefault(op_name, op_guid)
                operation_lookup[f"{act_name}:{op_name}"] = op_guid

    workflow_methods = [
        _normalize_method(raw, process_version_guid, i)
        for i, raw in enumerate(methods_raw)
        if isinstance(raw, dict)
    ]
    workflow_events = [
        _normalize_event(raw, process_version_guid, activity_lookup, operation_lookup, i)
        for i, raw in enumerate(events_raw)
        if isinstance(raw, dict)
    ]
    workflow_contexts = [
        _normalize_context(raw, process_version_guid, material_guid, args.sql_tablename or "", i)
        for i, raw in enumerate(contexts_raw)
        if isinstance(raw, dict)
    ]

    # ============================================================
    # 完整结构
    # ============================================================
    process_type = None
    custom_type = None
    if args.process_mode == "custom":
        process_type = 10
        custom_type = 0
    elif args.process_mode == "free":
        process_type = 20

    data = {
        "type": "workflow",
        "workFlow": {
            "workflowProcess": {
                "processguid": process_guid,
                "processname": args.name,
                "note": args.name,
                "isvue": 1,
                "designversion": "senior",
                "ordernum": 50,
                "status": 10,
                "tag": "20",
                "isnewversion": process_type,
                "customtype": custom_type,
                "cansimpledisplay": None,
                "statemachinetag": None,
                "appguid": None,
                "baseouguid": None,
                "tenantguid": "",
            },
            "workflowVersion": {
                "activity": activities,
                "workflowConfig": workflow_config,
                "workflowPvMaterial": workflow_pv_material,
                "workflowPvMisTableSet": workflow_pv_mistableset,
                "transition": transitions,
                "workflowProcessVersion": {
                    "processversionguid": process_version_guid,
                    "processguid": process_guid,
                    "processversionname": args.name,
                    "version": "V1",
                    "status": 10,
                    "designversion": "senior",
                    "direction": "90",
                    "createdate": now_str(),
                    "updatedate": now_str(),
                    "author": author_guid,
                    "isshowlinegraph": "Normal",      # 'Normal'(直线) / 'Orthogonal'(折线)
                    "isshownodesimple": "details",     # 'details'(详情) / 'simple'(精简)
                    "revokeoption": args.revoke_option,                # 10/20/30/40
                    "revokeallowday": args.revoke_allow_day,           # revokeoption=40 时填天数
                    "revokeremindoption": args.revoke_remind_option,   # 10(知会撤销) / 20(静默撤销)
                    "noparticipatoroption": args.no_participator_option,  # 10/20/30
                    "defaultuserguid": args.default_user_guid or None,
                },
            },
        },
    }
    version_data = data["workFlow"]["workflowVersion"]
    if workflow_methods:
        version_data["method"] = workflow_methods
    if workflow_events:
        version_data["workflowEvent"] = workflow_events
    if workflow_contexts:
        version_data["workflowContext"] = workflow_contexts

    yaml_dump(data, target)
    print_ok(f"工作流已创建: {target}")
    print_info(f"  - 流程名: {args.name}")
    middle_nodes = []
    if args.process_mode == "subprocess":
        middle_nodes.append(f"{args.subprocess_name}(90)")
    middle_nodes.extend(
        f"{n}(30{'/自由' if n in free_activity_names else ''})"
        for n in approver_names
    )
    print_info(
        "  - 节点序列: 开始(10) → 申请(30) → "
        + " → ".join(middle_nodes)
        + " → 结束(20) | 浏览(100, 孤立)"
    )
    print_info(f"  - 变迁数: {len(transitions)}")
    print_info(f"  - 退回按钮: {len(reject_operation_guids)} 个 (workflowConfig 自动生成)")
    print_info(f"  - 流程材料: {args.material}")
    if workflow_methods:
        print_info(f"  - 外部方法: {len(workflow_methods)} 个")
    if workflow_events:
        print_info(f"  - 事件配置: {len(workflow_events)} 个")
    if workflow_contexts:
        print_info(f"  - 相关数据: {len(workflow_contexts)} 个")
    if conditions_raw:
        print_info(f"  - 流转条件: {len(conditions_raw)} 个")
    if not args.form_id:
        print_info("  - 提示：未传 --form-id，材料 url 留空，需要后续在表单设计器中关联")
    if args.table_id is None:
        print_info("  - 提示：未传 --sql-tablename，workflowPvMisTableSet 字段留空，需后续填充")

    # ============================================================
    # 生成后 5 条重点检查提示（与 SKILL.md / references/workflow/工作流/index.md 对齐）
    # ============================================================
    print_info("")
    print_info("⚠️  交付前 5 条重点检查（必走，与 references/workflow/工作流/index.md 对齐）：")
    print_info("  [1] 结构完整性：type/workFlow/workflowProcess/workflowVersion/activity/transition/"
               "workflowConfig/workflowPvMaterial/workflowPvMisTableSet/workflowProcessVersion 齐全")
    print_info("  [2] 节点必填项：每个 activity 含 guid/name/type/vmlid/iconx/icony；"
               "开始/结束/浏览节点的 handleurl(浏览除外)/multitransactormode/timelimitenable/"
               "earlywarning_enable/isallowaddattachfile/is_passwhennotransactor 必须为 null")
    print_info("  [3] 关联关系闭合：processversionguid 全局一致 + transition.from/to 引用真实 activity + "
               "每个退回按钮配 1 条 workflowConfig + 材料↔表映射 1:1 + vmlid 唯一")
    print_info("  [4] 设计红线（重点：流转顺序）：5 类节点齐全；开始 ≠ 申请；"
               "transition 必须 开始→申请→审批→...→结束，禁止跳过申请节点；"
               "开始/结束/申请节点名称固定")
    print_info(f"  [5] 过引擎校验：python scripts/validate_yml.py {target}")
    print_info("       → 错误数 = 0 才算交付；整应用还要跑 validate_yml.py --check-refs <metadata>")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
