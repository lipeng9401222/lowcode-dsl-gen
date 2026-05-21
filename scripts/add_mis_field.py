#!/usr/bin/env python3
"""add_mis_field.py — 创建新 MIS 表 或 给已有 MIS 表追加字段.

用法：
    # 1) 创建新 mis 表（默认含 rowguid 主键字段）
    python add_mis_field.py \\
        --metadata /path/to/.../metadata \\
        --table customerinfo --create \\
        --table-desc "客户信息表"

    # 2) 给已有 mis 追加字段
    python add_mis_field.py \\
        --mis /path/to/customerinfo.mis.yml \\
        --name customer_phone --type nvarchar --length 50 \\
        --description "客户电话" --mustfill false

    # 3) 给已有 mis 追加多个字段（JSON 数组）
    python add_mis_field.py \\
        --mis /path/to/customerinfo.mis.yml \\
        --fields-json '[
            {"name": "customer_phone", "type": "nvarchar", "length": 50, "description": "客户电话"},
            {"name": "customer_email", "type": "nvarchar", "length": 100, "description": "邮箱"}
        ]'
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    is_valid_field_name,
    is_valid_mis_name,
    parse_json_arg,
    print_err,
    print_info,
    print_ok,
    print_warn,
    yaml_dump,
    yaml_load,
)


# 字段默认属性（避免每次调用都问 30 个字段）
DEFAULT_FIELD_ATTRS = {
    "datasourceCodename": "",
    "fielddisplaytype": "textbox",  # 会按 type 自动调整
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

# type 到默认 fielddisplaytype 的映射
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


VALID_TYPES = set(TYPE_TO_DISPLAY.keys())


def build_field(
    *,
    name: str,
    field_type: str,
    description: str,
    length: int,
    overrides: dict | None = None,
) -> dict:
    """构造一个完整字段对象（默认值 + 用户覆盖）."""
    if not is_valid_field_name(name):
        raise ValueError(f"字段名 '{name}' 非法（应小写英文+下划线）")
    if field_type not in VALID_TYPES:
        raise ValueError(f"type '{field_type}' 不在白名单内: {sorted(VALID_TYPES)}")

    field = {
        "name": name,
        "type": field_type,
        "description": description,
        "length": length,
    }
    field.update(DEFAULT_FIELD_ATTRS)
    field["fielddisplaytype"] = TYPE_TO_DISPLAY.get(field_type, "textbox")
    if overrides:
        field.update(overrides)
    return field


def build_primary_key_field() -> dict:
    """返回主键字段 rowguid 的标准定义."""
    f = build_field(
        name="rowguid", field_type="nvarchar",
        description="主键", length=50,
        overrides={
            "isforeignkey": True,
            "uniquefield": True,
            "mustfill": True,
            "todispingrid": False,
            "dispInadd": False,
            "ordernumingrid": 0,
        },
    )
    return f


def build_mis_yaml(table_name: str, description: str, fields: list[dict]) -> dict:
    """构造完整 mis yml dict."""
    return {
        "type": "mis",
        "name": table_name,
        "description": description,
        "tableName": table_name,
        "fields": fields,
        "relations": [],
    }


def cli():
    parser = argparse.ArgumentParser(description="创建/修改 MIS 表 yml")

    # 模式 1：创建
    parser.add_argument("--metadata", help="metadata 目录路径（创建模式必填）")
    parser.add_argument("--table", help="表名（小写英文数字、无下划线，如 customerinfo）")
    parser.add_argument("--table-desc", default="", help="表描述")
    parser.add_argument(
        "--create", action="store_true",
        help="创建新 mis 表（含默认 rowguid 主键）",
    )
    parser.add_argument(
        "--no-primary-key", action="store_true",
        help="创建时不自动加 rowguid 主键",
    )

    # 模式 2：追加字段
    parser.add_argument("--mis", help="已有 mis yml 路径（追加模式必填）")

    # 单字段属性
    parser.add_argument("--name", help="字段名（英文+下划线）")
    parser.add_argument("--type", default="nvarchar", help="字段类型 [nvarchar]")
    parser.add_argument("--length", type=int, default=50, help="字段长度 [50]")
    parser.add_argument("--description", default="", help="字段描述（中文）")
    parser.add_argument("--mustfill", default="false", help="是否必填 true/false [false]")
    parser.add_argument("--notnull", default="true", help="是否非空 true/false [true]")
    parser.add_argument("--unique", default="false", help="是否唯一 true/false [false]")
    parser.add_argument(
        "--codename", default="",
        help="绑定代码项名（如 审核状态），自动设置 fielddisplaytype=combobox",
    )
    parser.add_argument(
        "--display", default="",
        help="显示控件类型（textbox/combobox/datepicker等），覆盖按 type 推断的默认值",
    )

    # 多字段
    parser.add_argument(
        "--fields-json", help="字段数组 JSON，一次添加多个字段",
    )

    parser.add_argument(
        "--single-ext", action="store_true",
        help="使用历史单扩展名 .yml（默认 .mis.yml；仅兼容旧项目时使用）",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    parser.add_argument(
        "--allow-empty-fields", action="store_true",
        help="允许创建只含主键、无业务字段的 mis 表（默认拒绝；SKILL.md 资产信息完整性门禁要求先与用户确认字段清单）",
    )
    args = parser.parse_args()

    def parse_bool(s: str) -> bool:
        return s.lower() in ("true", "1", "yes", "y")

    # === 创建模式 ===
    if args.create:
        if not args.metadata or not args.table:
            print_err("创建模式必须提供 --metadata 和 --table")
            return 1
        if not is_valid_mis_name(args.table):
            print_err(f"表名非法: {args.table}（应小写英文数字，且不能包含下划线）")
            return 1

        metadata_dir = Path(args.metadata).resolve()
        if not metadata_dir.is_dir():
            print_err(f"metadata 目录不存在: {metadata_dir}")
            return 1

        mis_dir = metadata_dir / "mis"
        mis_dir.mkdir(parents=True, exist_ok=True)

        ext = ".yml" if args.single_ext else ".mis.yml"
        target = mis_dir / f"{args.table}{ext}"

        if target.exists() and not args.force:
            print_err(f"文件已存在: {target}（--force 覆盖）")
            return 1

        # 构造初始字段
        initial_fields = []
        if not args.no_primary_key:
            initial_fields.append(build_primary_key_field())

        # 解析业务字段
        business_fields_count = 0
        if args.fields_json:
            try:
                extras = parse_json_arg(args.fields_json, expected_type=list, label="--fields-json")
            except ValueError as e:
                print_err(str(e))
                return 1
            for f in extras:
                initial_fields.append(build_field(
                    name=f["name"],
                    field_type=f.get("type", "nvarchar"),
                    description=f.get("description", ""),
                    length=int(f.get("length", 50)),
                    overrides={k: v for k, v in f.items()
                               if k not in ("name", "type", "description", "length")},
                ))
                business_fields_count += 1

        # 资产信息完整性门禁：业务字段必须先与用户确认
        if business_fields_count == 0 and not args.allow_empty_fields:
            print_err(
                "未提供业务字段（--fields-json 至少 1 条非主键字段）。\n"
                "SKILL.md 「资产信息完整性门禁」要求：mis 表创建前必须先与用户确认字段名/类型/长度/说明/必填规则。\n"
                "如果确实需要先建只含主键的骨架（不推荐，后续仍需补字段），请显式加 --allow-empty-fields。"
            )
            return 1
        if business_fields_count == 0:
            print_warn("已显式允许创建只含主键的 mis 表（--allow-empty-fields），后续仍需补业务字段")

        data = build_mis_yaml(args.table, args.table_desc, initial_fields)
        yaml_dump(data, target)
        print_ok(f"已创建: {target}")
        print_info(f"  - 表名: {args.table}")
        print_info(f"  - 字段数: {len(initial_fields)}（业务字段 {business_fields_count}）")
        return 0

    # === 追加模式 ===
    if not args.mis:
        print_err("追加模式必须提供 --mis 指向已有 yml")
        return 1

    target = Path(args.mis).resolve()
    if not target.is_file():
        print_err(f"文件不存在: {target}")
        return 1

    try:
        data = yaml_load(target)
    except Exception as e:
        print_err(f"解析 yml 失败: {e}")
        return 1

    if data.get("type") != "mis":
        print_warn(f"文件 type 不是 'mis'，是 '{data.get('type')}'，请确认")

    new_fields = []
    if args.fields_json:
        try:
            extras = parse_json_arg(args.fields_json, expected_type=list, label="--fields-json")
        except ValueError as e:
            print_err(str(e))
            return 1
        for f in extras:
            new_fields.append(build_field(
                name=f["name"],
                field_type=f.get("type", "nvarchar"),
                description=f.get("description", ""),
                length=int(f.get("length", 50)),
                overrides={k: v for k, v in f.items()
                           if k not in ("name", "type", "description", "length")},
            ))
    elif args.name:
        overrides = {
            "mustfill": parse_bool(args.mustfill),
            "notnull": parse_bool(args.notnull),
            "uniquefield": parse_bool(args.unique),
        }
        if args.codename:
            overrides["datasourceCodename"] = args.codename
            overrides["fielddisplaytype"] = "combobox"
        if args.display:
            overrides["fielddisplaytype"] = args.display

        new_fields.append(build_field(
            name=args.name,
            field_type=args.type,
            description=args.description,
            length=args.length,
            overrides=overrides,
        ))
    else:
        print_err("请提供 --name（单字段）或 --fields-json（多字段）")
        return 1

    existing_fields = data.get("fields") or []
    existing_names = {f.get("name") for f in existing_fields}
    for f in new_fields:
        if f["name"] in existing_names:
            print_warn(f"字段已存在，跳过: {f['name']}")
            continue
        existing_fields.append(f)
        existing_names.add(f["name"])
        print_ok(f"已添加字段: {f['name']} ({f['type']}, {f['description']})")

    data["fields"] = existing_fields
    yaml_dump(data, target)
    print_info(f"已写回: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
