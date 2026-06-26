#!/usr/bin/env python3
"""validate_ir.py — 校验 lowcode-dsl-gen IR 中间语言.

校验范围保持轻量且可执行：
- 顶层字段与 application 必填项
- asset id 唯一、type/status 枚举
- dependencies 引用存在且无环
- open_questions 未解决时阻断生成
- workflow/event 的关键 spec 必填项
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _common import print_err, print_info, print_ok, print_warn, yaml_load  # noqa: E402


ASSET_TYPES = {
    "app-shell", "codeitem", "mis", "module", "pagedesigne", "workflow", "event",
}
ASSET_STATUS = {"pending", "generating", "validating", "done", "failed", "skipped"}
QUESTION_STATUS = {"pending", "resolved"}
APPTAG_RE = re.compile(r"^[a-z][a-z0-9]*$")
FIELD_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
BARE_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SOURCE_VALUES = {"user_confirmed", "repo_inferred", "safe_default", "model_inferred"}
TASK_MODES = {"whole-app", "greenfield-app", "existing-app", "asset-fast", "plan-only"}
WORKFLOW_OPERATION_MODES = {"create", "revise-plan", "update-existing"}
SPECIAL_QUESTION_TARGETS = {"application", "task", "global"}
WHOLE_APP_KEYWORDS = ("完整应用", "完整生成", "整个应用", "整应用", "根据 PRD", "需求文档", "会议纪要")

QUESTION_REQUIRED_FIELDS = ("id", "target", "field", "severity", "question", "status")
QUESTION_SEVERITY = {"blocking", "confirm", "info"}
QUESTION_REQUIRED_SEVERITY = {"blocking", "confirm"}
SAFE_DEFAULT_FIELDS = {
    "pagedesigne.device",
}
APPLICATION_SOURCE_RULES = {
    "developerstag": {"user_confirmed", "repo_inferred"},
    "kitid": {"user_confirmed", "repo_inferred"},
    "categories": {"user_confirmed", "repo_inferred"},
    "baseouguid": {"user_confirmed", "repo_inferred", "safe_default"},
    "tenantguid": {"user_confirmed", "repo_inferred", "safe_default"},
}
APP_SHELL_CONFIRMATION_FIELDS = {
    "developerstag": "开发商标识",
    "kitid": "套件标识",
    "categories": "应用分类",
    "appref": "应用引用配置",
}
WORKFLOW_CONFIRMATION_FIELDS = {
    "processGoal": "流程目标/实现效果",
    "activityChain": "节点链路",
    "transactors": "处理人来源",
    "conditions": "条件分支",
    "pageTags": "表单/详情页 pagetag",
    "sqlTableName": "关联 MIS 表",
    "fieldPermissions": "字段权限",
    "approvePassRate": "会签/通过率",
    "timeout": "超时提醒",
    "eventLinkage": "状态联动/event 需求",
}


class IRValidation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def report(self) -> int:
        for msg in self.errors:
            print_err(msg)
        for msg in self.warnings:
            print_warn(msg)
        if self.errors:
            print_info(f"IR 校验失败：错误 {len(self.errors)}，警告 {len(self.warnings)}")
            return 1
        print_ok(f"IR 校验通过：警告 {len(self.warnings)}")
        return 0


def _is_obj(value: Any) -> bool:
    return isinstance(value, dict)


def _is_list(value: Any) -> bool:
    return isinstance(value, list)


def _required_obj(result: IRValidation, obj: dict, field: str, path: str) -> dict:
    value = obj.get(field)
    if not _is_obj(value):
        result.err(f"{path}.{field} 必须是对象")
        return {}
    return value


def _required_list(result: IRValidation, obj: dict, field: str, path: str) -> list:
    value = obj.get(field)
    if not _is_list(value):
        result.err(f"{path}.{field} 必须是数组")
        return []
    return value


def _nested_get(obj: Any, path: str) -> Any:
    if not isinstance(obj, dict):
        return None
    if path in obj:
        return obj[path]
    current: Any = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _source_from_value(value: Any) -> str | None:
    if isinstance(value, dict):
        source = value.get("source") or value.get("_source")
        return str(source) if source not in (None, "") else None
    return None


def _source_from_container(container: Any, path: str) -> str | None:
    if not isinstance(container, dict):
        return None
    source = _nested_get(container, path)
    return str(source) if source not in (None, "") else None


def _source_for_application(data: dict, field: str) -> str | None:
    app = data.get("application") or {}
    candidates = (
        _source_from_container(data.get("sources"), f"application.{field}"),
        _source_from_container(data.get("sources"), field),
        _source_from_container(data.get("applicationSources"), field),
        _source_from_container(app.get("sources"), field),
        _source_from_container(app.get("_sources"), field),
        _source_from_value(app.get(field)),
    )
    return next((source for source in candidates if source), None)


def _source_for_task(data: dict, field: str) -> str | None:
    task = data.get("task") if isinstance(data.get("task"), dict) else {}
    candidates = (
        _source_from_container(data.get("sources"), f"task.{field}"),
        _source_from_container(data.get("sources"), field),
        _source_from_container(data.get("taskSources"), field),
        _source_from_container(task.get("sources"), field),
        _source_from_container(task.get("_sources"), field),
        _source_from_value(task.get(field)),
        _source_from_value(data.get(field)),
    )
    return next((source for source in candidates if source), None)


def _source_container_for_application(data: dict) -> dict:
    app = data.get("application")
    if not isinstance(app, dict):
        return {}
    sources = app.get("sourceDetails") or app.get("evidence") or app.get("sourceEvidence")
    return sources if isinstance(sources, dict) else {}


def _source_container_for_task(data: dict) -> dict:
    task = data.get("task")
    if not isinstance(task, dict):
        return {}
    sources = task.get("sourceDetails") or task.get("evidence") or task.get("sourceEvidence")
    return sources if isinstance(sources, dict) else {}


def _source_for_asset_field(asset: dict, field: str) -> str | None:
    spec = asset.get("spec") if isinstance(asset.get("spec"), dict) else {}
    candidates = (
        _source_from_container(asset.get("sources"), field),
        _source_from_container(asset.get("_sources"), field),
        _source_from_container(spec.get("sources"), field),
        _source_from_container(spec.get("_sources"), field),
        _source_from_container(spec.get("source"), field) if isinstance(spec.get("source"), dict) else None,
        _source_from_value(_nested_get(spec, field.removeprefix("workflow.").removeprefix("event.").removeprefix("app-shell."))),
    )
    return next((source for source in candidates if source), None)


def _field_evidence(container: Any, field: str) -> Any:
    if not isinstance(container, dict):
        return None
    candidates = (
        field,
        field.removeprefix("application."),
        field.removeprefix("app-shell."),
        field.removeprefix("workflow."),
        field.removeprefix("confirmations."),
    )
    for candidate in candidates:
        value = _nested_get(container, candidate)
        if value not in (None, ""):
            return value
    return None


def _list_from_value(value: Any) -> list:
    if value in (None, ""):
        return []
    return value if isinstance(value, list) else [value]


def _question_ids_from_value(value: Any) -> list[str]:
    if isinstance(value, dict):
        values = (
            value.get("questionId"),
            value.get("question_id"),
            value.get("openQuestionId"),
            value.get("open_question_id"),
            value.get("interactionId"),
            value.get("interaction_id"),
        )
        ids: list[str] = []
        for item in values:
            ids.extend(str(v) for v in _list_from_value(item) if not _is_blank(v))
        for key in ("questionIds", "question_ids", "openQuestionIds", "open_question_ids"):
            ids.extend(str(v) for v in _list_from_value(value.get(key)) if not _is_blank(v))
        return ids
    return []


def _has_repo_evidence(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_repo_evidence(item) for item in value)
    if isinstance(value, dict):
        for key in (
            "path",
            "paths",
            "file",
            "files",
            "appRoot",
            "app_root",
            "repoPath",
            "repo_path",
            "evidence",
            "repoEvidence",
            "repo_evidence",
        ):
            if _has_repo_evidence(value.get(key)):
                return True
    return False


def _question_ids_for_field(value: Any, fallback_question: dict | None = None) -> list[str]:
    ids = _question_ids_from_value(value)
    if fallback_question and fallback_question.get("id"):
        ids.append(str(fallback_question.get("id")))
    return ids


def _validate_question_ids(
    result: IRValidation,
    question_ids: list[str],
    known_question_ids: set[str],
    path: str,
) -> bool:
    if not question_ids:
        result.err(f"{path} source=user_confirmed 但缺少 questionId/interactionId 证据")
        return False
    ok = True
    for question_id in question_ids:
        if question_id not in known_question_ids:
            result.err(f"{path} 引用的确认问题不存在: {question_id}")
            ok = False
    return ok


def _validate_source_evidence(
    result: IRValidation,
    source: str | None,
    evidence: Any,
    path: str,
    known_question_ids: set[str],
    *,
    fallback_question: dict | None = None,
    require_safe_default_reason: bool = False,
) -> None:
    if source == "user_confirmed":
        _validate_question_ids(
            result,
            _question_ids_for_field(evidence, fallback_question),
            known_question_ids,
            path,
        )
    elif source == "repo_inferred":
        if not _has_repo_evidence(evidence):
            result.err(f"{path} source=repo_inferred 但缺少 repoEvidence/path 等可验证仓库证据")
    elif source == "safe_default" and require_safe_default_reason:
        if not isinstance(evidence, dict) or _is_blank(evidence.get("reason")):
            result.err(f"{path} source=safe_default 必须记录 reason 说明安全默认值")


def _validate_source(
    result: IRValidation,
    source: str | None,
    path: str,
    allowed: set[str] | None = None,
) -> bool:
    if source in (None, ""):
        result.err(f"{path} 缺少来源标记 source（user_confirmed/repo_inferred/safe_default/model_inferred）")
        return False
    if source not in SOURCE_VALUES:
        result.err(f"{path} source 非法: {source}")
        return False
    if source == "model_inferred":
        result.err(f"{path} source=model_inferred，不能进入生成/批准")
        return False
    if allowed and source not in allowed:
        result.err(f"{path} source={source} 不允许；允许值: {', '.join(sorted(allowed))}")
        return False
    return True


def _question_or_source_error(
    result: IRValidation,
    question_index: dict[tuple[str, str], dict],
    target: str,
    field: str,
    reason: str,
) -> None:
    question = _question_for(question_index, target, field)
    if question:
        if question.get("status") == "resolved":
            result.err(f"{target}.{field} 已 resolved，但仍缺少来源/确认信息：{reason}")
        return
    _require_question(result, question_index, target, field, reason)


def _check_application(result: IRValidation, data: dict) -> None:
    app = _required_obj(result, data, "application", "$")
    for field in ("apptag", "applicationname", "developerstag", "kitid"):
        if not app.get(field):
            result.err(f"application.{field} 必填")
    apptag = app.get("apptag")
    if apptag and not APPTAG_RE.match(str(apptag)):
        result.err(f"application.apptag 不合法: {apptag}")


def _check_application_sources(
    result: IRValidation,
    data: dict,
    question_index: dict[tuple[str, str], dict],
    known_question_ids: set[str],
) -> None:
    evidence_container = _source_container_for_application(data)
    for field, allowed in APPLICATION_SOURCE_RULES.items():
        source = _source_for_application(data, field)
        question = _question_for(question_index, "application", f"application.{field}") or _question_for(question_index, "application", field)
        if source in (None, ""):
            _question_or_source_error(
                result,
                question_index,
                "application",
                f"application.{field}",
                f"应用基础信息 {field} 未记录来源",
            )
            continue
        if _validate_source(result, source, f"application.{field}", allowed):
            evidence = _field_evidence(evidence_container, field)
            _validate_source_evidence(
                result,
                source,
                evidence,
                f"application.{field}",
                known_question_ids,
                fallback_question=question,
                require_safe_default_reason=True,
            )


def _task_field(data: dict, field: str) -> Any:
    for container_name in ("task", "intent"):
        container = data.get(container_name)
        if isinstance(container, dict):
            for key in (field, field.replace("_", ""), field.replace("_", "-")):
                if key in container:
                    return container[key]
    for key in (field, field.replace("_", ""), field.replace("_", "-")):
        if key in data:
            return data[key]
    return None


def _check_task_mode(
    result: IRValidation,
    data: dict,
    question_index: dict[tuple[str, str], dict],
    known_question_ids: set[str],
) -> None:
    mode = _task_field(data, "taskMode") or _task_field(data, "task_mode") or _task_field(data, "mode")
    if _is_blank(mode):
        _require_question(result, question_index, "task", "task.mode", "未确认任务模式：整应用、新建应用、已有应用补充、资产级快速通道或仅生成计划")
        return
    mode = str(mode)
    if mode not in TASK_MODES:
        result.err(f"task.mode 非法: {mode}；允许值: {', '.join(sorted(TASK_MODES))}")
    source = _source_for_task(data, "taskMode") or _source_for_task(data, "mode")
    if source in (None, ""):
        _question_or_source_error(result, question_index, "task", "task.mode", "任务模式未记录来源")
    else:
        if _validate_source(result, source, "task.mode", {"user_confirmed", "repo_inferred"}):
            evidence_container = _source_container_for_task(data)
            evidence = (
                _field_evidence(evidence_container, "mode")
                or _field_evidence(evidence_container, "task.mode")
                or _field_evidence(evidence_container, "taskMode")
            )
            question = _question_for(question_index, "task", "task.mode") or _question_for(question_index, "task", "mode")
            _validate_source_evidence(
                result,
                source,
                evidence,
                "task.mode",
                known_question_ids,
                fallback_question=question,
            )
            if mode == "whole-app":
                prompt_text = ""
                if isinstance(evidence, dict):
                    prompt_text = str(evidence.get("answer") or evidence.get("userReply") or evidence.get("user_reply") or evidence.get("text") or "")
                elif isinstance(evidence, str):
                    prompt_text = evidence
                if source == "user_confirmed" and not any(keyword in prompt_text for keyword in WHOLE_APP_KEYWORDS):
                    result.err(
                        "task.mode=whole-app 必须有用户明确的整应用/PRD/需求文档语义；"
                        "不能仅凭推荐项或 apptag 回复升级为 whole-app"
                    )

    requested = (
        _task_field(data, "requestedAssetTypes")
        or _task_field(data, "requested_asset_types")
        or _task_field(data, "requestedAssets")
        or []
    )
    if mode == "asset-fast":
        if not isinstance(requested, list) or not requested:
            _require_question(result, question_index, "task", "task.requestedAssetTypes", "资产级快速通道必须记录用户明确请求的资产类型")
            return
        requested_set = {str(item) for item in requested}
        asset_types = {
            str(asset.get("type"))
            for asset in data.get("assets") or []
            if isinstance(asset, dict) and asset.get("type")
        }
        extra = sorted(asset_types - requested_set)
        if extra:
            result.err(
                "资产级快速通道只允许生成用户明确请求的资产类型；"
                f"requestedAssetTypes={sorted(requested_set)}, 但 IR 包含 {extra}"
            )


def _check_app_shell_spec(
    result: IRValidation,
    asset: dict,
    question_index: dict[tuple[str, str], dict],
    known_question_ids: set[str],
) -> None:
    asset_id = asset.get("id", "<unknown>")
    spec = asset.get("spec") or {}
    create_dirs = spec.get("createDirs")
    if create_dirs is not None and not isinstance(create_dirs, list):
        result.err(f"{asset_id}.spec.createDirs 必须是数组")
    appref = spec.get("appref")
    if appref is not None and not isinstance(appref, dict):
        result.err(f"{asset_id}.spec.appref 必须是对象")
    if spec.get("actionRootRequired") and _is_blank(spec.get("actionRoot")):
        _require_question(result, question_index, asset_id, "app-shell.actionRoot", "无法确定 action 子工程根目录")
    if spec.get("categoriesRequired") and not spec.get("categories"):
        _require_question(result, question_index, asset_id, "app-shell.categories", "无法确定应用分类目录")
    appref_source = (
        _source_for_asset_field(asset, "app-shell.appref")
        or _source_for_asset_field(asset, "appref")
    )
    if appref_source in (None, ""):
        _question_or_source_error(result, question_index, asset_id, "app-shell.appref", "appref 启用/不启用未记录来源")
    else:
        if _validate_source(result, appref_source, f"{asset_id}.app-shell.appref", {"user_confirmed", "repo_inferred", "safe_default"}):
            evidence = _field_evidence(spec.get("sourceDetails") or spec.get("evidence") or {}, "appref")
            question = _question_for(question_index, asset_id, "app-shell.appref") or _question_for(question_index, "application", "app-shell.appref")
            _validate_source_evidence(
                result,
                appref_source,
                evidence,
                f"{asset_id}.app-shell.appref",
                known_question_ids,
                fallback_question=question,
                require_safe_default_reason=True,
            )

    confirmations = spec.get("confirmations")
    if confirmations is not None:
        if not isinstance(confirmations, dict):
            result.err(f"{asset_id}.spec.confirmations 必须是对象")
        else:
            for field, label in APP_SHELL_CONFIRMATION_FIELDS.items():
                value = confirmations.get(field)
                if value is None:
                    _require_question(result, question_index, asset_id, f"app-shell.confirmations.{field}", f"{label} 未确认")
                    continue
                status = _confirmation_status(value)
                if status not in {"confirmed", "not_required"}:
                    result.err(f"{asset_id}.app-shell.confirmations.{field} 状态非法: {status}")
                source = _confirmation_source(asset, f"app-shell.confirmations.{field}", value)
                if _validate_source(result, source, f"{asset_id}.app-shell.confirmations.{field}", {"user_confirmed", "repo_inferred", "safe_default"}):
                    question = _question_for(question_index, asset_id, f"app-shell.confirmations.{field}")
                    _validate_source_evidence(
                        result,
                        source,
                        value,
                        f"{asset_id}.app-shell.confirmations.{field}",
                        known_question_ids,
                        fallback_question=question,
                        require_safe_default_reason=True,
                    )


def _check_codeitem_spec(
    result: IRValidation,
    asset: dict,
    index: int,
    question_index: dict[tuple[str, str], dict],
) -> None:
    asset_id = asset.get("id", f"assets[{index}]")
    spec = asset.get("spec") or {}
    path = f"assets[{index}].spec"
    if _is_blank(spec.get("name")):
        _require_question(result, question_index, asset_id, "codeitem.name", "代码项名称缺失")
    items = spec.get("items")
    if not isinstance(items, list) or not items:
        _require_question(result, question_index, asset_id, "codeitem.items", "代码项子项缺失")
        return
    for j, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            result.err(f"{path}.items[{j}] 必须是对象")
            continue
        if _is_blank(item.get("codetext")):
            _require_question(result, question_index, asset_id, f"codeitem.items[{j}].codetext", "代码项文本缺失")
        if _is_blank(item.get("codevalue")):
            _require_question(result, question_index, asset_id, f"codeitem.items[{j}].codevalue", "代码项值缺失")


def _check_mis_spec(
    result: IRValidation,
    asset: dict,
    index: int,
    question_index: dict[tuple[str, str], dict],
) -> None:
    asset_id = asset.get("id", f"assets[{index}]")
    spec = asset.get("spec") or {}
    path = f"assets[{index}].spec"
    for field, reason in (
        ("tableName", "数据表名缺失"),
        ("tableChineseName", "数据表中文名缺失"),
    ):
        if _is_blank(spec.get(field)):
            _require_question(result, question_index, asset_id, f"mis.{field}", reason)
    table_name = spec.get("tableName")
    if table_name and not APPTAG_RE.match(str(table_name)):
        result.err(f"{path}.tableName 不合法: {table_name}（应为小写字母开头 + 字母/数字，不含下划线）")
    fields = spec.get("fields")
    if not isinstance(fields, list) or not fields:
        _require_question(result, question_index, asset_id, "mis.fields", "字段列表缺失")
        return
    for j, field in enumerate(fields, start=1):
        if not isinstance(field, dict):
            result.err(f"{path}.fields[{j}] 必须是对象")
            continue
        checks = (
            ("fieldName", "字段名缺失"),
            ("fieldType", "字段类型缺失"),
            ("chineseName", "字段中文名缺失"),
        )
        for key, reason in checks:
            if _is_blank(field.get(key)):
                _require_question(result, question_index, asset_id, f"mis.fields[{j}].{key}", reason)
        field_name = field.get("fieldName")
        if field_name and not FIELD_NAME_RE.match(str(field_name)):
            result.err(f"{path}.fields[{j}].fieldName 不合法: {field_name}")
        if field.get("fieldType") in {"nvarchar", "varchar", "char"} and _is_blank(field.get("length")):
            _require_question(result, question_index, asset_id, f"mis.fields[{j}].length", "字符型字段长度缺失")
        for bool_field in ("mustfill", "unique"):
            if bool_field in field and not isinstance(field.get(bool_field), bool):
                result.err(f"{path}.fields[{j}].{bool_field} 必须是布尔值")
        if field.get("datasourceCodename") and not isinstance(field.get("datasourceCodename"), str):
            result.err(f"{path}.fields[{j}].datasourceCodename 必须是字符串")


def _check_module_spec(
    result: IRValidation,
    asset: dict,
    question_index: dict[tuple[str, str], dict],
) -> None:
    asset_id = asset.get("id", "<unknown>")
    spec = asset.get("spec") or {}
    if _is_blank(spec.get("name")):
        _require_question(result, question_index, asset_id, "module.name", "模块名称缺失")
    if _is_blank(spec.get("code")):
        _require_question(result, question_index, asset_id, "module.code", "模块编码缺失")
    if spec.get("subModules") is not None and not isinstance(spec.get("subModules"), list):
        result.err(f"{asset_id}.spec.subModules 必须是数组")


def _check_pagedesigne_spec(
    result: IRValidation,
    asset: dict,
    question_index: dict[tuple[str, str], dict],
) -> None:
    asset_id = asset.get("id", "<unknown>")
    spec = asset.get("spec") or {}
    for field, reason in (
        ("title", "页面标题缺失"),
        ("pagetag", "页面 pagetag 缺失"),
        ("pageType", "页面类型缺失"),
        ("endpoint", "接口 endpoint 缺失"),
    ):
        if _is_blank(spec.get(field)):
            _require_question(result, question_index, asset_id, f"pagedesigne.{field}", reason)
    device = spec.get("device")
    if _is_blank(device):
        result.warn(f"{asset_id}.pagedesigne.device 未设置，默认 desktop；请在计划 assumptions 中记录")
    elif device not in {"desktop", "mobile"}:
        result.err(f"{asset_id}.spec.device 非法: {device}")
    fields = spec.get("fields")
    if not isinstance(fields, list) or not fields:
        _require_question(result, question_index, asset_id, "pagedesigne.fields", "页面字段列表缺失")
    query = spec.get("query")
    if query is not None and not isinstance(query, list):
        result.err(f"{asset_id}.spec.query 必须是数组")


def _question_key(target: str, field: str) -> tuple[str, str]:
    return str(target), str(field)


def _question_for(question_index: dict[tuple[str, str], dict], target: str, field: str) -> dict | None:
    return question_index.get(_question_key(target, field))


def _require_question(
    result: IRValidation,
    question_index: dict[tuple[str, str], dict],
    target: str,
    field: str,
    reason: str,
) -> None:
    display_path = field if field.startswith(f"{target}.") else f"{target}.{field}"
    if field in SAFE_DEFAULT_FIELDS:
        result.warn(f"{display_path} 使用安全默认值，请在计划 assumptions/阶段确认结果中记录")
        return
    question = _question_for(question_index, target, field)
    if not question:
        result.err(
            f"{display_path} 存在待人工确认疑点：{reason}；"
            f"请在 open_questions 中新增 target={target}, field={field}, status=pending"
        )
        return
    if question.get("status") == "resolved":
        result.err(
            f"{display_path} 已在 open_questions 中 resolved，但 spec 仍缺失；"
            "请把 resolvedValue 回填到对应 spec 字段后再生成"
        )


def _is_blank(value: Any) -> bool:
    return value in (None, "")


def _question_index(result: IRValidation, data: dict, asset_ids: set[str]) -> dict[tuple[str, str], dict]:
    questions = data.get("open_questions", [])
    index: dict[tuple[str, str], dict] = {}
    if questions is None:
        return index
    if not _is_list(questions):
        result.err("open_questions 必须是数组")
        return index
    for i, question in enumerate(questions, start=1):
        if not _is_obj(question):
            result.err(f"open_questions[{i}] 必须是对象")
            continue
        for field in QUESTION_REQUIRED_FIELDS:
            if _is_blank(question.get(field)):
                result.err(f"open_questions[{i}].{field} 必填")
        target = question.get("target")
        if target and target not in asset_ids and target not in SPECIAL_QUESTION_TARGETS:
            result.err(f"open_questions[{i}].target 引用不存在的 asset: {target}")
        field = question.get("field")
        if target and field:
            key = _question_key(str(target), str(field))
            if key in index:
                result.err(f"open_questions[{i}] 重复确认项: target={target}, field={field}")
            index[key] = question
        severity = question.get("severity", "blocking")
        if severity not in QUESTION_SEVERITY:
            result.err(f"open_questions[{i}].severity 非法: {severity}")
        if question.get("options") is not None and not isinstance(question.get("options"), list):
            result.err(f"open_questions[{i}].options 必须是数组")
        if "recommended" in question and question.get("recommended") not in (None, ""):
            options = question.get("options")
            if isinstance(options, list) and options and question.get("recommended") not in options:
                result.err(f"open_questions[{i}].recommended 必须来自 options")
        status = question.get("status", "pending")
        if status not in QUESTION_STATUS:
            result.err(f"open_questions[{i}].status 非法: {status}")
        if status == "pending":
            result.err(f"open_questions[{i}] 仍为 pending，不能进入生成")
        if status == "resolved":
            if question.get("severity", "blocking") in QUESTION_REQUIRED_SEVERITY:
                if _is_blank(question.get("answer")):
                    result.err(f"open_questions[{i}].answer 必填（resolved 时必须回填人工回复）")
                if "resolvedValue" not in question:
                    result.err(f"open_questions[{i}].resolvedValue 必填（resolved 时必须回填解析值）")
    return index


def _condition_type(condition: dict) -> int | None:
    try:
        return int(condition.get("conditionexpressiontype", 10))
    except (TypeError, ValueError):
        return None


def _confirmation_value(spec: dict, field: str) -> Any:
    confirmations = spec.get("confirmations")
    if not isinstance(confirmations, dict):
        return None
    return confirmations.get(field)


def _confirmation_status(value: Any) -> str:
    if value is True:
        return "confirmed"
    if value is False or value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        status = value.get("status")
        if status in (None, "") and value.get("confirmed") is True:
            return "confirmed"
        return str(status or "")
    return ""


def _confirmation_source(asset: dict, field: str, value: Any) -> str | None:
    if isinstance(value, dict):
        source = value.get("source") or value.get("_source")
        if source not in (None, ""):
            return str(source)
    return (
        _source_for_asset_field(asset, f"workflow.confirmations.{field}")
        or _source_for_asset_field(asset, field)
        or _source_for_asset_field(asset, f"confirmations.{field}")
    )


def _check_workflow_confirmations(
    result: IRValidation,
    asset: dict,
    question_index: dict[tuple[str, str], dict],
    known_question_ids: set[str],
) -> None:
    asset_id = asset.get("id", "<unknown>")
    spec = asset.get("spec") or {}
    confirmations = spec.get("confirmations")
    if not isinstance(confirmations, dict):
        _require_question(result, question_index, asset_id, "workflow.confirmations", "工作流实现效果确认矩阵缺失")
        return

    core_fields = {"processGoal", "activityChain", "transactors", "pageTags", "sqlTableName"}
    optional_fields = {"fieldPermissions", "approvePassRate", "timeout", "eventLinkage"}
    for field, label in WORKFLOW_CONFIRMATION_FIELDS.items():
        value = _confirmation_value(spec, field)
        status = _confirmation_status(value)
        field_path = f"workflow.confirmations.{field}"
        if not status:
            _require_question(result, question_index, asset_id, field_path, f"{label} 未确认")
            continue
        allowed_status = {"confirmed"} if field in core_fields else {"confirmed", "skipped", "not_required"}
        if field == "conditions" and not spec.get("conditions"):
            allowed_status = {"confirmed", "skipped", "not_required"}
        if status not in allowed_status:
            result.err(
                f"{asset_id}.{field_path} 状态非法: {status}；"
                f"{label} 允许值: {', '.join(sorted(allowed_status))}"
            )
        source = _confirmation_source(asset, field, value)
        if source in (None, ""):
            _question_or_source_error(result, question_index, asset_id, field_path, f"{label} 缺少确认来源")
        else:
            if _validate_source(result, source, f"{asset_id}.{field_path}", {"user_confirmed", "repo_inferred"}):
                question = _question_for(question_index, asset_id, field_path)
                _validate_source_evidence(
                    result,
                    source,
                    value,
                    f"{asset_id}.{field_path}",
                    known_question_ids,
                    fallback_question=question,
                )

    if spec.get("activityMaterials") and _confirmation_status(_confirmation_value(spec, "fieldPermissions")) != "confirmed":
        result.err(f"{asset_id}.workflow.confirmations.fieldPermissions 必须为 confirmed，因为 IR 包含 activityMaterials")
    if spec.get("approvePassRate") and _confirmation_status(_confirmation_value(spec, "approvePassRate")) != "confirmed":
        result.err(f"{asset_id}.workflow.confirmations.approvePassRate 必须为 confirmed，因为 IR 包含 approvePassRate")
    if spec.get("activityExtra") and _confirmation_status(_confirmation_value(spec, "timeout")) != "confirmed":
        result.err(f"{asset_id}.workflow.confirmations.timeout 必须为 confirmed，因为 IR 包含 activityExtra")
    if (spec.get("methods") or spec.get("events")) and _confirmation_status(_confirmation_value(spec, "eventLinkage")) != "confirmed":
        result.err(f"{asset_id}.workflow.confirmations.eventLinkage 必须为 confirmed，因为 IR 包含 methods/events")


def _check_workflow_spec(
    result: IRValidation,
    asset: dict,
    index: int,
    question_index: dict[tuple[str, str], dict],
    known_question_ids: set[str],
) -> None:
    asset_id = asset.get("id", f"assets[{index}]")
    spec = asset.get("spec") or {}
    path = f"assets[{index}].spec"
    operation_mode = spec.get("operationMode", "create")
    if operation_mode not in WORKFLOW_OPERATION_MODES:
        result.err(f"{path}.operationMode 非法: {operation_mode}，允许 create/revise-plan/update-existing")
    if operation_mode == "update-existing":
        target_workflow = spec.get("targetWorkflow") or {}
        target_file = (
            spec.get("targetWorkflowFile")
            or spec.get("existingWorkflowFile")
            or (target_workflow.get("file") if isinstance(target_workflow, dict) else "")
            or (target_workflow.get("path") if isinstance(target_workflow, dict) else "")
        )
        target_process_guid = (
            spec.get("processguid")
            or spec.get("processGuid")
            or (target_workflow.get("processguid") if isinstance(target_workflow, dict) else "")
            or (target_workflow.get("processGuid") if isinstance(target_workflow, dict) else "")
        )
        if _is_blank(target_file) and _is_blank(target_process_guid):
            _require_question(
                result,
                question_index,
                asset_id,
                "workflow.targetWorkflow",
                "修改已有工作流必须确认目标 .workflow.yml 或原 processguid",
            )
    rename_activities = spec.get("renameActivities")
    if rename_activities is not None and not isinstance(rename_activities, (dict, list)):
        result.err(f"{path}.renameActivities 必须是对象或数组")
    _check_workflow_confirmations(result, asset, question_index, known_question_ids)
    for field in ("processName", "activities"):
        if not spec.get(field):
            _require_question(result, question_index, asset_id, f"workflow.{field}", f"{field} 缺失")
    for field, reason in (
        ("material", "流程材料名称缺失"),
        ("sqlTableName", "流程关联 MIS 表名缺失"),
    ):
        if _is_blank(spec.get(field)):
            _require_question(result, question_index, asset_id, f"workflow.{field}", reason)
    if _is_blank(spec.get("pageTagForm")):
        _require_question(result, question_index, asset_id, "workflow.pageTagForm", "表单页 pagetag 缺失")
    if _is_blank(spec.get("pageTagDetail")):
        _require_question(result, question_index, asset_id, "workflow.pageTagDetail", "详情页 pagetag 缺失")
    activities = spec.get("activities") or []
    if not isinstance(activities, list):
        result.err(f"{path}.activities 必须是数组")
        return
    if not any(a.get("type") == "apply" for a in activities if isinstance(a, dict)):
        result.err(f"{path}.activities 必须包含 type=apply 的申请活动")
    approve_count = sum(1 for a in activities if isinstance(a, dict) and a.get("type") == "approve")
    if approve_count < 1:
        result.err(f"{path}.activities 至少需要 1 个 type=approve 的审批活动")
    for j, activity in enumerate(activities, start=1):
        if not isinstance(activity, dict):
            result.err(f"{path}.activities[{j}] 必须是对象")
            continue
        if not activity.get("name"):
            result.err(f"{path}.activities[{j}].name 必填")
        if activity.get("type") not in {"apply", "approve", "route", "subprocess"}:
            result.err(f"{path}.activities[{j}].type 非法: {activity.get('type')}")
        if activity.get("type") == "approve":
            transactor_source = (
                activity.get("transactorSource")
                or activity.get("targetactivitytransactorsource")
            )
            role_guid = activity.get("roleguid") or activity.get("roleGuid") or activity.get("targetRoleGuid")
            if _is_blank(transactor_source) or (str(transactor_source) in {"role", "30"} and _is_blank(role_guid)):
                _require_question(
                    result,
                    question_index,
                    asset_id,
                    f"workflow.activities[{j}].transactor",
                    f"审批活动“{activity.get('name', j)}”处理人来源/角色 GUID 未确认",
                )

    contexts = spec.get("contexts") or []
    if contexts and not isinstance(contexts, list):
        result.err(f"{path}.contexts 必须是数组")
        contexts = []
    context_fields = {
        ctx.get("fieldname")
        for ctx in contexts
        if isinstance(ctx, dict) and ctx.get("fieldname")
    }
    for j, ctx in enumerate(contexts, start=1):
        if not isinstance(ctx, dict):
            result.err(f"{path}.contexts[{j}] 必须是对象")
            continue
        for field in ("fieldname", "fieldtype", "valuesource", "fromfieldname"):
            if _is_blank(ctx.get(field)):
                _require_question(result, question_index, asset_id, f"workflow.contexts[{j}].{field}", f"相关数据 {field} 缺失")

    conditions = spec.get("conditions") or []
    if conditions and not isinstance(conditions, list):
        result.err(f"{path}.conditions 必须是数组")
        conditions = []
    for j, condition in enumerate(conditions, start=1):
        if not isinstance(condition, dict):
            result.err(f"{path}.conditions[{j}] 必须是对象")
            continue
        for field in ("fromActivity", "toActivity"):
            if _is_blank(condition.get(field)):
                _require_question(result, question_index, asset_id, f"workflow.conditions[{j}].{field}", f"流转条件 {field} 缺失")
        ctype = _condition_type(condition)
        if ctype is None:
            result.err(f"{path}.conditions[{j}].conditionexpressiontype 必须是 10/20/30")
            continue
        if ctype == 10:
            for field in ("leftvalue", "compareoperation", "rightvalue", "valuetype"):
                if _is_blank(condition.get(field)):
                    _require_question(result, question_index, asset_id, f"workflow.conditions[{j}].{field}", f"单一表达式条件 {field} 缺失")
            leftvalue = str(condition.get("leftvalue") or "")
            if leftvalue and BARE_FIELD_RE.match(leftvalue) and "[#=" not in leftvalue:
                result.err(
                    f"{path}.conditions[{j}].leftvalue='{leftvalue}' 缺少工作流占位符格式 [#=...#]；"
                    f"正确写法应为 '[#={leftvalue}#]'"
                )
            for token in re.findall(r"\[#=([A-Za-z][A-Za-z0-9_]*)#\]", leftvalue):
                if token not in context_fields:
                    _require_question(
                        result,
                        question_index,
                        asset_id,
                        f"workflow.contexts.{token}",
                        f"条件引用 [#={token}#]，但 workflowContext 未定义该 fieldname",
                    )
        elif ctype == 20:
            if _is_blank(condition.get("conditionexpression")):
                _require_question(result, question_index, asset_id, f"workflow.conditions[{j}].conditionexpression", "复杂表达式缺失")
        elif ctype == 30:
            if _is_blank(condition.get("methodguid")) and _is_blank(condition.get("ruleguid")):
                _require_question(result, question_index, asset_id, f"workflow.conditions[{j}].methodOrRule", "外部方法/规则条件入口缺失")
        else:
            result.err(f"{path}.conditions[{j}].conditionexpressiontype 非法: {ctype}")

    for field, entries in (("methods", spec.get("methods") or []), ("events", spec.get("events") or [])):
        if entries and not isinstance(entries, list):
            result.err(f"{path}.{field} 必须是数组")


def _check_event_spec(
    result: IRValidation,
    asset: dict,
    index: int,
    question_index: dict[tuple[str, str], dict],
) -> None:
    asset_id = asset.get("id", f"assets[{index}]")
    spec = asset.get("spec") or {}
    path = f"assets[{index}].spec"
    for field in ("name", "sign", "triggerType"):
        if not spec.get(field):
            _require_question(result, question_index, asset_id, f"event.{field}", f"{field} 缺失")
    trigger = spec.get("triggerType")
    if trigger and trigger not in {"webhook", "form", "schedule", "custom", "workflow"}:
        result.err(f"{path}.triggerType 非法: {trigger}")
    nodes = spec.get("nodes", [])
    has_standard_args = spec.get("bizAction") and spec.get("contextClass")
    if nodes and not isinstance(nodes, list):
        result.err(f"{path}.nodes 必须是数组")
    if not nodes and not has_standard_args:
        _require_question(result, question_index, asset_id, "event.nodesOrStandardArgs", "缺少 nodes，且缺少标准三段式参数 bizAction/contextClass")
    if trigger == "webhook" and _is_blank(spec.get("webhookUrl")):
        _require_question(result, question_index, asset_id, "event.webhookUrl", "webhook 触发地址未确认")
    if has_standard_args:
        for field in ("bizAction", "contextClass"):
            if _is_blank(spec.get(field)):
                _require_question(result, question_index, asset_id, f"event.{field}", f"标准三段式 {field} 缺失")
    if nodes:
        for j, node in enumerate(nodes, start=1):
            if not isinstance(node, dict):
                result.err(f"{path}.nodes[{j}] 必须是对象")
                continue
            if node.get("type") in {"table", "data-table", "query", "insert", "update", "delete"}:
                if _is_blank(node.get("tableName")) and _is_blank(node.get("tableId")):
                    _require_question(result, question_index, asset_id, f"event.nodes[{j}].table", "数据表操作缺少 tableName/tableId")
                if not node.get("fieldMappings") and not node.get("queryFields"):
                    _require_question(result, question_index, asset_id, f"event.nodes[{j}].fieldMappings", "数据表操作字段映射缺失")


def _check_assets(result: IRValidation, data: dict, question_index: dict[tuple[str, str], dict]) -> set[str]:
    assets = _required_list(result, data, "assets", "$")
    ids: set[str] = set()
    dep_map: dict[str, list[str]] = {}
    for i, asset in enumerate(assets, start=1):
        if not _is_obj(asset):
            result.err(f"assets[{i}] 必须是对象")
            continue
        asset_id = asset.get("id")
        if not asset_id:
            result.err(f"assets[{i}].id 必填")
            continue
        if asset_id in ids:
            result.err(f"asset id 重复: {asset_id}")
        ids.add(asset_id)
        asset_type = asset.get("type")
        if asset_type not in ASSET_TYPES:
            result.err(f"{asset_id}.type 非法: {asset_type}")
        status = asset.get("status")
        if status not in ASSET_STATUS:
            result.err(f"{asset_id}.status 非法: {status}")
        if not _is_obj(asset.get("spec")):
            result.err(f"{asset_id}.spec 必须是对象")
        deps = asset.get("dependencies", [])
        if deps is None:
            deps = []
        if not isinstance(deps, list):
            result.err(f"{asset_id}.dependencies 必须是数组")
            deps = []
        dep_map[asset_id] = deps
        if asset_type == "app-shell":
            _check_app_shell_spec(result, asset, question_index, _known_question_ids(data))
        elif asset_type == "codeitem":
            _check_codeitem_spec(result, asset, i, question_index)
        elif asset_type == "mis":
            _check_mis_spec(result, asset, i, question_index)
        elif asset_type == "module":
            _check_module_spec(result, asset, question_index)
        elif asset_type == "pagedesigne":
            _check_pagedesigne_spec(result, asset, question_index)
        elif asset_type == "workflow":
            _check_workflow_spec(result, asset, i, question_index, _known_question_ids(data))
        elif asset_type == "event":
            _check_event_spec(result, asset, i, question_index)

    for asset_id, deps in dep_map.items():
        for dep in deps:
            if dep not in ids:
                result.err(f"{asset_id}.dependencies 引用不存在的 asset: {dep}")

    _check_acyclic(result, dep_map)
    return ids


def _check_acyclic(result: IRValidation, dep_map: dict[str, list[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle = " -> ".join(stack + [node])
            result.err(f"assets.dependencies 存在环: {cycle}")
            return
        visiting.add(node)
        for dep in dep_map.get(node, []):
            if dep in dep_map:
                visit(dep, stack + [node])
        visiting.remove(node)
        visited.add(node)

    for node in dep_map:
        visit(node, [])


def _collect_asset_ids(data: dict) -> set[str]:
    assets = data.get("assets")
    if not isinstance(assets, list):
        return set()
    return {
        str(asset.get("id"))
        for asset in assets
        if isinstance(asset, dict) and asset.get("id")
    }


def _known_question_ids(data: dict) -> set[str]:
    questions = data.get("open_questions")
    if not isinstance(questions, list):
        return set()
    return {
        str(question.get("id"))
        for question in questions
        if isinstance(question, dict) and question.get("id")
    }


def validate_ir(path: Path) -> int:
    data = yaml_load(path)
    result = IRValidation()
    if not isinstance(data, dict):
        result.err("IR 顶层必须是对象")
        return result.report()
    if data.get("version") != "1.0":
        result.err("version 必须为 '1.0'")
    known_asset_ids = _collect_asset_ids(data)
    known_question_ids = _known_question_ids(data)
    question_index = _question_index(result, data, known_asset_ids)
    _check_application(result, data)
    _check_application_sources(result, data, question_index, known_question_ids)
    _check_task_mode(result, data, question_index, known_question_ids)
    _check_assets(result, data, question_index)
    return result.report()


def cli() -> int:
    parser = argparse.ArgumentParser(description="校验 lowcode-dsl-gen IR")
    parser.add_argument("ir", help="IR yaml 文件")
    args = parser.parse_args()
    path = Path(args.ir).resolve()
    if not path.is_file():
        print_err(f"IR 文件不存在: {path}")
        return 1
    if path.parent.name == ".lowcode-plans" and path.name.endswith("-ir.yml"):
        print_err(
            "IR 文件路径已废弃：请使用 .lowcode-plans/<apptag>/ir.yml，"
            f"当前是 {path}"
        )
        return 1
    return validate_ir(path)


if __name__ == "__main__":
    sys.exit(cli())
