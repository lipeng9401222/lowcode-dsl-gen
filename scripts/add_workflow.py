#!/usr/bin/env python3
"""add_workflow.py — 创建符合《Epoint 工作流 YAML 定义规范》的工作流 yml.

骨架（红线）：
    必含 5 类节点：开始(10) + 申请(30) + N 个审批(30) + 结束(20) + 浏览(100, 孤立)
    开始节点不能填表单；申请节点必须独立；开始/结束名称固定为"开始"/"结束".

字段命名：spec v2 严格全小写（如 processguid / activityguid / activitytype /
          mobilehandletype / is_lockwhenmultitransactor / subpromultitransctormode）.
          activity/transition 列表项直接平铺，不再多一层 WorkflowActivity 包装.

⛔ 路径红线（spec v2）：
    应用资产直接挂在 <apptag>/ 下，**不再有 metadata/ 这一层**。
    --app-root 末尾或路径中包含 /metadata 段时直接报错退出。

用法：
    # 默认骨架：开始 + 申请 + 审批 + 结束 + 浏览
    python add_workflow.py \\
        --app-root /path/to/<apptag> \\
        --name "采购立项审核流程" \\
        --material "采购立项申请表"

    # 多审批节点（开始 + 申请 + 部门审核 + 主管审核 + 财务审核 + 结束 + 浏览）
    python add_workflow.py \\
        --app-root /path/to/<apptag> \\
        --name "费用报销审核流程" \\
        --approvers "部门审核,主管审核,财务审核" \\
        --material "费用报销申请单"

    # 关联具体数据表（用于 workflowPvMisTableSet）
    python add_workflow.py \\
        --app-root /path/to/<apptag> \\
        --name "请假审批流程" \\
        --material "请假申请表" \\
        --sql-tablename formtable20260112164507245

兼容：--from-ir 仍可用，但默认建议直接传 CLI 参数。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ir_to_workflow_args import workflow_args_from_ir  # noqa: E402
from _common import (  # noqa: E402
    assert_no_metadata_layer,
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
from workflow_defaults import (  # noqa: E402
    DEFAULT_IS_CHECKMATERIALSUBMIT,
    FLOW_BRANCH_ICON_Y,
    FLOW_BROWSE_ICON_X,
    FLOW_BROWSE_ICON_Y,
    FLOW_END_ICON_Y,
    FLOW_MAIN_ICON_Y,
    FLOW_START_ICON_X,
    FLOW_START_ICON_Y,
    build_handle_url,
    default_operationvisiablecase,
    default_splittype,
    flow_iconx_sequence,
    material_page_url,
)


BARE_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _resolve_pagetags(app_root: Path, page_tag_form: str, page_tag_detail: str):
    """根据用户传参 + 同应用页面设计器文件自动推断 pagetag.

    返回 (page_tag_form, page_tag_detail)：
        - 用户显式传值 → 直接用
        - 未传 + 同应用下仅 1 份页面 → 自动取该 pagetag（form/detail 都用它）
        - 未传 + 多份页面 → 给提示并返回 (None, None) 让 cli 退出
        - 没有页面目录或为空 → 返回 ("", "")，由 cli 使用约定 pagetag 兜底
    """
    if page_tag_form or page_tag_detail:
        return page_tag_form, page_tag_detail or page_tag_form

    import re as _re
    candidates: list[tuple[str, Path]] = []
    page_dir = app_root / "page"
    if not page_dir.is_dir():
        return "", ""
    for path in list(page_dir.glob("*.json")):
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
        f"检测到 {len(candidates)} 个页面设计器文件，请通过 --pagetag-form / --pagetag-detail 显式指定 pagetag："
    )
    for tag, path in candidates:
        print_err(f"  - {path.name}: pagetag={tag}")
    return None, None


def _fallback_pagetag_base(sql_tablename: str, workflow_name: str) -> str:
    """Return a stable ASCII-ish base for conventional pagetag fallback."""
    raw = (sql_tablename or workflow_name or "workflow").strip()
    base = re.sub(r"[^0-9A-Za-z_]+", "_", raw).strip("_").lower()
    return base or "workflow"


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
        "splittype": default_splittype(10),
        "jointype": None,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": FLOW_START_ICON_X,
        "icony": FLOW_START_ICON_Y,
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
        "is_checkmaterialsubmit": DEFAULT_IS_CHECKMATERIALSUBMIT,
        "is_showoperationpage": 0,
        "operationvisiablecase": default_operationvisiablecase(10),
        "is_shownextactivity": 1,
        "is_showopiniontemplete": 0,
        "ordernumber": 0,
    }]
    return activity


def build_apply_activity(*, activity_guid: str, process_version_guid: str, vml_id: int = 2,
                         icon_x: str = "", page_tag_form: str = "") -> dict:
    """申请节点（activitytype=30，独立于开始节点）：填报提交，必须绑表单."""
    handle_url = build_handle_url(30, page_tag_form)
    return {
        "activityguid": activity_guid,
        "activityname": "申请",
        "activitydispname": "申请",
        "processversionguid": process_version_guid,
        "activitytype": 30,
        "splittype": default_splittype(30),
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
        "iconx": icon_x or flow_iconx(0),
        "icony": FLOW_MAIN_ICON_Y,
        "vmlid": vml_id,
        "note": "申请人填写并提交申请信息",
    }


def build_approve_activity(
    *,
    name: str,
    activity_guid: str,
    process_version_guid: str,
    vml_id: int,
    icon_x: str,
    is_free: bool = False,
    page_tag_form: str = "",
) -> dict:
    """普通审批节点（activitytype=30）：可有多个."""
    handle_url = build_handle_url(30, page_tag_form)
    return {
        "activityguid": activity_guid,
        "activityname": name,
        "activitydispname": name,
        "processversionguid": process_version_guid,
        "activitytype": 30,
        "splittype": default_splittype(30),
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
        "iconx": icon_x,
        "icony": FLOW_MAIN_ICON_Y,
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
    icon_x: str,
    callsubprocessguid: str,
    subprocesssynctype: int = 20,
    sub_multi_mode: int = 10,
    page_tag_form: str = "",
) -> dict:
    """子流程节点（activitytype=90）。handleurl 为 None（仅 30/100 有 handleurl）."""
    return {
        "activityguid": activity_guid,
        "activityname": name,
        "activitydispname": name,
        "processversionguid": process_version_guid,
        "activitytype": 90,
        "splittype": default_splittype(90),
        "jointype": 30,
        "callsubprocessguid": callsubprocessguid,
        "subprocesssynctype": subprocesssynctype,
        "multitransactormode": 10,
        "subpromultitransctormode": sub_multi_mode,
        "handleurl": None,
        "mobilehandleurl": None,
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
        "iconx": icon_x,
        "icony": FLOW_MAIN_ICON_Y,
        "vmlid": vml_id,
        "note": f"{name}子流程调用",
    }


def build_end_activity(
    *,
    activity_guid: str,
    process_version_guid: str,
    icon_x: str,
) -> dict:
    """结束节点（activitytype=20）."""
    activity = {
        "activityguid": activity_guid,
        "activityname": "结束",
        "activitydispname": "结束",
        "processversionguid": process_version_guid,
        "activitytype": 20,
        "splittype": default_splittype(20),
        "jointype": 30,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "app",
        "iconx": icon_x,
        "icony": FLOW_END_ICON_Y,
        "vmlid": 1,
        "note": "流程结束",
    }
    activity.update(_common_emptyish_for_terminal_node())
    return activity


def build_browse_activity(*, activity_guid: str, process_version_guid: str,
                          page_tag_detail: str = "") -> dict:
    """浏览节点（activitytype=100，孤立节点）：位置置于流程上方. handleurl 用 detail 模式."""
    handle_url = build_handle_url(100, page_tag_detail)
    activity = {
        "activityguid": activity_guid,
        "activityname": "浏览",
        "activitydispname": "浏览",
        "processversionguid": process_version_guid,
        "activitytype": 100,
        "splittype": default_splittype(100),
        "jointype": None,
        "handleurl": handle_url,
        "mobilehandleurl": handle_url,
        "timelimit": -1.0,
        "timelimitunit": 55,
        "earlywarning_time": -1.0,
        "earlywarning_timeunit": 55,
        "is_lockwhenmultitransactor": 0,
        "mobilehandletype": "view",
        "iconx": FLOW_BROWSE_ICON_X,
        "icony": FLOW_BROWSE_ICON_Y,
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

    - is_apply：保留兼容参数；is_checkmaterialsubmit 按现行规范固定为 20
    - state_level：按钮重要程度（0/10/20/30），默认 10（主按钮，蓝色）
    """
    return {
        "operationguid": gen_uuid(),
        "activityguid": activity_guid,
        "processversionguid": process_version_guid,
        "operationname": "送下一步",
        "operationtype": 10,
        "is_requireopinion": 10,
        "is_checkmaterialsubmit": DEFAULT_IS_CHECKMATERIALSUBMIT,
        "is_showoperationpage": 1,
        "operationvisiablecase": default_operationvisiablecase(10),
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
        "is_checkmaterialsubmit": DEFAULT_IS_CHECKMATERIALSUBMIT,
        "is_showoperationpage": 1,
        "operationvisiablecase": default_operationvisiablecase(30),
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
        "is_checkmaterialsubmit": DEFAULT_IS_CHECKMATERIALSUBMIT,
        "is_showoperationpage": 1,
        "operationvisiablecase": default_operationvisiablecase(80),
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
    if expression_type == 10:
        leftvalue = item.get("leftvalue", "")
        if isinstance(leftvalue, str) and leftvalue and BARE_FIELD_RE.match(leftvalue) and "[#=" not in leftvalue:
            fixed = f"[#={leftvalue}#]"
            print_warn(f"条件 leftvalue='{leftvalue}' 是裸字段名，已自动修正为 '{fixed}'")
            item["leftvalue"] = fixed
    return item


_CONDITION_REF_PATTERN = re.compile(r"\[(\d+)\]")
_CONDITION_EXPR_TOKEN_PATTERN = re.compile(r"\s*(\[\d+\]|\(|\)|AND|OR|NOT)\s*", re.IGNORECASE)


def _condition_sort_key(indexed_condition: tuple[int, dict]) -> tuple[int, int]:
    index, condition = indexed_condition
    try:
        return int(condition.get("ordernum", index)), index
    except (TypeError, ValueError):
        return index, index


def _condition_expression_error(expression: str, single_count: int) -> str | None:
    expression = expression or ""
    refs = [int(value) for value in _CONDITION_REF_PATTERN.findall(expression or "")]
    if not refs:
        return "conditionexpression 必须引用同一变迁下的单一表达式序号，如 [1] AND [2]"
    seen_refs: set[int] = set()
    for ref in refs:
        if ref in seen_refs:
            return f"conditionexpression 重复引用 [{ref}]"
        seen_refs.add(ref)
        if ref < 1 or ref > single_count:
            return f"conditionexpression 引用 [{ref}] 越界，同一变迁下只有 {single_count} 条 type=10 条件"

    compact = re.sub(r"\s+", "", expression or "")
    tokens: list[str] = []
    position = 0
    while position < len(expression or ""):
        match = _CONDITION_EXPR_TOKEN_PATTERN.match(expression, position)
        if not match:
            return "conditionexpression 仅支持 [n]、AND、OR、NOT 和括号"
        tokens.append(match.group(1).upper())
        position = match.end()
    if re.sub(r"\s+", "", "".join(tokens)).upper() != compact.upper():
        return "conditionexpression 包含无法识别的内容"

    position = 0

    def parse_expression() -> bool:
        return parse_or()

    def parse_or() -> bool:
        if not parse_and():
            return False
        while position < len(tokens) and tokens[position] == "OR":
            advance()
            if not parse_and():
                return False
        return True

    def parse_and() -> bool:
        if not parse_not():
            return False
        while position < len(tokens) and tokens[position] == "AND":
            advance()
            if not parse_not():
                return False
        return True

    def parse_not() -> bool:
        if position < len(tokens) and tokens[position] == "NOT":
            advance()
            return parse_not()
        return parse_primary()

    def parse_primary() -> bool:
        if position >= len(tokens):
            return False
        token = tokens[position]
        if _CONDITION_REF_PATTERN.fullmatch(token):
            advance()
            return True
        if token == "(":
            advance()
            if not parse_expression():
                return False
            if position >= len(tokens) or tokens[position] != ")":
                return False
            advance()
            return True
        return False

    def advance() -> None:
        nonlocal position
        position += 1

    if not parse_expression() or position != len(tokens):
        return "conditionexpression 语法不合法，仅支持 [n]、AND、OR、NOT 和括号组合"
    return None


def _condition_expression_type(condition: dict) -> int | None:
    try:
        return int(condition.get("conditionexpressiontype", 10))
    except (TypeError, ValueError):
        return None


def _validate_transition_conditions(transition: dict, transition_index: int) -> str | None:
    conditions = transition.get("workflowTransitionCondition") or []
    if not conditions:
        return None
    if not isinstance(conditions, list):
        return f"transition[{transition_index}] workflowTransitionCondition 必须是数组"

    indexed_single_conditions = [
        (i, condition)
        for i, condition in enumerate(conditions)
        if isinstance(condition, dict) and _condition_expression_type(condition) == 10
    ]
    single_conditions = [condition for _, condition in sorted(indexed_single_conditions, key=_condition_sort_key)]

    for i, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            return f"transition[{transition_index}].workflowTransitionCondition[{i}] 必须是对象"
        expression_type = _condition_expression_type(condition)
        if expression_type is None:
            return f"transition[{transition_index}].workflowTransitionCondition[{i}] conditionexpressiontype 必须是 10/20/30"

        label = f"transition[{transition_index}].workflowTransitionCondition[{i}]"
        if expression_type == 10:
            for key in ("leftvalue", "compareoperation", "rightvalue", "valuetype"):
                if condition.get(key) in (None, ""):
                    return f"{label} conditionexpressiontype=10 缺少 {key}"
        elif expression_type == 20:
            expression = condition.get("conditionexpression")
            if not expression:
                return f"{label} conditionexpressiontype=20 缺少 conditionexpression"
            error = _condition_expression_error(str(expression), len(single_conditions))
            if error:
                return f"{label} {error}"
        elif expression_type == 30:
            if not condition.get("methodguid") and not condition.get("ruleguid"):
                return f"{label} conditionexpressiontype=30 必须配置 methodguid 或 ruleguid"
        else:
            return f"{label} conditionexpressiontype={expression_type} 不支持（仅支持 10/20/30）"
    return None


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


def _first_present(raw: dict, *keys: str):
    """Return the first non-empty value from raw using exact key names."""
    for key in keys:
        value = raw.get(key)
        if value is not None and value != "":
            return value
    return None


def _refresh_transition_lookups(transitions: list[dict]):
    by_name: dict[str, dict] = {}
    by_guid: dict[str, dict] = {}
    by_pair: dict[tuple[str, str], dict] = {}
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        name = transition.get("transitionname")
        guid = transition.get("transitionguid")
        from_guid = transition.get("fromactivityguid")
        to_guid = transition.get("toactivityguid")
        if name:
            by_name[name] = transition
        if guid:
            by_guid[guid] = transition
        if from_guid and to_guid:
            by_pair[(from_guid, to_guid)] = transition
    return by_name, by_guid, by_pair


def _next_transition_vmlid(transitions: list[dict]) -> int:
    vmlids: list[int] = []
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        try:
            vmlids.append(int(transition.get("vmlid")))
        except (TypeError, ValueError):
            continue
    return (max(vmlids) if vmlids else 1) + 1


def _apply_optional_branch_layout(activities: list[dict], transitions: list[dict]) -> None:
    """Move one-step optional branch nodes above the main flow.

    Pattern: A → B → C and A → C.  B is a conditional detour, so it keeps its
    x slot but moves to the branch lane. This preserves the existing dynamic
    horizontal spacing while making the visual branch clear in the designer.
    """
    guid_to_activity = {
        act.get("activityguid"): act
        for act in activities
        if isinstance(act, dict) and act.get("activityguid")
    }
    outgoing: dict[str, list[str]] = {}
    edge_set: set[tuple[str, str]] = set()
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        from_guid = transition.get("fromactivityguid")
        to_guid = transition.get("toactivityguid")
        if not from_guid or not to_guid:
            continue
        outgoing.setdefault(from_guid, []).append(to_guid)
        edge_set.add((from_guid, to_guid))

    branch_guids: set[str] = set()
    for source_guid, direct_targets in outgoing.items():
        for branch_guid in direct_targets:
            branch_act = guid_to_activity.get(branch_guid)
            if not branch_act or branch_act.get("activitytype") == 100:
                continue
            for merge_guid in outgoing.get(branch_guid, []):
                if (source_guid, merge_guid) in edge_set:
                    branch_guids.add(branch_guid)

    for act in activities:
        if not isinstance(act, dict):
            continue
        atype = act.get("activitytype")
        guid = act.get("activityguid")
        if atype == 10:
            act["iconx"] = FLOW_START_ICON_X
            act["icony"] = FLOW_START_ICON_Y
        elif atype == 100:
            act["iconx"] = FLOW_BROWSE_ICON_X
            act["icony"] = FLOW_BROWSE_ICON_Y
        elif atype == 20:
            act["icony"] = FLOW_END_ICON_Y
        elif guid in branch_guids:
            act["icony"] = FLOW_BRANCH_ICON_Y
        else:
            act["icony"] = FLOW_MAIN_ICON_Y


# ============================================================
# CLI
# ============================================================

def cli():
    parser = argparse.ArgumentParser(
        description="按《Epoint 工作流 YAML 定义规范》生成工作流 yml",
    )
    parser.add_argument("--from-ir", help="兼容：从 lowcode-dsl-gen IR 文件读取 workflow spec")
    parser.add_argument("--asset-id", help="兼容：IR 中 workflow asset id；多个 workflow 时必填")
    parser.add_argument("--dry-run", action="store_true", help="只校验/打印参数，不创建目录、不写文件")
    parser.add_argument("--app-root", "--metadata", dest="app_root",
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名，仍可用")
    parser.add_argument("--name", help="流程名称（中文）")
    parser.add_argument(
        "--approvers", default="审批",
        help="审批节点列表（逗号分隔，不含开始/申请/结束/浏览）[审批]",
    )
    parser.add_argument(
        "--material", default="申请表单",
        help="流程材料名称 [申请表单]",
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
    parser.add_argument("--conditions-json", default="",
                        help="流转条件数组 JSON，可按 transition/transitionname/transitionIndex 定位；"
                             "也可传 fromActivity/toActivity，缺少对应变迁时自动创建")
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
                        help="申请/审批节点 handleurl 拼接的表单页 pagetag；不填时自动扫 <app-root>/page/ 推断（仅 1 份时自动取，多份时报错）")
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

    if args.from_ir:
        ir_path = Path(args.from_ir).resolve()
        if ir_path.parent.name == ".lowcode-plans" and ir_path.name.endswith("-ir.yml"):
            print_err(
                "IR 文件路径已废弃：请使用 .lowcode-plans/<apptag>/ir.yml，"
                f"当前是 {ir_path}"
            )
            return 1
        try:
            from _common import yaml_load  # noqa: E402
            converted = workflow_args_from_ir(yaml_load(ir_path), args.asset_id)
        except Exception as e:
            print_err(f"--from-ir 解析失败: {e}")
            return 1
        for key, value in converted.items():
            if value not in (None, ""):
                if key.endswith("_json") and isinstance(value, list):
                    value = json.dumps(value, ensure_ascii=False)
                setattr(args, key, value)

    if not args.app_root:
        print_err("--app-root 必填")
        return 1
    if not args.name:
        print_err("--name 必填（或通过 --from-ir 提供 workflow.spec.processName）")
        return 1

    # 兼容老的 --metadata 参数：若用户用了它，给一次 deprecation 提示
    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir() and not args.dry_run:
        print_err(f"应用根目录不存在: {app_root}")
        return 1
    if not app_root.is_dir() and args.dry_run:
        print_warn(f"应用根目录暂不存在，dry-run 仅校验参数与目标路径: {app_root}")

    # spec v2 路径红线：应用根 = <apptag>/，禁止再有 metadata/ 这一层
    ok, msg = assert_no_metadata_layer(app_root)
    if not ok:
        print_err(msg)
        return 1
    print_info(f"✅ 应用根目录已遵循新结构（不含 metadata/ 层）：{app_root}")

    # 自动扫页面设计器文件推断 pagetag
    page_tag_form, page_tag_detail = _resolve_pagetags(
        app_root, args.pagetag_form, args.pagetag_detail
    )
    if page_tag_form is None:  # 多份歧义错误
        return 1
    args.pagetag_form_resolved = page_tag_form
    args.pagetag_detail_resolved = page_tag_detail or page_tag_form
    if not args.pagetag_form_resolved:
        fallback_base = _fallback_pagetag_base(args.sql_tablename, args.filename or args.name)
        args.pagetag_form_resolved = f"{fallback_base}_form"
        print_warn(
            "未解析到表单页 pagetag，使用约定 pagetag "
            f"'{args.pagetag_form_resolved}' 生成 activitytype=30 URL；页面资产需后续补齐"
        )
    if not args.pagetag_detail_resolved:
        fallback_base = _fallback_pagetag_base(args.sql_tablename, args.filename or args.name)
        args.pagetag_detail_resolved = f"{fallback_base}_detail"
        print_warn(
            "未解析到详情页 pagetag，使用约定 pagetag "
            f"'{args.pagetag_detail_resolved}' 生成 activitytype=100 URL；页面资产需后续补齐"
        )

    workflow_dir = app_root / "workflow"

    base_name = args.filename or safe_filename(args.name)
    target = workflow_dir / f"{base_name}.workflow.yml"

    if target.exists() and not args.force and not args.dry_run:
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

    flow_layout_nodes: list[tuple[int, str]] = [(30, "申请")]
    if args.process_mode == "subprocess":
        flow_layout_nodes.append((90, args.subprocess_name))
    flow_layout_nodes.extend((30, name) for name in approver_names)
    flow_layout_nodes.append((20, "结束"))
    flow_iconxs = flow_iconx_sequence(flow_layout_nodes)
    flow_pos = 0

    # 2. 申请节点（vmlid=2）
    apply_activity = build_apply_activity(
        activity_guid=apply_guid,
        process_version_guid=process_version_guid,
        vml_id=2,
        icon_x=flow_iconxs[flow_pos],
        page_tag_form=args.pagetag_form_resolved,
    )
    flow_pos += 1
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
    if args.process_mode == "subprocess":
        activities.append(build_subprocess_activity(
            name=args.subprocess_name,
            activity_guid=subprocess_activity_guid,
            process_version_guid=process_version_guid,
            vml_id=next_vml_id,
            icon_x=flow_iconxs[flow_pos],
            callsubprocessguid=args.subprocess_guid,
            subprocesssynctype=args.subprocess_sync_type,
            sub_multi_mode=args.subprocess_multi_transactor_mode,
            page_tag_form=args.pagetag_form_resolved,
        ))
        next_vml_id += 1
        flow_pos += 1

    # 3. 审批节点（vmlid 从 3 开始递增；iconx 按动态横向布局递增）
    reject_operation_guids: list[str] = []  # 收集退回按钮 GUID 用于生成 workflowConfig
    for i, name in enumerate(approver_names):
        guid = approver_guids[i]
        approve = build_approve_activity(
            name=name,
            activity_guid=guid,
            process_version_guid=process_version_guid,
            vml_id=next_vml_id + i,
            icon_x=flow_iconxs[flow_pos],
            is_free=name in free_activity_names,
            page_tag_form=args.pagetag_form_resolved,
        )
        flow_pos += 1
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
    activities.append(build_end_activity(
        activity_guid=end_guid,
        process_version_guid=process_version_guid,
        icon_x=flow_iconxs[flow_pos],
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
    page_read = material_page_url("detail", args.pagetag_detail_resolved)
    page_rw = material_page_url("add", args.pagetag_form_resolved)
    mobile_read = mobile_rw = ""

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
        # spec v2: tableid 已废弃且不再写入 yml；引擎在工作流安装时根据 sql_tablename
        # 自动绑定 mis 表 ID（mis 表先于工作流入库，安装时按 sql_tablename + fieldname 查询替换）。
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

    activity_lookup = {
        act.get("activityname"): act.get("activityguid")
        for act in activities
        if isinstance(act, dict) and act.get("activityname") and act.get("activityguid")
    }
    transition_lookup, transition_guid_lookup, transition_pair_lookup = _refresh_transition_lookups(transitions)
    next_transition_vmlid = _next_transition_vmlid(transitions)
    for i, raw_condition in enumerate(conditions_raw):
        if not isinstance(raw_condition, dict):
            continue
        target_transition = None
        raw_from_activity = _first_present(
            raw_condition,
            "fromActivity",
            "fromactivity",
            "fromActivityName",
            "fromactivityname",
        )
        raw_to_activity = _first_present(
            raw_condition,
            "toActivity",
            "toactivity",
            "toActivityName",
            "toactivityname",
        )
        if raw_from_activity and raw_to_activity:
            from_guid = activity_lookup.get(str(raw_from_activity))
            to_guid = activity_lookup.get(str(raw_to_activity))
            if not from_guid or not to_guid:
                print_err(
                    f"--conditions-json 第 {i + 1} 条按 fromActivity/toActivity 定位失败："
                    f"fromActivity={raw_from_activity!r}, toActivity={raw_to_activity!r}"
                )
                return 1
            target_transition = transition_pair_lookup.get((from_guid, to_guid))
            if target_transition is None:
                transition_name = (
                    raw_condition.get("transitionname")
                    or raw_condition.get("transition")
                    or str(raw_to_activity)
                )
                target_transition = build_transition(
                    from_guid=from_guid,
                    to_guid=to_guid,
                    process_version_guid=process_version_guid,
                    name=transition_name,
                    vml_id=next_transition_vmlid,
                )
                transitions.append(target_transition)
                next_transition_vmlid += 1
                transition_lookup, transition_guid_lookup, transition_pair_lookup = _refresh_transition_lookups(transitions)
        else:
            raw_guid = raw_condition.get("transitionguid")
            if raw_guid:
                target_transition = transition_guid_lookup.get(raw_guid)
            if target_transition is None:
                raw_name = (
                    raw_condition.get("transition")
                    or raw_condition.get("transitionname")
                    or raw_condition.get("targetTransition")
                    or raw_condition.get("targettransition")
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
            print_err(
                f"--conditions-json 第 {i + 1} 条无法定位 transition，请提供 "
                "transitionguid/transition/transitionIndex 或 fromActivity/toActivity"
            )
            return 1
        target_transition["is_default"] = 20
        normalized_condition = _normalize_condition(
            raw_condition,
            process_version_guid,
            target_transition["transitionguid"],
            i,
        )
        normalized_condition["transitionguid"] = target_transition["transitionguid"]
        target_transition.setdefault("workflowTransitionCondition", []).append(normalized_condition)

    for i, transition in enumerate(transitions):
        condition_error = _validate_transition_conditions(transition, i)
        if condition_error:
            print_err(condition_error)
            return 1

    _apply_optional_branch_layout(activities, transitions)

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

    if args.dry_run:
        print_ok(f"workflow dry-run 通过: {target}")
    else:
        workflow_dir.mkdir(parents=True, exist_ok=True)
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
    if page_read or page_rw:
        print_info(f"  - 材料只读页: {page_read or '未解析到详情页 pagetag'}")
        print_info(f"  - 材料读写页: {page_rw or '未解析到表单页 pagetag'}")
        print_info("  - 提示：移动端材料 pageurl 暂不自动填充")
    else:
        print_info("  - 提示：未解析到 pagetag，材料 pageurl_read/pageurl_readandwrite 暂为空")
    if not args.sql_tablename:
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
               "条件分支需用显式互补条件，不能只靠默认变迁；开始/结束/申请节点名称固定")
    print_info(f"  [5] 过引擎校验：python scripts/validate_yml.py {target}")
    print_info("       → 错误数 = 0 才算交付；整应用还要跑 validate_yml.py --strict --check-refs <app-root>")

    # ============================================================
    # spec v2 主动追问引导（软约束，提醒上层 LLM 别漏问扩展能力）
    # ============================================================
    missing_extras = []
    if not activity_extra_raw:
        missing_extras.append(
            "--activity-extra-json（超时提醒/短信通知/多人锁定时间/小程序规则/多路汇合）"
        )
    if not approve_pass_rate_raw:
        missing_extras.append(
            "--approve-pass-rate-json（通过率/多人会签 X% 通过/未通过处理策略）"
        )
    if not activity_materials_raw:
        missing_extras.append(
            "--activity-materials-json（节点字段权限：只读/隐藏/必填、字段级 workflowActivityFieldAccess）"
        )
    if not conditions_raw:
        missing_extras.append(
            "--conditions-json（流转条件分支：金额>X 走A否则走B；否则需互补条件，跨节点可用 fromActivity/toActivity）"
        )
    if not workflow_methods:
        missing_extras.append(
            "--methods-json（外部方法 / 业务方法调用，可关联动作流 ruleguid）"
        )
    if not workflow_events:
        missing_extras.append(
            "--events-json（流程事件钩子：操作前后/活动创建后/完成后）"
        )
    if not workflow_contexts:
        missing_extras.append(
            "--contexts-json（相关数据 workflowContext，用于流转条件 [#=jine#] 等表达式）"
        )
    if missing_extras:
        print_info("")
        print_info(
            "🟡 spec v2 主动追问引导：本次未注入下列扩展能力。"
            "若需求里出现对应关键词，必须先与用户确认后用对应入参重生成（不要默认就跳过）："
        )
        for tip in missing_extras:
            print_info(f"   - {tip}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
