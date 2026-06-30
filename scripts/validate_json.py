#!/usr/bin/env python3
"""validate_json.py - validate page designer JSON files."""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path


PAGETAG_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PAGE_ID_PATTERN = re.compile(r"^page_\d+$")


class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: ERROR: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: WARN: {message}")


def model_index(data: dict, result: Result, path: str) -> dict:
    raw = data.get("models")
    models = {}
    model_guids: set[str] = set()
    if not isinstance(raw, list):
        result.err(path, "models must be an array")
        return models
    for i, model in enumerate(raw):
        if not isinstance(model, dict):
            result.err(path, f"models[{i}] must be an object")
            continue
        model_guid = model.get("modelGuid")
        if not isinstance(model_guid, str) or not model_guid:
            result.err(path, f"models[{i}].modelGuid must be a non-empty UUID string")
        elif not is_uuid(model_guid):
            result.err(path, f"models[{i}].modelGuid must be a valid UUID: {model_guid}")
        elif model_guid in model_guids:
            result.err(path, f"duplicate modelGuid: {model_guid}")
        else:
            model_guids.add(model_guid)
        alias = model.get("alias")
        if not isinstance(alias, str) or not alias:
            result.err(path, f"models[{i}].alias must be a non-empty string")
            continue
        if alias in models:
            result.err(path, f"duplicate model alias: {alias}")
            continue
        if model.get("type") not in {"record", "collection"}:
            result.err(path, f"models[{i}].type must be record or collection")
        if not isinstance(model.get("fields"), dict):
            result.err(path, f"models[{i}].fields must be an object")
            model["fields"] = {}
        models[alias] = model
    return models


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (TypeError, ValueError):
        return False


def model_ref_path(ref) -> str:
    if isinstance(ref, str):
        return ref
    if isinstance(ref, dict) and isinstance(ref.get("$expr"), str):
        expr = ref["$expr"]
        if expr.startswith("$model."):
            return expr[len("$model."):]
    return ""


def model_ref_exists(ref, models: dict, *, allow_root: bool = True) -> bool:
    ref = model_ref_path(ref)
    if not ref:
        return False
    parts = ref.split(".")
    root = parts[0]
    if root not in models:
        return False
    if len(parts) == 1:
        return allow_root
    return parts[1] in (models[root].get("fields") or {})


def iter_nodes(nodes, owner="children"):
    if not isinstance(nodes, list):
        return
    for index, node in enumerate(nodes):
        node_path = f"{owner}[{index}]"
        if not isinstance(node, dict):
            yield node_path, node
            continue
        yield node_path, node
        children = node.get("children")
        if isinstance(children, list):
            yield from iter_nodes(children, f"{node_path}.children")
        slots = node.get("slots")
        if isinstance(slots, dict):
            for slot_name, slot_nodes in slots.items():
                if isinstance(slot_nodes, list):
                    yield from iter_nodes(slot_nodes, f"{node_path}.slots.{slot_name}")


def validate_page(path: Path, result: Result) -> None:
    path_label = str(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        result.err(path_label, f"invalid JSON: {exc}")
        return
    if not isinstance(data, dict):
        result.err(path_label, "top-level value must be an object")
        return

    if data.get("schemaVersion") != "core-1.0":
        result.err(path_label, "schemaVersion must be core-1.0")
    if data.get("kind") != "page":
        result.err(path_label, "kind must be page")
    pagetag = data.get("pagetag")
    if not isinstance(pagetag, str) or not PAGETAG_PATTERN.match(pagetag):
        result.err(path_label, "pagetag must match ^[a-z][a-z0-9_]*$")
    page_id = data.get("pageId")
    if page_id is not None and (not isinstance(page_id, str) or not page_id):
        result.warn(path_label, "pageId should be a non-empty designer id for renderer URLs when present")
    elif isinstance(page_id, str) and not PAGE_ID_PATTERN.match(page_id):
        result.warn(path_label, f"pageId should use designer format page_<timestamp>: {page_id}")
    if not isinstance(data.get("children"), list):
        result.err(path_label, "children must be an array")

    models = model_index(data, result, path_label)
    component_ids: list[str] = []

    for owner, node in iter_nodes(data.get("children") or []):
        if not isinstance(node, dict):
            result.err(path_label, f"{owner} must be an object")
            continue
        component_type = node.get("componentType")
        if not isinstance(component_type, str) or not component_type:
            result.err(path_label, f"{owner}.componentType must be a non-empty string")
        component_id = node.get("componentId")
        if isinstance(component_id, str) and component_id:
            component_ids.append(component_id)
        else:
            result.err(path_label, f"{owner}.componentId must be a non-empty string")

        props = node.get("props")
        if props is not None and not isinstance(props, dict):
            result.err(path_label, f"{owner}.props must be an object")
            props = {}
        props = props or {}

        if node.get("type") == "collapse":
            children = node.get("children")
            if not isinstance(children, list) or not children:
                result.warn(path_label, f"{owner} is a collapse without children")

        model_value = props.get("modelValue")
        if model_value and component_type != "table":
            if not model_ref_exists(model_value, models, allow_root=False):
                result.err(path_label, f"{owner}.props.modelValue references unknown model field: {model_ref_path(model_value) or model_value}")
        if model_value and component_type == "table":
            if not model_ref_exists(model_value, models, allow_root=True):
                result.err(path_label, f"{owner}.props.modelValue references unknown model: {model_ref_path(model_value) or model_value}")

        slots = node.get("slots")
        if slots is not None and not isinstance(slots, dict):
            result.err(path_label, f"{owner}.slots must be an object")
        children = node.get("children")
        if children is not None and not isinstance(children, list):
            result.err(path_label, f"{owner}.children must be an array")

    duplicates = sorted({item for item in component_ids if component_ids.count(item) > 1})
    if duplicates:
        result.err(path_label, f"duplicate componentId values: {duplicates}")


def collect_targets(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.rglob("*.json"))
    return []


def cli() -> int:
    parser = argparse.ArgumentParser(description="Validate page designer JSON")
    parser.add_argument("target", help="JSON file or directory")
    args = parser.parse_args()

    target = Path(args.target)
    result = Result()
    targets = collect_targets(target)
    if not targets:
        result.err(str(target), "no JSON files found")

    for item in targets:
        validate_page(item, result)

    for warning in result.warnings:
        print(warning)
    for error in result.errors:
        print(error, file=sys.stderr)
    if result.errors:
        print(f"FAILED: {len(result.errors)} error(s), {len(result.warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(targets)} JSON file(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
