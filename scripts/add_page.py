#!/usr/bin/env python3
"""add_page.py - create page designer page YAML files.

This script intentionally targets the page-designer persisted JSON shape:
componentType/componentId/componentName/props/slots.

Generated JSON files are written to <app-root>/page/.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from copy import deepcopy
from pathlib import Path


VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900, "unit": "px", "device": "desktop"},
    "mobile": {"width": 390, "height": 844, "unit": "px", "device": "mobile"},
    "tablet": {"width": 768, "height": 1024, "unit": "px", "device": "tablet"},
    "embedded": {"width": 800, "height": 600, "unit": "px", "device": "embedded"},
}

TYPE_MAP = {
    "nvarchar": "string",
    "ntext": "string",
    "Integer": "number",
    "int": "number",
    "Numeric": "number",
    "DateTime": "datetime",
    "datetime": "datetime",
    "date": "datetime",
    "Image": "string",
}

PAGETAG_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

WIDGET_ALIASES = {
    "sforminput": "input",
    "sforminputnumber": "input-number",
    "sformselect": "select",
    "sformcascader": "cascader",
    "sformtreeselect": "tree-select",
    "sformtree": "tree",
    "sformanchor": "anchor",
    "sformcheckbox": "checkbox",
    "sformcheckboxgroup": "checkbox-group",
    "sformradiogroup": "radio-group",
    "sformswitch": "switch",
    "sformdatepicker": "date-picker",
    "sformtimepicker": "time-picker",
    "sformpersonpicker": "person-picker",
    "sformorganizationselect": "organization-select",
    "sformbuttonedit": "button-edit",
    "sformbutton": "button",
    "sformdropdown": "dropdown",
    "sformfileupload": "file-upload",
    "sformimageupload": "image-upload",
    "sformeditorwrapper": "editor-wrapper",
    "sformtext": "text",
    "sformimage": "image",
    "sformline": "line",
    "sformrate": "rate",
    "sformslider": "slider",
    "sformworkflowbutton": "workflow-button",
    "sformworkflowhistory": "workflow-history",
    "sformworkflowright": "workflow-right",
    "sformlayoutmanager": "layout-manager",
    "sformformlayout": "form-layout",
    "sformformitem": "form-item",
    "sformgridlayout": "grid-layout",
    "sformflexlayout": "flex-layout",
    "sformdiv": "div",
    "sformtabs": "tabs",
    "sformtabpane": "tab-pane",
    "sformcollapse": "collapse",
    "sformtoolbar": "toolbar",
    "sformtable": "table",
    "sformscrollbar": "scrollbar",
}

STRING_QUERY_OPERATIONS = ["EQ", "NQ", "EQBLANK", "NQBLANK", "LIKE", "NOTLIKE", "LEFTLIKE", "RIGHTLIKE"]
NUMBER_QUERY_OPERATIONS = ["EQ", "NQ", "GT", "GE", "LT", "LE", "BTW", "NOTBTW"]
ENUM_QUERY_OPERATIONS = ["EQ", "NQ", "IN"]

PERSON_MULTI_KEYWORDS = (
    "参会人员",
    "参与人员",
    "处理人员",
    "审批人员",
    "成员",
    "人员",
    "participants",
    "participant",
    "members",
    "member",
)

PERSON_SINGLE_KEYWORDS = (
    "立项人",
    "负责人",
    "经办人",
    "申请人",
    "发起人",
    "审批人",
    "处理人",
    "联系人",
    "负责人",
    "initiator",
    "owner",
    "handler",
    "leader",
    "manager",
    "principal",
    "contact",
    "creator",
)

FILE_UPLOAD_KEYWORDS = (
    "附件",
    "资料",
    "文件",
    "上传",
    "attachment",
    "attachments",
    "file",
    "files",
    "document",
    "documents",
)

IMAGE_UPLOAD_KEYWORDS = (
    "图片",
    "照片",
    "截图",
    "image",
    "images",
    "photo",
    "photos",
    "picture",
    "pictures",
)


def repair_text(value):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return text

    # Windows shell / subprocess chains sometimes turn UTF-8 Chinese into
    # mojibake like "ç«é¡¹..." or replacement marks like "????".
    # Prefer a lossless utf8<-latin1 repair when possible; otherwise keep
    # the original text so we do not damage already-correct ASCII content.
    if "?" not in text:
        try:
            repaired = text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            repaired = text
        else:
            if repaired != text:
                return repaired
    return text


def repair_json_value(value):
    if isinstance(value, dict):
        return {k: repair_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [repair_json_value(v) for v in value]
    if isinstance(value, str):
        return repair_text(value)
    return value


def identifier(value: str, default: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9_]+", "_", value or "").strip("_")
    if not raw:
        raw = default
    if not re.match(r"^[a-zA-Z]", raw):
        raw = f"{default}_{raw}"
    return raw[0].lower() + raw[1:]


def page_id_from_pagetag(pagetag: str) -> str:
    return pagetag.replace("_", "-") + "-page"


def renderer_page_id() -> str:
    return f"page_{int(time.time() * 1000)}"


def stable_model_guid(pagetag: str, alias: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"epoint-lowcode:pagedesigne:model:{pagetag}:{alias}"))


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def read_text_arg(value: str, file_path: str | None = None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8-sig")
    return value


def parse_json_arg(value: str, *, label: str) -> list:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} parse failed: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{label} must be a JSON array")
    return repair_json_value(data)


def parse_object_arg(value: str, *, label: str) -> dict:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} parse failed: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return repair_json_value(data)


def mock_value_for_field(field: dict, index: int):
    name = field["name"]
    label = field["label"]
    field_type = field["type"]
    if name in {"rowguid", "id"} or name.endswith("guid"):
        return f"mock-{name}-{index:03d}"
    if field_type == "number":
        return index
    if field_type in {"date", "datetime"}:
        return f"2026-06-{index:02d}"
    if "status" in name or label in {"状态", "审批状态"}:
        statuses = ["审批中", "退回", "审批通过"]
        return statuses[(index - 1) % len(statuses)]
    if "person" in name or "user" in name or "人员" in label or "申请人" in label:
        return "测试人员"
    return f"{label}{index}"


def build_mock_initial(fields: list[dict], count: int = 3) -> list[dict]:
    rows = []
    for index in range(1, max(1, count) + 1):
        row = {"rowguid": f"mock-row-{index:03d}"}
        for field in fields:
            row[field["name"]] = mock_value_for_field(field, index)
        rows.append(row)
    return rows


def read_json_param_local(inline_value, file_path, *, label: str) -> list:
    """从内联 JSON 或文件读取 JSON 数组，二选一；都未提供返回 []。

    超长 / 含中文的内联 JSON 会撑爆命令行导致部分执行环境挂起，提供文件方式规避。
    """
    if inline_value and file_path:
        raise ValueError(f"{label}: inline JSON and file are mutually exclusive")
    if file_path:
        p = Path(file_path)
        if not p.is_file():
            raise ValueError(f"{label}: file not found: {file_path}")
        return parse_json_arg(p.read_text(encoding="utf-8"), label=label)
    if inline_value:
        return parse_json_arg(inline_value, label=label)
    return []


def normalize_field(item, index: int) -> dict:
    if isinstance(item, str):
        item = {"name": item, "label": item}
    if not isinstance(item, dict):
        raise ValueError(f"field {index} must be an object or string")
    name = item.get("name") or item.get("field") or item.get("key")
    if not name:
        raise ValueError(f"field {index} missing name")
    name = identifier(str(name), f"field{index}")
    field_type = TYPE_MAP.get(item.get("type"), item.get("type", "string"))
    if field_type not in {"string", "number", "boolean", "date", "datetime", "object", "array"}:
        field_type = "string"
    widget = item.get("widget") or item.get("component") or item.get("editor")
    if isinstance(widget, str):
        widget = widget.strip()
    else:
        widget = ""
    group = item.get("group") or item.get("section") or ""
    if not isinstance(group, str):
        group = ""
    query = item.get("query")
    if query is None:
        query = item.get("isQuery")
    label = repair_text(str(item.get("label") or item.get("description") or item.get("title") or name))
    explicit_multiple = item.get("multiple")
    explicit_person = item.get("personSelect")
    inferred_person = infer_person_field(name, label)
    return {
        "name": name,
        "label": label,
        "type": field_type,
        "widget": widget,
        "group": repair_text(group),
        "span": int(item.get("span", 0) or 0),
        "query": bool(query) if query is not None else False,
        "editable": bool(item.get("editable", True)),
        "required": bool(item.get("required", False)),
        "displayField": repair_text(str(item.get("displayField") or "")),
        "codeItem": repair_text(str(item.get("codeItem") or item.get("datasourceCodename") or "")),
        "fielddisplaytype": repair_text(str(item.get("fielddisplaytype") or "")),
        "multiple": bool(explicit_multiple) if explicit_multiple is not None else inferred_person.get("multiple", False),
        "personSelect": bool(explicit_person) if explicit_person is not None else inferred_person.get("enabled", False),
    }


def normalize_fields(items) -> list[dict]:
    return [normalize_field(item, index + 1) for index, item in enumerate(items or [])]


def field_index(fields: list[dict]) -> dict[str, dict]:
    return {field["name"]: field for field in fields}


def merge_dict(base: dict, extra: dict | None) -> dict:
    merged = deepcopy(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def model_fields(fields: list[dict]) -> dict:
    return {
        field["name"]: {
            "type": field["type"],
            "label": field["label"],
        }
        for field in fields
    }


def load_mis_field_hints(app_root: Path, sql_table: str) -> dict[str, dict]:
    if not sql_table:
        return {}
    mis_path = app_root / "mis" / f"{sql_table}.mis.yml"
    if not mis_path.is_file():
        return {}
    try:
        data = json.loads(mis_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    fields = data.get("fields")
    if not isinstance(fields, list):
        return {}
    hints: dict[str, dict] = {}
    for raw in fields:
        if not isinstance(raw, dict):
            continue
        name = raw.get("name")
        if not name:
            continue
        hints[str(name)] = {
            "label": repair_text(str(raw.get("description") or "")),
            "type": raw.get("type"),
            "codeItem": repair_text(str(raw.get("datasourceCodename") or "")),
            "fielddisplaytype": repair_text(str(raw.get("fielddisplaytype") or "")),
            "required": bool(raw.get("mustfill", False)),
        }
    return hints


def apply_mis_hints(fields: list[dict], hints: dict[str, dict]) -> list[dict]:
    if not hints:
        return fields
    merged: list[dict] = []
    for field in fields:
        hint = hints.get(field["name"], {})
        merged_field = dict(field)
        if hint.get("label") and (not merged_field.get("label") or merged_field["label"] == merged_field["name"]):
            merged_field["label"] = hint["label"]
        hint_type = TYPE_MAP.get(hint.get("type"), hint.get("type"))
        if hint_type in {"string", "number", "boolean", "date", "datetime", "object", "array"}:
            merged_field["type"] = hint_type
        if hint.get("codeItem") and not merged_field.get("codeItem"):
            merged_field["codeItem"] = hint["codeItem"]
        if hint.get("fielddisplaytype") and not merged_field.get("fielddisplaytype"):
            merged_field["fielddisplaytype"] = hint["fielddisplaytype"]
        if hint.get("required") and not merged_field.get("required"):
            merged_field["required"] = True
        merged.append(merged_field)
    return merged


def model_expr(model_alias: str, field_name: str | None = None) -> dict:
    path = f"$model.{model_alias}"
    if field_name:
        path = f"{path}.{field_name}"
    return {"$expr": path}


def upload_resource_id(field_name: str) -> str:
    return f"{field_name}Upload"


def ensure_upload_resource(schema: dict, field: dict, control_type: str) -> str:
    resource_id = upload_resource_id(field["name"])
    resources = schema.setdefault("resources", {})
    if resource_id in resources:
        return resource_id
    is_image = control_type == "image-upload"
    resources[resource_id] = {
        "type": "upload",
        "request": {
            "method": "POST",
            "url": "/api/files/upload",
        },
        "accept": ["image/*"] if is_image else [],
        "maxSizeMb": 10,
        "map": {
            "url": "url",
            "id": "id",
            "name": "filename",
        },
    }
    return resource_id


def widget_key(field: dict) -> str:
    raw = (field.get("widget") or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", raw)


def infer_person_field(name: str, label: str) -> dict:
    text = f"{name} {label}".lower()
    if any(keyword in text for keyword in PERSON_MULTI_KEYWORDS):
        return {"enabled": True, "multiple": True}
    if any(keyword in text for keyword in PERSON_SINGLE_KEYWORDS):
        return {"enabled": True, "multiple": False}
    return {"enabled": False, "multiple": False}


def infer_upload_widget(name: str, label: str) -> str:
    text = f"{name} {label}".lower()
    if any(keyword in text for keyword in IMAGE_UPLOAD_KEYWORDS):
        return "image-upload"
    if any(keyword in text for keyword in FILE_UPLOAD_KEYWORDS):
        return "file-upload"
    return ""


def field_widget_type(field: dict, *, mode: str) -> str:
    explicit = widget_key(field)
    if explicit in WIDGET_ALIASES:
        return WIDGET_ALIASES[explicit]

    field_type = field["type"]
    display_type = (field.get("fielddisplaytype") or "").strip().lower()
    has_code_item = bool(field.get("codeItem"))
    upload_widget = infer_upload_widget(field["name"], field["label"])

    if mode == "query":
        if field_type == "number":
            return "input-number"
        if field_type in {"date", "datetime"}:
            return "date-picker"
        if display_type in {"combobox", "radio", "checkbox"} or has_code_item or field.get("displayField"):
            return "select"
        return "input"

    if mode == "form":
        if field.get("personSelect"):
            return "organization-select"
        if upload_widget:
            return upload_widget
        if display_type in {"textarea", "textareacontrol"}:
            return "input"
        if display_type in {"combobox", "radio", "checkbox"} or has_code_item or field.get("displayField"):
            return "select"
        if field_type == "number":
            return "input-number"
        if field_type in {"date", "datetime"}:
            return "date-picker"
        if field_type == "boolean":
            return "switch"
        if field.get("multiple"):
            return "select"
        return "input"

    if mode == "table":
        if field_type == "number":
            return "input-number"
        if field_type in {"date", "datetime"}:
            return "date-picker"
        if display_type in {"combobox", "radio", "checkbox"} or has_code_item or field.get("displayField"):
            return "select"
        return "input"

    return "input"


def query_operations(field: dict) -> list[str]:
    if field["type"] == "number":
        return NUMBER_QUERY_OPERATIONS
    if field["type"] in {"date", "datetime"}:
        return NUMBER_QUERY_OPERATIONS
    if field.get("displayField"):
        return ENUM_QUERY_OPERATIONS
    return STRING_QUERY_OPERATIONS


def component(page_id: str, component_type: str, *, suffix: str | None = None,
              parent: str | None = None, slot: str | None = None,
              component_name: str | None = None, node_type: str | None = None,
              props: dict | None = None, children: list | None = None,
              slots: dict | None = None, events: dict | None = None,
              source: str | None = None) -> dict:
    suffix = suffix or component_type
    component_id = f"{suffix}_{page_id}"
    data = {
        "componentType": component_type,
        "componentId": component_id,
    }
    if parent:
        data["parentContainerId"] = parent
    if slot:
        data["slotName"] = slot
    if children is not None:
        data["children"] = children
    data.update({
        "id": suffix,
        "componentName": component_name or f"ev-{component_type}100",
        "type": node_type or component_type,
        "version": "1.0.0",
        "isRegister": True,
        "props": props or {},
    })
    if source:
        data["source"] = source
    if events is not None:
        data["events"] = events
    if slots is not None:
        data["slots"] = slots
    return data


def editor_type(field_type: str) -> str:
    if field_type == "number":
        return "input-number"
    return "input"


def editor_props(field: dict, *, mode: str = "form") -> dict:
    widget = field_widget_type(field, mode=mode)
    if widget in {"date-picker", "time-picker"}:
        return {
            "clearable": True,
            "format": "YYYY-MM-DD",
            "placeholder": f"请选择{field['label']}",
            "type": "date" if widget == "date-picker" else "time",
        }
    if widget == "input-number":
        return {
            "min": 0,
            "max": 999999999,
            "precision": 2,
            "step": 1,
        }
    if widget == "switch":
        return {
            "activeValue": True,
            "inactiveValue": False,
        }
    if widget in {"organization-select", "person-picker"}:
        return {
            "mode": "people",
            "clearable": True,
            "interactive": "dropdown",
            "multiple": bool(field.get("multiple", False)),
            "range": "all",
            "placeholder": f"请选择{field['label']}",
        }
    return {
        "maxlength": 500,
        "showWordLimit": True,
        "placeholder": f"请输入{field['label']}",
    }


def table_column(page_id: str, model_alias: str, field: dict, index: int, table_id: str) -> dict:
    column_suffix = f"table-column-{index}"
    column_id = f"{column_suffix}_{page_id}"
    editor_suffix = f"table-column-editor-{index}"
    return component(
        page_id,
        column_suffix,
        suffix=column_suffix,
        parent=table_id,
        component_name=f"ev-table-column-{index}100",
        node_type="table-column",
        children=[
            component(
                page_id,
                f"table-column-editor-{index}",
                suffix=editor_suffix,
                parent=column_id,
                component_name=f"ev-table-column-editor-{index}100",
                node_type=field_widget_type(field, mode="table"),
                props=editor_props(field),
            )
        ],
        props={
            "modelValue": model_expr(model_alias, field["name"]),
            "state": "normal",
            "title": field["label"],
            "width": 180 if field["type"] in {"date", "datetime"} else (100 if field["type"] == "number" else 220),
            "align": "left",
            "allowHtml": False,
            "displayField": field.get("displayField", ""),
            "ellipsis": True,
            "resizable": True,
            "sorter": False,
            "mergeColumn": False,
            "edit": False,
            **({"dateFormat": "YYYY-MM-DD"} if field["type"] in {"date", "datetime"} else {}),
        },
    )


def search_control(page_id: str, model_alias: str, field: dict, index: int, toolbar_id: str) -> dict:
    suffix = f"search-control-{index}"
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=toolbar_id,
        slot="search",
        component_name=f"ev-search-control-{index}100",
        node_type="search-control",
        props={
            "orgType": "",
            "default": False,
            "isTreeDataSource": False,
            "isOrgDataSource": False,
            "modelValue": model_expr(model_alias, field["name"]),
            "defaultOperation": "EQ",
            "label": field["label"],
            "state": "normal",
            "fieldType": field["type"],
            "operation": query_operations(field),
            "codeItem": "",
        },
    )


def add_button_props(target_page_id: str) -> dict:
    return {
        "buttonText": "新增记录",
        "carryParentPageParam": False,
        "plain": False,
        "dialogHeight": "400px",
        "dialogTitle": "新增记录",
        "dialogWidth": "1000px",
        "state": "default",
        "text": False,
        "type": "primary",
        "params": [],
        "url": f"vuepagedesigner/renderer/add?pageId={target_page_id}",
        "openType": "dialog",
    }


def group_fields(fields: list[dict]) -> list[dict]:
    groups: list[dict] = []
    current_group = None
    default_group = None
    for field in fields:
        group_name = field.get("group") or ""
        if group_name:
            if not current_group or current_group["title"] != group_name:
                current_group = {"title": group_name, "fields": []}
                groups.append(current_group)
            current_group["fields"].append(field)
        else:
            if default_group is None:
                default_group = {"title": "", "fields": []}
                groups.append(default_group)
            default_group["fields"].append(field)
            current_group = default_group
    return groups


def choose_form_field(field: dict) -> str:
    return field_widget_type(field, mode="form")


def choose_query_field(field: dict) -> str:
    return field_widget_type(field, mode="query")


def choose_table_field(field: dict) -> str:
    return field_widget_type(field, mode="table")


def delete_button_props() -> dict:
    return {
        "buttonText": "删除选中",
        "plain": False,
        "state": "default",
        "text": False,
        "type": "danger",
    }


def default_toolbar_layout() -> dict:
    return {
        "props": {
            "template": "col-1",
            "showTitleSlot": False,
            "filterAdvancedFixed": "popover",
            "mixSearchDefault": False,
            "showActionsSlot": True,
            "showSearchSlot": True,
            "position": "top",
            "mixSearch": False,
            "buttonPosition": "left",
            "showButtonSlot": True,
        },
        "title": {"enabled": True},
        "buttons": [
            {"kind": "add", "slot": "button", "enabled": True},
            {"kind": "delete", "slot": "button", "enabled": True},
        ],
        "search": {
            "slot": "search",
            "enabled": True,
            "fields": [],
        },
        "actions": [
            {"kind": "more", "slot": "actions", "enabled": True},
        ],
    }


def default_table_layout() -> dict:
    return {
        "props": {
            "idField": "",
            "tableType": "dialog",
            "rowSelection": "checkbox",
            "showSelectionColumn": True,
            "showIndexColumn": True,
            "defaultShowIndex": True,
            "pageSize": 10,
            "pageSizeType": "system",
            "frozenLeft": 0,
            "frozenRight": 0,
            "borderStyle": "horizontal",
        },
        "columns": [],
        "actions": {
            "enabled": True,
            "title": "操作",
            "width": 100,
            "align": "left",
            "ellipsis": True,
            "resizable": True,
            "items": [
                {"actionType": "edit", "label": "修改", "icon": "Edit", "openType": "dialog"},
                {"actionType": "detail", "label": "查看", "icon": "Search", "openType": "dialog"},
                {"actionType": "delete", "label": "删除", "icon": "Delete", "openType": "dialog"},
            ],
        },
    }


def default_list_layout() -> dict:
    return {
        "toolbar": default_toolbar_layout(),
        "table": default_table_layout(),
    }


def table_action(page_id: str, table_id: str, action_index: int, action_type: str,
                 icon: str, label: str, url: str, dialog_title: str = "") -> dict:
    suffix = f"table-action-{action_index}"
    props = {
        "actionType": action_type,
        "carryParentPageParam": False,
        "icon": icon,
        "dialogHeight": "800px",
        "dialogWidth": "1000px",
        "label": label,
        "params": [],
        "url": url,
        "deleteTip": "是否确认删除已选中的记录？",
        "openType": "modal",
    }
    if dialog_title:
        props["dialogTitle"] = dialog_title
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=f"table-action-column-1_{page_id}",
        component_name=f"sform-table-action-{action_index}001",
        node_type="table-action",
        events={},
        props=props,
    )


def table_action_column(page_id: str, table_id: str, target_page_id: str) -> dict:
    return component(
        page_id,
        "table-action-column-1",
        suffix="table-action-column-1",
        parent=table_id,
        component_name="sform-table-action-column-1001",
        node_type="table-action-column",
        children=[
            table_action(
                page_id,
                table_id,
                1,
                "edit",
                "Edit",
                "修改",
                f"vuepagedesigner/renderer/add?pageId={target_page_id}",
                "修改",
            ),
            table_action(
                page_id,
                table_id,
                2,
                "detail",
                "Search",
                "查看",
                f"vuepagedesigner/renderer/detail?pageId={target_page_id}",
                "查看",
            ),
            table_action(page_id, table_id, 3, "delete", "Delete", "删除", ""),
        ],
        props={
            "resizable": True,
            "width": 100,
            "title": "操作",
            "align": "left",
            "asText": False,
            "ellipsis": True,
        },
    )


def base_schema(schema_id: str, pagetag: str, title: str, device: str, *, page_id: str | None = None) -> dict:
    schema = {
        "pagetag": pagetag,
        "schemaVersion": "core-1.0",
        "kind": "page",
        "id": schema_id,
        "title": repair_text(title),
        "viewport": VIEWPORTS[device],
        "theme": {
            "background": "#FFFFFF",
            "textColor": "#111827",
            "fontFamily": "system",
        },
        "models": [],
        "resources": {},
        "actions": {},
        "events": {},
        "children": [],
        "props": {},
    }
    if page_id:
        schema["pageId"] = page_id
    return schema


def build_list(schema: dict, args, fields: list[dict], query_fields: list[dict]) -> None:
    page_id = schema["id"]
    target_page_id = args.form_page_id or page_id
    model_alias = identifier(args.model, "items") if args.model else "items"
    fields_by_name = field_index(fields)
    model = {
        "modelGuid": stable_model_guid(args.pagetag, model_alias),
        "alias": model_alias,
        "source": "mis" if args.sql_table else "interface" if args.endpoint else "",
        "type": "collection",
        "primaryKey": "rowguid",
        "fields": model_fields(fields),
        **({"sqlTableName": args.sql_table} if args.sql_table else {}),
    }
    if getattr(args, "initial", None):
        model["initial"] = args.initial
    schema["models"].append(model)

    container_id = f"list-container_{page_id}"
    toolbar_id = f"toolbar_{page_id}"
    table_id = f"table_{page_id}"
    layout = normalize_list_layout(args.layout, query_fields=query_fields)
    toolbar_layout = layout["toolbar"]
    table_layout = layout["table"]

    title_slot = []
    if toolbar_layout.get("title", {}).get("enabled", True):
        title_slot.append(toolbar_title_component(page_id, toolbar_id, args.title, toolbar_layout.get("title") or {}))

    button_slot = [
        toolbar_button_component(page_id, toolbar_id, target_page_id, index + 1, item)
        for index, item in enumerate(toolbar_layout.get("buttons") or [])
        if isinstance(item, dict) and item.get("enabled", True)
    ]

    search_slot = []
    if toolbar_layout.get("search", {}).get("enabled", True):
        for index, item in enumerate(toolbar_layout["search"].get("fields") or [], start=1):
            if isinstance(item, str):
                field = resolve_field(item, fields_by_name, label="layout.toolbar.search.fields")
                search_slot.append(search_control(page_id, model_alias, field, index, toolbar_id))
            elif isinstance(item, dict) and item.get("enabled", True):
                field_name = item.get("field") or item.get("name")
                field = resolve_field(str(field_name), fields_by_name, label="layout.toolbar.search.fields")
                search_slot.append(custom_search_control(page_id, toolbar_id, model_alias, field, index, item))

    actions_slot = [
        toolbar_more_component(page_id, toolbar_id, index + 1, item)
        for index, item in enumerate(toolbar_layout.get("actions") or [])
        if isinstance(item, dict) and item.get("enabled", True)
    ]

    toolbar_props = merge_dict(toolbar_layout.get("props") or {}, {})
    toolbar_props["showTitleSlot"] = bool(title_slot) if "showTitleSlot" not in toolbar_props else toolbar_props["showTitleSlot"]
    toolbar_props["showButtonSlot"] = bool(button_slot) if "showButtonSlot" not in toolbar_props else toolbar_props["showButtonSlot"]
    toolbar_props["showSearchSlot"] = bool(search_slot) if "showSearchSlot" not in toolbar_props else toolbar_props["showSearchSlot"]
    toolbar_props["showActionsSlot"] = bool(actions_slot) if "showActionsSlot" not in toolbar_props else toolbar_props["showActionsSlot"]

    toolbar = component(
        page_id,
        str(toolbar_layout.get("id") or "toolbar"),
        suffix=str(toolbar_layout.get("id") or "toolbar"),
        parent=container_id,
        children=[],
        component_name=str(toolbar_layout.get("componentName") or "ev-toolbar100"),
        node_type=str(toolbar_layout.get("type") or "toolbar"),
        slots={
            "title": title_slot,
            "button": button_slot,
            "search": search_slot,
            "actions": actions_slot,
        },
        props=toolbar_props,
    )

    raw_columns = table_layout.get("columns") if isinstance(table_layout.get("columns"), list) and table_layout.get("columns") else []
    if not raw_columns:
        raw_columns = [{"field": field["name"]} for field in fields]
    column_counter = {"value": 0}
    columns = build_table_column_tree(page_id, table_id, model_alias, fields_by_name, raw_columns, column_counter, target_page_id)
    action_column = build_table_action_column(page_id, table_id, target_page_id, table_layout.get("actions") or {})
    if action_column:
        columns.append(action_column)

    table_props = merge_dict(
        {
            "modelValue": model_expr(model_alias),
        },
        table_layout.get("props") if isinstance(table_layout.get("props"), dict) else {},
    )

    table = component(
        page_id,
        str(table_layout.get("id") or "table"),
        suffix=str(table_layout.get("id") or "table"),
        parent=container_id,
        component_name=str(table_layout.get("componentName") or "ev-table100"),
        node_type=str(table_layout.get("type") or "table"),
        children=columns,
        props=table_props,
    )

    schema["children"] = [
        {
            "componentType": "list-container",
            "componentId": container_id,
            "children": [toolbar, table],
            "id": "list-container",
            "componentName": "ev-list-container100",
            "type": "list-container",
            "version": "1.0.0",
            "isRegister": True,
            "props": {},
        }
    ]


def form_control(page_id: str, model_alias: str, field: dict, index: int, parent_id: str,
                 *, readonly: bool = False, schema: dict | None = None) -> dict:
    suffix = f"control-{index}"
    control_type = field_widget_type(field, mode="form")
    source = None
    props = {
        "width": "100%",
        "modelValue": model_expr(model_alias, field["name"]),
        "tooltipPosition": "none",
        "state": "normal" if not readonly else "disabled",
        "tooltipContent": "",
    }
    if control_type == "date-picker":
        props.update({
            "minDate": "",
            "clearable": not readonly,
            "editable": False,
            "format": "YYYY-MM-DD",
            "maxDate": "",
            "placeholder": f"请选择{field['label']}",
            "type": "date",
        })
    elif control_type == "input-number":
        props.update({
            "unit": "",
            "min": 0,
            "max": 999999999,
            "precision": 2,
            "step": 1,
            "showControls": not readonly,
        })
    elif control_type in {"select", "organization-select", "person-picker", "tree-select", "cascader"}:
        props.update({
            "clearable": not readonly,
            "placeholder": f"请选择{field['label']}",
            "codeItem": field.get("codeItem", ""),
            "multiple": field.get("multiple", False),
            "displayField": field.get("displayField", ""),
        })
    elif control_type == "file-upload":
        source = ensure_upload_resource(schema, field, control_type) if schema is not None else None
        props.update({
            "pickerText": "选择文件",
            "multiple": bool(field.get("multiple", False)),
            "numLimit": "",
            "sizeLimit": 0,
            "typeLimit": "",
            "accept": "",
            "clientTag": field["name"],
            "enableSort": False,
            "drag": False,
            "showFileList": True,
        })
    elif control_type == "image-upload":
        source = ensure_upload_resource(schema, field, control_type) if schema is not None else None
        props.update({
            "multiple": bool(field.get("multiple", False)),
            "imageSize": 140,
            "numLimit": "",
            "sizeLimit": 0,
            "typeLimit": "gif,jpg,jpeg,bmp,png,webp",
            "accept": "image/*",
            "clientTag": field["name"],
            "enableSort": False,
        })
    elif control_type == "switch":
        props.update({
            "activeText": "",
            "inactiveText": "",
        })
    else:
        is_textarea = (
            (field.get("fielddisplaytype") or "").strip().lower() in {"textarea", "textareacontrol"}
            or field["type"] == "string" and field["name"] in {"remark", "description"}
            or field["type"] == "string" and any(keyword in field["name"].lower() for keyword in {"content", "desc", "remark", "attachment", "compare", "value"})
            or field["type"] == "string" and any(keyword in field["label"] for keyword in {"内容", "描述", "备注", "附件", "对比", "价值"})
        )
        props.update({
            "clearable": not readonly,
            "unit": "",
            "maxlength": 500,
            "showWordLimit": False,
            "placeholder": f"请输入{field['label']}",
            "type": "textarea" if is_textarea else "text",
            **({"rows": 4} if is_textarea else {}),
            "validate": "",
        })
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=parent_id,
        component_name=f"ev-{suffix}100",
        node_type=control_type,
        events={} if control_type == "input" else None,
        props=props,
        source=source,
    )


def form_item(page_id: str, model_alias: str, field: dict, index: int, parent_id: str,
              *, readonly: bool = False, schema: dict | None = None, default_span: int = 12) -> dict:
    suffix = f"form-item-{index}"
    item_id = f"{suffix}_{page_id}"
    span = int(field.get("span") or 0)
    if span <= 0:
        span = 24 if field["name"] in {"remark", "description"} else default_span
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=parent_id,
        component_name=f"ev-form-item-{index}100",
        node_type="form-item",
        children=[form_control(page_id, model_alias, field, index, item_id, readonly=readonly, schema=schema)],
        props={
            "labelPosition": "right",
            "labelTooltip": "",
            "labelWidth": "auto",
            "label": field["label"],
            "span": span,
        },
    )


def default_action_url(action_type: str, target_page_id: str) -> str:
    if action_type == "edit":
        return f"vuepagedesigner/renderer/add?pageId={target_page_id}"
    if action_type == "detail":
        return f"vuepagedesigner/renderer/detail?pageId={target_page_id}"
    return ""


def normalize_list_layout(layout: dict | None, *, query_fields: list[dict]) -> dict:
    merged = merge_dict(default_list_layout(), layout or {})
    toolbar = merged.get("toolbar") if isinstance(merged.get("toolbar"), dict) else {}
    table = merged.get("table") if isinstance(merged.get("table"), dict) else {}
    search = toolbar.get("search") if isinstance(toolbar.get("search"), dict) else {}
    if not isinstance(search.get("fields"), list) or not search.get("fields"):
        search["fields"] = [field["name"] for field in query_fields]
    toolbar["search"] = search
    merged["toolbar"] = toolbar
    merged["table"] = table
    return merged


def default_form_layout() -> dict:
    return {
        "layout": {
            "gutter": 0,
            "itemSpan": 12,
        },
        "toolbar": {
            "position": "bottom",
            "buttonPosition": "right",
            "buttons": [
                {"kind": "save", "enabled": True},
            ],
        },
        "sections": [],
    }


def normalize_form_layout(layout: dict | None) -> dict:
    merged = merge_dict(default_form_layout(), layout or {})
    toolbar = merged.get("toolbar") if isinstance(merged.get("toolbar"), dict) else {}
    position = str(toolbar.get("position") or "bottom").lower()
    toolbar["position"] = "top" if position == "top" else "bottom"
    toolbar["buttonPosition"] = str(toolbar.get("buttonPosition") or ("left" if toolbar["position"] == "top" else "right"))
    buttons = toolbar.get("buttons")
    if not isinstance(buttons, list):
        buttons = [{"kind": "save", "enabled": True}]
    toolbar["buttons"] = buttons
    merged["toolbar"] = toolbar

    section_layout = merged.get("layout") if isinstance(merged.get("layout"), dict) else {}
    try:
        item_span = int(section_layout.get("itemSpan", 12))
    except (TypeError, ValueError):
        item_span = 12
    if item_span not in {6, 8, 12, 24}:
        item_span = 12
    section_layout["itemSpan"] = item_span
    try:
        section_layout["gutter"] = int(section_layout.get("gutter", 0))
    except (TypeError, ValueError):
        section_layout["gutter"] = 0
    merged["layout"] = section_layout

    if not isinstance(merged.get("sections"), list):
        merged["sections"] = []
    return merged


def resolve_field(name: str, fields_by_name: dict[str, dict], *, label: str) -> dict:
    field = fields_by_name.get(identifier(name, "field"))
    if not field:
        raise ValueError(f"{label} references unknown field: {name}")
    return field


def toolbar_title_component(page_id: str, toolbar_id: str, title: str, config: dict) -> dict:
    title_props = {"title": title}
    if isinstance(config.get("props"), dict):
        title_props.update(config["props"])
    return component(
        page_id,
        str(config.get("id") or "toolbar-title"),
        suffix=str(config.get("id") or "toolbar-title"),
        parent=toolbar_id,
        slot=str(config.get("slot") or "title"),
        component_name=str(config.get("componentName") or "ev-toolbar-title100"),
        node_type=str(config.get("type") or "toolbar-title"),
        props=title_props,
    )


def toolbar_button_component(page_id: str, toolbar_id: str, target_page_id: str, index: int, item: dict) -> dict:
    kind = str(item.get("kind") or "custom")
    slot = str(item.get("slot") or "button")
    suffix = str(item.get("id") or f"toolbar-button-{index}")
    if kind == "add":
        props = add_button_props(target_page_id)
        props = merge_dict(props, item.get("props") if isinstance(item.get("props"), dict) else {})
        return component(
            page_id,
            suffix,
            suffix=suffix,
            parent=toolbar_id,
            slot=slot,
            component_name=str(item.get("componentName") or "sform-add-button100"),
            node_type=str(item.get("type") or "add-button"),
            events={} if item.get("events", True) is not None else None,
            props=props,
        )
    if kind == "delete":
        props = delete_button_props()
        props = merge_dict(props, item.get("props") if isinstance(item.get("props"), dict) else {})
        return component(
            page_id,
            suffix,
            suffix=suffix,
            parent=toolbar_id,
            slot=slot,
            component_name=str(item.get("componentName") or "ev-del-button100"),
            node_type=str(item.get("type") or "del-button"),
            events={} if item.get("events", True) is not None else None,
            props=props,
        )
    props = {
        "buttonText": repair_text(str(item.get("text") or item.get("label") or "按钮")),
        "type": str(item.get("buttonType") or item.get("visualType") or item.get("typeStyle") or "default"),
        "plain": bool(item.get("plain", False)),
        "text": bool(item.get("textMode", False)),
        "state": str(item.get("state") or "default"),
    }
    props = merge_dict(props, item.get("props") if isinstance(item.get("props"), dict) else {})
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=toolbar_id,
        slot=slot,
        component_name=str(item.get("componentName") or f"ev-{suffix}100"),
        node_type=str(item.get("type") or "button"),
        events=item.get("events") if isinstance(item.get("events"), dict) else {},
        props=props,
    )


def toolbar_more_component(page_id: str, toolbar_id: str, index: int, item: dict) -> dict:
    suffix = str(item.get("id") or f"toolbar-more-{index}")
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=toolbar_id,
        slot=str(item.get("slot") or "actions"),
        component_name=str(item.get("componentName") or "ev-toolbar-more100"),
        node_type=str(item.get("type") or "toolbar-more"),
        props=item.get("props") if isinstance(item.get("props"), dict) else {},
    )


def custom_search_control(page_id: str, toolbar_id: str, model_alias: str, field: dict, index: int, item: dict) -> dict:
    suffix = str(item.get("id") or f"search-control-{index}")
    props = {
        "orgType": "",
        "default": False,
        "isTreeDataSource": False,
        "isOrgDataSource": False,
        "modelValue": model_expr(model_alias, field["name"]),
        "defaultOperation": str(item.get("defaultOperation") or "EQ"),
        "label": repair_text(str(item.get("label") or field["label"])),
        "state": str(item.get("state") or "normal"),
        "fieldType": field["type"],
        "operation": item.get("operation") if isinstance(item.get("operation"), list) and item.get("operation") else query_operations(field),
        "codeItem": repair_text(str(item.get("codeItem") or field.get("codeItem") or "")),
    }
    props = merge_dict(props, item.get("props") if isinstance(item.get("props"), dict) else {})
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=toolbar_id,
        slot=str(item.get("slot") or "search"),
        component_name=str(item.get("componentName") or f"ev-search-control-{index}100"),
        node_type=str(item.get("type") or "search-control"),
        props=props,
    )


def build_table_column_tree(page_id: str, parent_id: str, model_alias: str, fields_by_name: dict[str, dict],
                            items: list[dict], counter: dict, target_page_id: str) -> list[dict]:
    columns: list[dict] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("enabled", True):
            continue
        kind = str(item.get("kind") or "").lower()
        if item.get("type") == "table-action-column" or isinstance(item.get("items"), list):
            counter["value"] += 1
            action_index = counter["value"]
            action_config = merge_dict({"id": item.get("id") or f"table-action-column-{action_index}"}, item)
            action_column = build_table_action_column(page_id, parent_id, target_page_id, action_config)
            if action_column:
                columns.append(action_column)
            continue
        counter["value"] += 1
        column_index = counter["value"]
        is_sequence = kind in {"sequence", "seq", "index"} or str(item.get("type") or "").lower() in {"sequence-column", "index-column"}
        suffix = str(item.get("id") or ("table-column-seq" if is_sequence else f"table-column-{column_index}"))
        column_id = f"{suffix}_{page_id}"
        child_items = item.get("children") if isinstance(item.get("children"), list) else []
        field_name = item.get("field")
        is_group = bool(child_items) and not field_name
        props = {
            "state": str(item.get("state") or "normal"),
            "title": repair_text(str(item.get("title") or item.get("label") or ("序" if is_sequence else field_name) or f"列{column_index}")),
            "width": item.get("width", 80 if is_sequence else ""),
            "align": str(item.get("align") or ("center" if is_sequence else "left")),
            "allowHtml": bool(item.get("allowHtml", False)),
            "displayField": repair_text(str(item.get("displayField") or "")),
            "ellipsis": bool(item.get("ellipsis", True)),
            "resizable": bool(item.get("resizable", True)),
            "sorter": bool(item.get("sorter", False)),
            "mergeColumn": bool(item.get("mergeColumn", False)),
            "edit": bool(item.get("edit", False)),
        }
        column_children: list[dict] = []
        if is_sequence:
            if field_name:
                field = resolve_field(str(field_name), fields_by_name, label="layout.table.columns.field")
                props["modelValue"] = model_expr(model_alias, field["name"])
            elif isinstance(item.get("modelValue"), dict):
                props["modelValue"] = item["modelValue"]
        elif field_name:
            field = resolve_field(str(field_name), fields_by_name, label="layout.table.columns.field")
            props["modelValue"] = model_expr(model_alias, field["name"])
            if not item.get("displayField"):
                props["displayField"] = field.get("displayField", "")
            if not item.get("title") and not item.get("label"):
                props["title"] = field["label"]
            if item.get("width") in (None, ""):
                props["width"] = 180 if field["type"] in {"date", "datetime"} else (100 if field["type"] == "number" else 220)
            if field["type"] in {"date", "datetime"} and "dateFormat" not in props:
                props["dateFormat"] = "YYYY-MM-DD"
            editor_suffix = str(item.get("editorId") or f"table-column-editor-{column_index}")
            column_children.append(
                component(
                    page_id,
                    editor_suffix,
                    suffix=editor_suffix,
                    parent=column_id,
                    component_name=str(item.get("editorComponentName") or f"ev-table-column-editor-{column_index}100"),
                    node_type=str(item.get("editorType") or field_widget_type(field, mode="table")),
                    props=merge_dict(editor_props(field), item.get("editorProps") if isinstance(item.get("editorProps"), dict) else {}),
                )
            )
        if child_items:
            column_children.extend(
                build_table_column_tree(page_id, column_id, model_alias, fields_by_name, child_items, counter, target_page_id)
            )
        columns.append(
            component(
                page_id,
                suffix,
                suffix=suffix,
                parent=parent_id,
                component_name=str(
                    item.get("componentName")
                    or ("ev-table-column-seq100" if is_sequence else f"ev-table-column-group-{column_index}100" if is_group else f"ev-table-column-{column_index}100")
                ),
                node_type="table-column" if is_sequence else str(item.get("type") or ("table-column-group" if is_group else "table-column")),
                children=column_children,
                props=props if isinstance(item.get("props"), dict) is False else merge_dict(props, item["props"]),
            )
        )
    return columns


def infer_action_as_text(item: dict, column_config: dict | None = None) -> bool:
    explicit = item.get("asText")
    if explicit is not None:
        return bool(explicit)
    column_title = repair_text(str((column_config or {}).get("title") or ""))
    action_type = str(item.get("actionType") or item.get("kind") or "custom")
    if column_title and column_title != "操作":
        return True
    if action_type in {"custom", "detail"}:
        return True
    return False


def table_action_column_as_text(column_config: dict | None = None) -> bool:
    props = (column_config or {}).get("props")
    if isinstance(props, dict) and props.get("asText") is not None:
        return bool(props.get("asText"))
    if (column_config or {}).get("asText") is not None:
        return bool((column_config or {}).get("asText"))
    items = (column_config or {}).get("items")
    if isinstance(items, list) and items:
        return any(infer_action_as_text(item, column_config) for item in items if isinstance(item, dict))
    title = repair_text(str((column_config or {}).get("title") or ""))
    return bool(title and title != "操作")


def table_action_component(page_id: str, parent_id: str, target_page_id: str, action_index: int,
                           item: dict, column_config: dict | None = None) -> dict:
    action_type = str(item.get("actionType") or item.get("kind") or "custom")
    parent_suffix = re.sub(rf"_{re.escape(page_id)}$", "", parent_id)
    suffix = str(item.get("id") or f"{parent_suffix}-action-{action_index}")
    props = {
        "actionType": action_type,
        "carryParentPageParam": bool(item.get("carryParentPageParam", False)),
        "icon": str(item.get("icon") or ("Edit" if action_type == "edit" else "Search" if action_type == "detail" else "Delete" if action_type == "delete" else "")),
        "dialogHeight": str(item.get("dialogHeight") or "800px"),
        "dialogWidth": str(item.get("dialogWidth") or "1000px"),
        "label": repair_text(str(item.get("label") or item.get("text") or action_type)),
        "params": item.get("params") if isinstance(item.get("params"), list) else [],
        "url": repair_text(str(item.get("url") or default_action_url(action_type, target_page_id))),
        "deleteTip": repair_text(str(item.get("deleteTip") or "是否确认删除已选中的记录？")),
        "openType": str(item.get("openType") or "modal"),
    }
    if item.get("dialogTitle"):
        props["dialogTitle"] = repair_text(str(item["dialogTitle"]))
    elif action_type in {"edit", "detail"}:
        props["dialogTitle"] = props["label"]
    props = merge_dict(props, item.get("props") if isinstance(item.get("props"), dict) else {})
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=parent_id,
        component_name=str(item.get("componentName") or f"sform-table-action-{action_index}001"),
        node_type=str(item.get("type") or "table-action"),
        events=item.get("events") if isinstance(item.get("events"), dict) else {},
        props=props,
    )


def build_table_action_column(page_id: str, parent_id: str, target_page_id: str, config: dict) -> dict | None:
    if not config.get("enabled", True):
        return None
    suffix = str(config.get("id") or "table-action-column-1")
    component_id = f"{suffix}_{page_id}"
    items = config.get("items") if isinstance(config.get("items"), list) else []
    children = [
        table_action_component(page_id, component_id, target_page_id, index + 1, item, config)
        for index, item in enumerate(items)
        if isinstance(item, dict) and item.get("enabled", True)
    ]
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=parent_id,
        component_name=str(config.get("componentName") or "sform-table-action-column-1001"),
        node_type=str(config.get("type") or "table-action-column"),
        children=children,
        props=merge_dict(
            {
                "resizable": bool(config.get("resizable", True)),
                "width": config.get("width", 100),
                "title": repair_text(str(config.get("title") or "操作")),
                "align": str(config.get("align") or "left"),
                "asText": table_action_column_as_text(config),
                "ellipsis": bool(config.get("ellipsis", True)),
            },
            config.get("props") if isinstance(config.get("props"), dict) else {},
        ),
    )


def build_form_section(page_id: str, model_alias: str, fields: list[dict], start_index: int,
                       parent_id: str, section_index: int, *, readonly: bool = False,
                       schema: dict | None = None, item_span: int = 12, gutter: int = 0) -> tuple[dict, int]:
    form_layout_suffix = f"form-layout-{section_index}"
    form_layout_id = f"{form_layout_suffix}_{page_id}"
    items: list[dict] = []
    index = start_index
    for field in fields:
        items.append(
            form_item(
                page_id,
                model_alias,
                field,
                index,
                form_layout_id,
                readonly=readonly,
                schema=schema,
                default_span=item_span,
            )
        )
        index += 1
    form_layout = component(
        page_id,
        form_layout_suffix,
        suffix=form_layout_suffix,
        parent=parent_id,
        component_name=f"ev-form-layout-{section_index}100",
        node_type="form-layout",
        children=items,
        props={"gutter": gutter, "itemSpan": item_span},
    )
    return form_layout, index


def field_with_overrides(base: dict, item: dict | str, index: int) -> dict:
    if isinstance(item, str):
        return dict(base)
    if not isinstance(item, dict):
        return dict(base)
    merged = dict(base)
    explicit_keys = set(item)
    normalized = normalize_field(item, index)
    for key, value in normalized.items():
        if key == "name":
            continue
        if key in explicit_keys or key in {"required", "editable", "multiple", "personSelect"}:
            merged[key] = value
    return merged


def form_sections_from_layout(fields: list[dict], layout: dict, args_title: str) -> list[dict]:
    fields_by_name = field_index(fields)
    sections = []
    raw_sections = layout.get("sections") if isinstance(layout.get("sections"), list) else []
    for section_index, raw_section in enumerate(raw_sections, start=1):
        if not isinstance(raw_section, dict):
            continue
        section_fields = []
        for field_index_value, raw_field in enumerate(raw_section.get("fields") or [], start=1):
            field_name = raw_field if isinstance(raw_field, str) else raw_field.get("name") if isinstance(raw_field, dict) else ""
            if field_name:
                base = resolve_field(str(field_name), fields_by_name, label="layout.sections.fields")
                section_fields.append(field_with_overrides(base, raw_field, field_index_value))
        if section_fields:
            sections.append({
                "title": repair_text(str(raw_section.get("title") or args_title)),
                "fields": section_fields,
                "layout": raw_section.get("layout") if isinstance(raw_section.get("layout"), dict) else {},
            })
    if sections:
        return sections
    grouped_sections = []
    for group in group_fields(fields):
        grouped_sections.append({
            "title": group["title"] or args_title,
            "fields": group["fields"],
            "layout": {},
        })
    return grouped_sections


def form_toolbar_button(page_id: str, toolbar_id: str, index: int, item: dict) -> dict:
    kind = str(item.get("kind") or item.get("type") or "save").lower()
    if kind == "submit":
        suffix = str(item.get("id") or "submit-button")
        default_props = {
            "buttonText": "提交",
            "plain": False,
            "state": "default",
            "text": False,
            "type": "primary",
            "params": [],
            "url": "",
            "openType": "self",
        }
        component_name = str(item.get("componentName") or "ev-submit-button100")
        node_type = str(item.get("nodeType") or "button")
    else:
        suffix = str(item.get("id") or "save-button")
        default_props = {
            "buttonText": "保存",
            "plain": False,
            "state": "default",
            "text": False,
            "type": "primary",
        }
        component_name = str(item.get("componentName") or "ev-save-button100")
        node_type = str(item.get("nodeType") or "save-button")
    props = merge_dict(default_props, item.get("props") if isinstance(item.get("props"), dict) else {})
    if item.get("buttonText"):
        props["buttonText"] = repair_text(str(item["buttonText"]))
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=toolbar_id,
        slot=str(item.get("slot") or "button"),
        component_name=component_name,
        node_type=node_type,
        events={},
        props=props,
    )


def build_form(schema: dict, args, fields: list[dict], *, readonly: bool = False) -> None:
    page_id = schema["id"]
    model_alias = identifier(args.model, "record") if args.model else "record"
    layout = normalize_form_layout(args.layout)
    base_item_span = int(layout["layout"].get("itemSpan", 12))
    base_gutter = int(layout["layout"].get("gutter", 0))
    schema["models"].append({
        "modelGuid": stable_model_guid(args.pagetag, model_alias),
        "alias": model_alias,
        "source": "mis" if args.sql_table else "interface" if args.endpoint else "",
        "type": "record",
        "primaryKey": "rowguid",
        "fields": model_fields(fields),
        **({"sqlTableName": args.sql_table} if args.sql_table else {}),
    })
    schema["props"] = {"labelPosition": "top"}

    layout_id = f"layout-manager-1_{page_id}"
    toolbar_id = f"toolbar_{page_id}"
    div_id = f"sform-div-1_{page_id}"
    collapse_id = f"collapse_{page_id}"

    button_slot = [] if readonly else [
        form_toolbar_button(page_id, toolbar_id, index + 1, item)
        for index, item in enumerate(layout["toolbar"].get("buttons") or [])
        if isinstance(item, dict) and item.get("enabled", True)
    ]
    toolbar_position = str(layout["toolbar"].get("position") or "bottom")
    toolbar = component(
        page_id,
        "toolbar",
        suffix="toolbar",
        parent=layout_id,
        slot=toolbar_position,
        children=[],
        component_name="ev-toolbar100",
        slots={"button": button_slot, "title": [], "actions": []},
        props={
            "showTitleSlot": False if toolbar_position == "top" else True,
            "showActionsSlot": False if toolbar_position == "top" else True,
            "position": "top",
            "buttonPosition": layout["toolbar"].get("buttonPosition"),
            "showButtonSlot": not readonly,
        },
    )
    sections = form_sections_from_layout(fields, layout, args.title)
    collapse_items: list[dict] = []
    control_index = 1
    for section_index, section in enumerate(sections, start=1):
        section_title = section["title"] or args.title
        section_layout = merge_dict(layout["layout"], section.get("layout") or {})
        try:
            item_span = int(section_layout.get("itemSpan", base_item_span))
        except (TypeError, ValueError):
            item_span = base_item_span
        if item_span not in {6, 8, 12, 24}:
            item_span = base_item_span
        try:
            gutter = int(section_layout.get("gutter", base_gutter))
        except (TypeError, ValueError):
            gutter = base_gutter
        collapse_item_id = f"collapse-item-{section_index}_{page_id}"
        form_layout, control_index = build_form_section(
            page_id,
            model_alias,
            section["fields"],
            control_index,
            collapse_item_id,
            section_index,
            readonly=readonly,
            schema=schema,
            item_span=item_span,
            gutter=gutter,
        )
        collapse_items.append(
            component(
                page_id,
                f"collapse-item-{section_index}",
                suffix=f"collapse-item-{section_index}",
                parent=collapse_id,
                component_name=f"ev-collapse-item-{section_index}100",
                node_type="collapse-item",
                children=[form_layout],
                props={
                    "tooltipStatus": "default",
                    "defaultActive": True,
                    "tooltipMode": "tooltip",
                    "tooltip": "",
                    "showArrow": True,
                    "state": "normal",
                    "title": section_title,
                },
            )
        )
    collapse = component(
        page_id,
        "collapse",
        suffix="collapse",
        parent=div_id,
        component_name="ev-collapse100",
        node_type="collapse",
        children=collapse_items,
        props={
            "navAffix": True,
            "showIndex": False,
            "accordion": False,
            "headerPrefix": "block",
            "size": "default",
            "showArrow": True,
            "arrowType": "text",
            "showNav": False,
        },
    )
    main = component(
        page_id,
        "sform-div-1",
        suffix="sform-div-1",
        parent=layout_id,
        slot="main",
        component_name="ev-sform-div-1100",
        node_type="div",
        children=[collapse],
        props={"contentClass": "px-xxl"},
    )
    top_slot = [] if readonly or toolbar_position != "top" else [toolbar]
    bottom_slot = [] if readonly or toolbar_position != "bottom" else [toolbar]
    schema["children"] = [
        component(
            page_id,
            "layout-manager-1",
            suffix="layout-manager-1",
            children=[],
            component_name="ev-layout-manager-1100",
            node_type="layout-manager",
            slots={"top": top_slot, "left": [], "bottom": bottom_slot, "main": [main], "right": []},
            props={
                "leftConfig": {"enabled": False},
                "topConfig": {
                    "enabled": bool(top_slot),
                    "defaultHeight": "48px",
                    "inset": False,
                    "resize": False,
                },
                "mainConfig": {"enabled": True},
                "height": "100%",
                "rightConfig": {"enabled": False},
                "bottomConfig": {
                    "showDivider": False,
                    "defaultHeight": "65px",
                    "inset": False,
                    "closed": False,
                    "resize": False,
                    "toggle": False,
                    "enabled": bool(bottom_slot),
                },
            },
        )
    ]


def cli() -> int:
    parser = argparse.ArgumentParser(description="Create page designer page schema file")
    parser.add_argument("--app-root", required=True, help="application root path")
    parser.add_argument("--pagetag", required=True, help="unique page tag, e.g. purchaseproject_list")
    parser.add_argument("--type", choices=["list", "form", "detail"], default="list", help="page type")
    parser.add_argument("--title", required=True, help="page title")
    parser.add_argument("--page-id", help="designer pageId, e.g. page_1781580614416")
    parser.add_argument("--device", choices=sorted(VIEWPORTS), default="desktop")
    parser.add_argument("--endpoint", default="", help="reserved for future resource/action generation")
    parser.add_argument("--model", default="", help="model alias")
    parser.add_argument("--sql-table", default="", help="optional sqlTableName")
    parser.add_argument("--form-page-id", default="", help="target form page id for list add/edit/detail dialogs")
    parser.add_argument("--fields-json", default="[]", help="field JSON array")
    parser.add_argument("--fields-file", help="field JSON array file path (alternative to --fields-json)")
    parser.add_argument("--query-json", default="[]", help="query field JSON array")
    parser.add_argument("--layout-json", default="{}", help="list layout JSON object")
    parser.add_argument("--initial-json", default="[]", help="optional initial/mock data JSON array")
    parser.add_argument("--fields-json-file", help="UTF-8 JSON file path for field array")
    parser.add_argument("--query-json-file", help="UTF-8 JSON file path for query field array")
    parser.add_argument("--layout-json-file", help="UTF-8 JSON file path for list layout object")
    parser.add_argument("--initial-json-file", help="UTF-8 JSON file path for initial/mock data array")
    parser.add_argument("--mock-data", action="store_true", help="generate preview initial data when no initial JSON is provided")
    parser.add_argument("--mock-count", type=int, default=3, help="row count for --mock-data")
    parser.add_argument("--filename", help="file name without extension")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="只预览将写入的内容，不落盘（逐资产人工确认用）")
    parser.add_argument("--confirm", action="store_true",
                        help="确认落盘。落盘前确认红线：不加 --confirm 一律拒绝写文件，必须先 --dry-run 预览")
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir():
        print(f"ERROR: app root does not exist: {app_root}", file=sys.stderr)
        return 1
    if not PAGETAG_PATTERN.match(args.pagetag):
        print(f"ERROR: invalid pagetag: {args.pagetag}", file=sys.stderr)
        return 1

    try:
        fields_json = read_text_arg(args.fields_json, args.fields_json_file)
        query_json = read_text_arg(args.query_json, args.query_json_file)
        layout_json = read_text_arg(args.layout_json, args.layout_json_file)
        initial_json = read_text_arg(args.initial_json, args.initial_json_file)
        fields = normalize_fields(parse_json_arg(fields_json, label="--fields-json"))
        query_fields = normalize_fields(parse_json_arg(query_json, label="--query-json"))
        args.layout = parse_object_arg(layout_json, label="--layout-json")
        args.initial = parse_json_arg(initial_json, label="--initial-json")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    mis_hints = load_mis_field_hints(app_root, args.sql_table)
    fields = apply_mis_hints(fields, mis_hints)
    query_fields = apply_mis_hints(query_fields, mis_hints)
    if args.mock_data and not args.initial:
        args.initial = build_mock_initial(fields, args.mock_count)
    if not fields:
        print(f"ERROR: {args.type} page requires at least one field", file=sys.stderr)
        return 1

    args.title = repair_text(args.title)
    schema_id = page_id_from_pagetag(args.pagetag)
    page_id = args.page_id or (renderer_page_id() if args.type != "list" else None)
    schema = base_schema(schema_id, args.pagetag, args.title, args.device, page_id=page_id)
    if args.type == "list":
        build_list(schema, args, fields, query_fields)
    elif args.type == "form":
        build_form(schema, args, fields)
    elif args.type == "detail":
        build_form(schema, args, fields, readonly=True)

    page_dir = app_root / "page"
    page_dir.mkdir(parents=True, exist_ok=True)
    target = page_dir / f"{safe_filename(args.filename or args.title)}.page.yml"
    if target.exists() and not args.force:
        print(f"ERROR: file already exists: {target}", file=sys.stderr)
        return 1

    content = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"

    # 落盘前确认红线：先 --dry-run 预览，确认后再 --confirm 落盘
    if args.dry_run:
        print(f"ℹ️  [dry-run] 将创建页面: {target}")
        print("ℹ️  [dry-run] 预览内容如下（未写入任何文件）：")
        print("-" * 60)
        print(content)
        print("-" * 60)
        print("ℹ️  [dry-run] 请人工核对；确认无误后去掉 --dry-run 并加 --confirm 落盘。")
        return 0
    if not args.confirm:
        print(
            "ERROR: 拒绝落盘：页面必须经人工预览确认后才能写入。\n"
            "请先用 --dry-run 预览内容，核对无误后再加 --confirm 落盘。\n"
            "（落盘前确认红线：禁止未经 dry-run 预览 + --confirm 确认直接写文件）",
            file=sys.stderr,
        )
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"OK: page file created: {target}")

    if not args.no_validate:
        validator = Path(__file__).with_name("validate_json.py")
        result = subprocess.run([sys.executable, str(validator), str(target)], text=True)
        return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(cli())

