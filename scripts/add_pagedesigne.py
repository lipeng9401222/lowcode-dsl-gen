#!/usr/bin/env python3
"""add_pagedesigne.py — 创建页面设计器 Core Schema yml（内容仍为 JSON 文本）.

用法：
    # 列表页
    python add_pagedesigne.py \\
        --metadata /path/to/.../metadata \\
        --type list \\
        --title "采购立项列表" \\
        --endpoint "/api/purchaseproject" \\
        --fields-json '[{"name":"project_name","label":"项目名称","type":"string"}]' \\
        --query-json '[{"name":"keyword","label":"关键词","type":"string"}]'

    # 表单页
    python add_pagedesigne.py \\
        --metadata /path/to/.../metadata \\
        --type form \\
        --title "采购立项表单" \\
        --model project \\
        --endpoint "/api/purchaseproject" \\
        --fields-json '[{"name":"project_name","label":"项目名称","required":true}]'
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    gen_page_id,
    json_dump,
    parse_json_arg,
    print_err,
    print_info,
    print_ok,
    print_warn,
    safe_filename,
)


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
    "DateTime": "date",
    "datetime": "date",
    "Image": "string",
}


def identifier(value: str, default: str) -> str:
    """转成页面 schema 可用的模型/action/resource 标识."""
    raw = re.sub(r"[^a-zA-Z0-9_]+", "_", value or "").strip("_")
    if not raw:
        raw = default
    if not re.match(r"^[a-zA-Z]", raw):
        raw = f"{default}_{raw}"
    return raw[0].lower() + raw[1:]


def cap(value: str) -> str:
    return value[:1].upper() + value[1:]


def normalize_field(item, index: int) -> dict:
    if isinstance(item, str):
        item = {"name": item, "label": item}
    if not isinstance(item, dict):
        raise ValueError(f"字段 {index} 必须是对象或字符串")

    name = item.get("name") or item.get("field") or item.get("key")
    if not name:
        raise ValueError(f"字段 {index} 缺少 name")
    name = identifier(str(name), f"field{index}")
    label = item.get("label") or item.get("description") or item.get("title") or name
    field_type = TYPE_MAP.get(item.get("type"), item.get("type", "string"))
    field_type = field_type if field_type in {"string", "number", "boolean", "date", "object", "array"} else "string"

    field = {
        "name": name,
        "label": str(label),
        "type": field_type,
    }
    rules = dict(item.get("rules") or {})
    if item.get("required") is True or item.get("mustfill") is True:
        rules["required"] = True
    if rules:
        field["rules"] = rules
    if item.get("source"):
        field["source"] = item["source"]
    return field


def normalize_fields(raw_items) -> list[dict]:
    return [normalize_field(item, i + 1) for i, item in enumerate(raw_items or [])]


def model_fields(fields: list[dict]) -> dict:
    result = {}
    for field in fields:
        meta = {"type": field["type"], "label": field["label"]}
        if field.get("rules"):
            meta["rules"] = field["rules"]
        result[field["name"]] = meta
    return result


def node(page_id: str, suffix: str, node_type: str, **kwargs) -> dict:
    data = {
        "id": identifier(f"{page_id}_{suffix}", suffix),
        "version": "1.0.0",
        "type": node_type,
    }
    data.update({k: v for k, v in kwargs.items() if v not in (None, {}, [])})
    return data


def input_node(page_id: str, model_name: str, field: dict, *, action: str | None = None) -> dict:
    events = {"change": action} if action else None
    node_type = "select" if field.get("source") else "input"
    props = {"label": field["label"]}
    if field["type"] == "date":
        props["inputType"] = "date"
    elif field["type"] == "number":
        props["inputType"] = "number"
    return node(
        page_id,
        f"{model_name}_{field['name']}",
        node_type,
        model=f"{model_name}.{field['name']}",
        source=field.get("source"),
        props=props,
        events=events,
    )


def base_schema(page_id: str, title: str, device: str) -> dict:
    return {
        "schemaVersion": "core-1.0",
        "kind": "page",
        "id": page_id,
        "title": title,
        "viewport": VIEWPORTS[device],
        "theme": {
            "background": "#FFFFFF",
            "textColor": "#111827",
            "fontFamily": "system",
        },
        "models": {},
        "resources": {},
        "actions": {},
        "events": {},
        "children": [],
    }


def add_endpoint(schema: dict, resource_id: str, endpoint: str, operations: dict) -> None:
    if endpoint:
        schema["resources"][resource_id] = {
            "type": "endpoint",
            "baseUrl": endpoint,
            "operations": operations,
        }


def build_list(schema: dict, args, fields: list[dict], query_fields: list[dict]) -> None:
    page_id = schema["id"]
    list_model = identifier(args.model, "items") if args.model else "items"
    search_model = "search"
    resource_id = identifier(f"{list_model}Api", "pageApi")
    refresh_action = identifier(f"refresh{cap(list_model)}", "refresh")

    if query_fields:
        schema["models"][search_model] = {
            "type": "record",
            "fields": model_fields(query_fields),
            "initial": {f["name"]: "" for f in query_fields},
        }
    schema["models"][list_model] = {
        "type": "collection",
        "primaryKey": "rowguid",
        "fields": model_fields(fields),
    }

    add_endpoint(schema, resource_id, args.endpoint, {"list": {"method": "GET", "path": ""}})
    if args.endpoint:
        params = {f["name"]: f"model.{search_model}.{f['name']}" for f in query_fields}
        schema["actions"][refresh_action] = {
            "steps": [{
                "use": f"{resource_id}.list",
                "params": params,
                "assign": {f"model.{list_model}": "response.items"},
            }],
            "onError": {"notify": "加载失败", "stop": True},
        }
        schema["events"]["load"] = refresh_action

    children = []
    if query_fields:
        search_children = [
            input_node(page_id, search_model, field, action=refresh_action if args.endpoint else None)
            for field in query_fields
        ]
        if args.endpoint:
            search_children.append(node(
                page_id,
                "search_button",
                "button",
                props={"label": "查询"},
                events={"click": refresh_action},
            ))
        children.append(node(page_id, "search_form", "form", children=search_children))
    elif args.endpoint:
        children.append(node(
            page_id,
            "refresh_button",
            "button",
            props={"label": "刷新"},
            events={"click": refresh_action},
        ))

    children.append(node(
        page_id,
        "table",
        "table",
        model=list_model,
        columns=[{"type": "field", "field": f["name"], "label": f["label"]} for f in fields],
    ))
    schema["children"] = children


def build_form(schema: dict, args, fields: list[dict]) -> None:
    page_id = schema["id"]
    form_model = identifier(args.model, "record") if args.model else "record"
    resource_id = identifier(f"{form_model}Api", "pageApi")
    submit_action = identifier(f"submit{cap(form_model)}", "submit")

    schema["models"][form_model] = {
        "type": "record",
        "primaryKey": "rowguid",
        "fields": model_fields(fields),
        "initial": {f["name"]: None if f["type"] in {"number", "date"} else "" for f in fields},
    }
    add_endpoint(schema, resource_id, args.endpoint, {
        "detail": {"method": "GET", "path": "/detail"},
        "save": {"method": "POST", "path": ""},
    })
    if args.endpoint:
        schema["actions"][submit_action] = {
            "steps": [
                {"validate": f"model.{form_model}"},
                {"use": f"{resource_id}.save", "body": f"model.{form_model}"},
                {"notify": "保存成功"},
            ],
            "onError": {"notify": "保存失败", "stop": True},
        }

    form_children = [input_node(page_id, form_model, field) for field in fields]
    if args.endpoint:
        form_children.append(node(
            page_id,
            "submit_button",
            "button",
            props={"label": "保存"},
            events={"click": submit_action},
        ))
    schema["children"] = [node(page_id, "form", "form", model=form_model, children=form_children)]


def build_detail(schema: dict, args, fields: list[dict]) -> None:
    page_id = schema["id"]
    detail_model = identifier(args.model, "record") if args.model else "record"
    resource_id = identifier(f"{detail_model}Api", "pageApi")
    load_action = identifier(f"load{cap(detail_model)}", "load")

    schema["models"][detail_model] = {
        "type": "record",
        "primaryKey": "rowguid",
        "fields": model_fields(fields),
    }
    add_endpoint(schema, resource_id, args.endpoint, {"detail": {"method": "GET", "path": "/detail"}})
    if args.endpoint:
        schema["actions"][load_action] = {
            "steps": [{
                "use": f"{resource_id}.detail",
                "params": {"rowguid": "params.rowguid"},
                "assign": {f"model.{detail_model}": "response"},
            }],
            "onError": {"notify": "加载详情失败", "stop": True},
        }
        schema["events"]["load"] = load_action
    schema["children"] = [
        node(page_id, "detail", "form", model=detail_model, children=[
            node(
                page_id,
                f"{detail_model}_{field['name']}",
                "text",
                model=f"{detail_model}.{field['name']}",
                props={"label": field["label"]},
            )
            for field in fields
        ])
    ]


def build_custom(schema: dict, args, fields: list[dict]) -> None:
    if not fields:
        return
    custom_model = identifier(args.model, "record") if args.model else "record"
    schema["models"][custom_model] = {
        "type": "record",
        "fields": model_fields(fields),
    }
    schema["children"] = [
        node(schema["id"], "content", "form", model=custom_model, children=[
            input_node(schema["id"], custom_model, field) for field in fields
        ])
    ]


def cli():
    parser = argparse.ArgumentParser(description="创建 pagedesigne Core Schema yml（内容仍为 JSON 文本）")
    parser.add_argument("--metadata", required=True, help="metadata 目录路径")
    parser.add_argument("--type", choices=["list", "form", "detail", "custom"], default="custom", help="页面类型")
    parser.add_argument("--title", required=True, help="页面标题（中文）")
    parser.add_argument("--page-id", help="页面稳定 id；不填则自动生成")
    parser.add_argument("--device", choices=sorted(VIEWPORTS), default="desktop", help="设备类型 [desktop]")
    parser.add_argument("--endpoint", default="", help="页面主接口 baseUrl，如 /api/employees")
    parser.add_argument("--model", default="", help="主数据模型名；列表页默认 items，表单/详情默认 record")
    parser.add_argument("--fields-json", default="[]", help="字段 JSON 数组")
    parser.add_argument("--query-json", default="[]", help="查询字段 JSON 数组（列表页使用）")
    parser.add_argument("--filename", help="自定义文件名（不含扩展名），默认用页面标题")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    parser.add_argument("--no-validate", action="store_true", help="跳过 validate_yml.py 自检")
    args = parser.parse_args()

    metadata_dir = Path(args.metadata).resolve()
    if not metadata_dir.is_dir():
        print_err(f"metadata 目录不存在: {metadata_dir}")
        return 1

    try:
        fields = normalize_fields(parse_json_arg(args.fields_json, expected_type=list, label="--fields-json"))
        query_fields = normalize_fields(parse_json_arg(args.query_json, expected_type=list, label="--query-json"))
    except ValueError as e:
        print_err(str(e))
        return 1

    if args.type in {"list", "form", "detail"} and not fields:
        print_err(f"{args.type} 页面至少需要提供一个字段")
        return 1

    page_id = args.page_id or gen_page_id(args.title)
    schema = base_schema(page_id, args.title, args.device)
    if args.type == "list":
        build_list(schema, args, fields, query_fields)
    elif args.type == "form":
        build_form(schema, args, fields)
    elif args.type == "detail":
        build_detail(schema, args, fields)
    else:
        build_custom(schema, args, fields)

    page_dir = metadata_dir / "pagedesigne"
    page_dir.mkdir(parents=True, exist_ok=True)
    filename = args.filename or safe_filename(args.title)
    target = page_dir / f"{filename}.pagedesigne.yml"
    if target.exists() and not args.force:
        print_err(f"文件已存在: {target}（--force 覆盖）")
        return 1

    json_dump(schema, target)
    print_ok(f"页面 schema 已创建: {target}")
    print_info(f"  - 标题: {args.title}")
    print_info(f"  - 页面类型: {args.type}")
    print_info(f"  - 页面 id: {page_id}")
    print_info(f"  - 字段数: {len(fields)}")

    if not args.no_validate:
        validate_script = Path(__file__).parent / "validate_yml.py"
        result = subprocess.run(
            [sys.executable, str(validate_script), str(target)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print_ok("校验通过")
        else:
            print_warn("校验未通过：")
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(cli())
