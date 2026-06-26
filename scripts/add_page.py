#!/usr/bin/env python3
"""add_page.py - create page designer JSON files.

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


def parse_json_arg(value: str, *, label: str) -> list:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} parse failed: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{label} must be a JSON array")
    return data


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
    return {
        "name": name,
        "label": str(item.get("label") or item.get("description") or item.get("title") or name),
        "type": field_type,
    }


def normalize_fields(items) -> list[dict]:
    return [normalize_field(item, index + 1) for index, item in enumerate(items or [])]


def model_fields(fields: list[dict]) -> dict:
    return {
        field["name"]: {
            "type": field["type"],
            "label": field["label"],
        }
        for field in fields
    }


def model_expr(model_alias: str, field_name: str | None = None) -> dict:
    path = f"$model.{model_alias}"
    if field_name:
        path = f"{path}.{field_name}"
    return {"$expr": path}


def component(page_id: str, component_type: str, *, suffix: str | None = None,
              parent: str | None = None, slot: str | None = None,
              component_name: str | None = None, node_type: str | None = None,
              props: dict | None = None, children: list | None = None,
              slots: dict | None = None, events: dict | None = None) -> dict:
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
    if events is not None:
        data["events"] = events
    if slots is not None:
        data["slots"] = slots
    return data


def editor_type(field_type: str) -> str:
    if field_type == "number":
        return "input-number"
    return "input"


def editor_props(field: dict) -> dict:
    if field["type"] in {"date", "datetime"}:
        return {
            "clearable": True,
            "format": "YYYY-MM-DD",
            "placeholder": f"请选择{field['label']}",
            "type": "date",
        }
    if field["type"] == "number":
        return {
            "min": 0,
            "max": 999999999,
            "precision": 2,
            "step": 1,
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
                node_type=editor_type(field["type"]),
                props=editor_props(field),
            )
        ],
        props={
            "modelValue": model_expr(model_alias, field["name"]),
            "state": "normal",
            "title": field["label"],
            "width": 180 if field["type"] in {"date", "datetime"} else 220,
            "align": "left",
            "allowHtml": False,
            "displayField": "",
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
            "default": True,
            "isTreeDataSource": False,
            "isOrgDataSource": False,
            "modelValue": model_expr(model_alias, field["name"]),
            "defaultOperation": "EQ",
            "label": field["label"],
            "state": "normal",
            "fieldType": field["type"],
            "operation": ["EQ", "NQ"],
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


def delete_button_props() -> dict:
    return {
        "buttonText": "删除选中",
        "plain": False,
        "state": "default",
        "text": False,
        "type": "danger",
    }


def table_action(page_id: str, table_id: str, action_index: int, action_type: str,
                 icon: str, label: str, url: str, dialog_title: str = "") -> dict:
    suffix = f"table-action-{action_index}"
    props = {
        "actionType": action_type,
        "carryParentPageParam": False,
        "actionStyle": "icon",
        "icon": icon,
        "dialogHeight": "800px",
        "dialogWidth": "1000px",
        "label": label,
        "params": [],
        "url": url,
        "deleteTip": "是否确认删除已选中的记录？",
        "openType": "dialog",
    }
    if dialog_title:
        props["dialogTitle"] = dialog_title
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=f"table-action-column-1_{page_id}",
        component_name=f"ev-table-action-{action_index}100",
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
        component_name="ev-table-action-column-1100",
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
            "ellipsis": True,
        },
    )


def base_schema(schema_id: str, pagetag: str, title: str, device: str, *, page_id: str | None = None) -> dict:
    schema = {
        "pagetag": pagetag,
        "schemaVersion": "core-1.0",
        "kind": "page",
        "id": schema_id,
        "title": title,
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
    schema["models"].append({
        "modelGuid": stable_model_guid(args.pagetag, model_alias),
        "alias": model_alias,
        "source": "mis" if args.sql_table else "interface" if args.endpoint else "",
        "type": "collection",
        "primaryKey": "rowguid",
        "fields": model_fields(fields),
        **({"sqlTableName": args.sql_table} if args.sql_table else {}),
    })

    container_id = f"list-container_{page_id}"
    toolbar_id = f"toolbar_{page_id}"
    table_id = f"table_{page_id}"

    toolbar = component(
        page_id,
        "toolbar",
        suffix="toolbar",
        parent=container_id,
        children=[],
        component_name="ev-toolbar100",
        slots={
            "title": [
                component(
                    page_id,
                    "toolbar-title",
                    suffix="toolbar-title",
                    parent=toolbar_id,
                    slot="title",
                    component_name="ev-toolbar-title100",
                    props={"title": args.title},
                )
            ],
            "button": [
                component(
                    page_id,
                    "add-button",
                    suffix="add-button",
                    parent=toolbar_id,
                    slot="button",
                    component_name="sform-add-button100",
                    node_type="add-button",
                    events={},
                    props=add_button_props(target_page_id),
                ),
                component(
                    page_id,
                    "del-button",
                    suffix="del-button",
                    parent=toolbar_id,
                    slot="button",
                    component_name="ev-del-button100",
                    node_type="del-button",
                    events={},
                    props=delete_button_props(),
                )
            ],
            "search": [
                search_control(page_id, model_alias, field, index + 1, toolbar_id)
                for index, field in enumerate(query_fields)
            ],
            "actions": [
                component(
                    page_id,
                    "toolbar-more",
                    suffix="toolbar-more",
                    parent=toolbar_id,
                    slot="actions",
                    component_name="ev-toolbar-more100",
                    props={},
                )
            ],
        },
        props={
            "template": "col-1",
            "showTitleSlot": False,
            "filterAdvancedFixed": "popover",
            "mixSearchDefault": False,
            "showActionsSlot": True,
            "showSearchSlot": bool(query_fields),
            "position": "top",
            "mixSearch": False,
            "buttonPosition": "left",
            "showButtonSlot": True,
        },
    )

    table = component(
        page_id,
        "table",
        suffix="table",
        parent=container_id,
        component_name="ev-table100",
        node_type="table",
        children=[
            table_column(page_id, model_alias, field, index + 1, table_id)
            for index, field in enumerate(fields)
        ] + [table_action_column(page_id, table_id, target_page_id)],
        props={
            "modelValue": model_expr(model_alias),
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
                 *, readonly: bool = False) -> dict:
    suffix = f"control-{index}"
    control_type = "date-picker" if field["type"] in {"date", "datetime"} else editor_type(field["type"])
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
    else:
        props.update({
            "clearable": not readonly,
            "unit": "",
            "maxlength": 500,
            "showWordLimit": False,
            "placeholder": f"请输入{field['label']}",
            "type": "textarea" if field["name"] in {"remark", "description"} else "text",
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
    )


def form_item(page_id: str, model_alias: str, field: dict, index: int, parent_id: str,
              *, readonly: bool = False) -> dict:
    suffix = f"form-item-{index}"
    item_id = f"{suffix}_{page_id}"
    return component(
        page_id,
        suffix,
        suffix=suffix,
        parent=parent_id,
        component_name=f"ev-form-item-{index}100",
        node_type="form-item",
        children=[form_control(page_id, model_alias, field, index, item_id, readonly=readonly)],
        props={
            "labelPosition": "right",
            "labelTooltip": "",
            "labelWidth": "auto",
            "label": field["label"],
            "span": 24 if field["name"] in {"remark", "description"} else 12,
        },
    )


def build_form(schema: dict, args, fields: list[dict], *, readonly: bool = False) -> None:
    page_id = schema["id"]
    model_alias = identifier(args.model, "record") if args.model else "record"
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
    collapse_item_id = f"collapse-item-1_{page_id}"
    form_layout_id = f"form-layout_{page_id}"

    button_slot = [] if readonly else [
        component(
            page_id,
            "save-button",
            suffix="save-button",
            parent=toolbar_id,
            slot="button",
            component_name="ev-save-button100",
            node_type="save-button",
            events={},
            props={
                "buttonText": "保存",
                "plain": False,
                "state": "default",
                "text": False,
                "type": "primary",
            },
        )
    ]
    toolbar = component(
        page_id,
        "toolbar",
        suffix="toolbar",
        parent=layout_id,
        slot="bottom",
        children=[],
        component_name="ev-toolbar100",
        slots={"button": button_slot, "title": [], "actions": []},
        props={
            "showTitleSlot": True,
            "showActionsSlot": True,
            "position": "top",
            "buttonPosition": "right",
            "showButtonSlot": not readonly,
        },
    )
    form_layout = component(
        page_id,
        "form-layout",
        suffix="form-layout",
        parent=collapse_item_id,
        component_name="ev-form-layout100",
        node_type="form-layout",
        children=[
            form_item(page_id, model_alias, field, index + 1, form_layout_id, readonly=readonly)
            for index, field in enumerate(fields)
        ],
        props={"gutter": 0, "itemSpan": 24},
    )
    collapse_item = component(
        page_id,
        "collapse-item-1",
        suffix="collapse-item-1",
        parent=collapse_id,
        component_name="ev-collapse-item-1100",
        node_type="collapse-item",
        children=[form_layout],
        props={
            "tooltipStatus": "default",
            "defaultActive": True,
            "tooltipMode": "tooltip",
            "tooltip": "",
            "showArrow": True,
            "state": "normal",
            "title": args.title,
        },
    )
    collapse = component(
        page_id,
        "collapse",
        suffix="collapse",
        parent=div_id,
        component_name="ev-collapse100",
        node_type="collapse",
        children=[collapse_item],
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
    schema["children"] = [
        component(
            page_id,
            "layout-manager-1",
            suffix="layout-manager-1",
            children=[],
            component_name="ev-layout-manager-1100",
            node_type="layout-manager",
            slots={"top": [], "left": [], "bottom": [toolbar], "main": [main], "right": []},
            props={
                "leftConfig": {"enabled": False},
                "topConfig": {"enabled": False},
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
                    "enabled": not readonly,
                },
            },
        )
    ]


def cli() -> int:
    parser = argparse.ArgumentParser(description="Create page designer JSON")
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
    parser.add_argument("--query-json", default="[]", help="query field JSON array")
    parser.add_argument("--filename", help="file name without extension")
    parser.add_argument("--force", action="store_true")
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
        fields = normalize_fields(parse_json_arg(args.fields_json, label="--fields-json"))
        query_fields = normalize_fields(parse_json_arg(args.query_json, label="--query-json"))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not fields:
        print(f"ERROR: {args.type} page requires at least one field", file=sys.stderr)
        return 1

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
    target = page_dir / f"{safe_filename(args.filename or args.title)}.json"
    if target.exists() and not args.force:
        print(f"ERROR: file already exists: {target}", file=sys.stderr)
        return 1
    target.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: page JSON created: {target}")

    if not args.no_validate:
        validator = Path(__file__).with_name("validate_json.py")
        result = subprocess.run([sys.executable, str(validator), str(target)], text=True)
        return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(cli())

