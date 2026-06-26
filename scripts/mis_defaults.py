#!/usr/bin/env python3
"""Shared MIS field defaults for generation and validation."""
from __future__ import annotations

from typing import Any


# Screenshot/mis.md commented fields: final YAML must contain these keys.
MIS_FIELD_REQUIRED_TEMPLATE_KEYS = [
    "name",
    "type",
    "description",
    "length",
    "datasourceCodename",
    "fielddisplaytype",
    "isframeou",
    "isframeuser",
    "isforeignkey",
    "autoincrease",
    "mustfill",
    "defaultvalue",
    "uniquefield",
    "notnull",
]


DEFAULT_FIELD_ATTRS = {
    "datasourceCodename": "",
    "fielddisplaytype": "textbox",
    "isframeou": False,
    "isframeuser": False,
    "isforeignkey": False,
    "autoincrease": False,
    "mustfill": False,
    "defaultvalue": "",
    "uniquefield": False,
    "notnull": True,
    "fieldjd": 2,
    "ismillisecond": False,
    "precision": 0,
    "frameMj": 0,
    "controlwidth": 1,
    "ordernumingrid": 10,
    "dispfielddesc": False,
    "fielddesc": "",
    "todispingrid": True,
    "isquerycondition": False,
    "isorderfield": False,
    "orderdirection": "asc",
    "isexportexcel": False,
    "gridmultirows": False,
    "gridwidth": 100,
    "dispInadd": True,
    "iscustom": False,
}


TYPE_TO_DISPLAY = {
    "nvarchar": "textbox",
    "Integer": "spinner",
    "int": "spinner",
    "Numeric": "spinner",
    "DateTime": "datepicker",
    "datetime": "datepicker",
    "ntext": "textarea",
    "Image": "webuploader",
}


TYPE_TO_DEFAULT_LENGTH = {
    "nvarchar": 50,
    "Integer": 4,
    "int": 4,
    "Numeric": 18,
    "DateTime": 50,
    "datetime": 50,
    "ntext": 50,
    "Image": 50,
}


VALID_MIS_TYPES = set(TYPE_TO_DISPLAY.keys())


def default_display_for_type(field_type: Any) -> str:
    return TYPE_TO_DISPLAY.get(str(field_type or "nvarchar"), "textbox")


def default_length_for_type(field_type: Any) -> int:
    return TYPE_TO_DEFAULT_LENGTH.get(str(field_type or "nvarchar"), 50)


def normalize_mis_field(raw: dict, *, order_index: int | None = None) -> dict:
    """Return a complete MIS field dict while preserving explicit values."""
    field = dict(raw or {})
    field_type = field.get("type") or "nvarchar"
    if not field.get("length"):
        field["length"] = default_length_for_type(field_type)

    normalized = {
        "name": field.get("name", ""),
        "type": field_type,
        "description": field.get("description", ""),
        "length": int(field.get("length") or default_length_for_type(field_type)),
    }
    normalized.update(DEFAULT_FIELD_ATTRS)
    normalized["fielddisplaytype"] = default_display_for_type(field_type)
    if order_index is not None:
        normalized["ordernumingrid"] = order_index * 10
    normalized.update(field)
    if normalized.get("datasourceCodename") and "fielddisplaytype" not in field:
        normalized["fielddisplaytype"] = "combobox"
    return normalized


def primary_key_overrides() -> dict:
    return {
        "isforeignkey": True,
        "uniquefield": True,
        "mustfill": True,
        "todispingrid": False,
        "dispInadd": False,
        "ordernumingrid": 0,
    }
