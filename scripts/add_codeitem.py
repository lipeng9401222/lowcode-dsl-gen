#!/usr/bin/env python3
"""add_codeitem.py — 在指定应用根目录追加一个代码项 yml.

用法：
    # 简单：从命令行参数提供 items
    python add_codeitem.py \\
        --app-root /path/to/.../<apptag> \\
        --name 审核状态 \\
        --description "审核状态字典" \\
        --items "草稿:0:5,待审核:1:2,审核通过:2:3"

    # 复杂：从 JSON 字符串提供 items（支持完整字段）
    python add_codeitem.py \\
        --app-root /path/to/.../<apptag> \\
        --name 审核状态 \\
        --description "审核状态字典" \\
        --items-json '[
            {"codetext": "草稿", "codevalue": "0", "ordernumber": 5},
            {"codetext": "待审核", "codevalue": "1", "ordernumber": 2}
        ]'

    # 修改：在已有代码项里追加子项
    python add_codeitem.py \\
        --file /path/to/审核状态.codeitem.yml \\
        --append-items "审核驳回:3:4"

兼容：--metadata 旧参数仍可用，等价于 --app-root（输出 deprecation warn）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    assert_no_metadata_layer,
    check_landing,
    parse_json_arg,
    print_err,
    print_info,
    print_ok,
    print_warn,
    read_json_param,
    safe_filename,
    yaml_dump,
    yaml_dump_str,
    yaml_load,
)


def parse_items_str(items_str: str) -> list[dict]:
    """解析 'text:value:ordernumber,text2:value2' 风格的字符串."""
    result = []
    for part in items_str.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) < 2:
            raise ValueError(f"items 格式错误: {part}（应为 text:value 或 text:value:ordernumber）")
        item = {
            "codetext": fields[0].strip(),
            "codevalue": fields[1].strip(),
        }
        if len(fields) >= 3 and fields[2].strip():
            item["ordernumber"] = int(fields[2].strip())
        result.append(item)
    return result

def _flatten_items(items: list[dict]) -> list[dict]:
    """将可能含 label/children 嵌套结构的 items 扁平化为 codetext/codevalue 列表.

    AI agent 常生成如下格式：
        [{"label": "项目类型", "children": [{"codetext": "研发项目", "codevalue": "01"}, ...]}]
    本函数自动提取 children 中的子项，忽略外层分组信息。
    """
    flat: list[dict] = []
    for item in items:
        if "children" in item and isinstance(item["children"], list):
            # 嵌套结构：提取 children
            flat.extend(_flatten_items(item["children"]))
        elif "codetext" in item:
            flat.append(item)
        elif "label" in item and "value" in item:
            # 兼容 label/value 格式
            flat.append({
                "codetext": item["label"],
                "codevalue": item["value"],
                **{k: v for k, v in item.items() if k not in ("label", "value")},
            })
        else:
            # 未知格式，原样保留让后续逻辑报错
            flat.append(item)
    return flat


def build_codeitem_yaml(name: str, description: str, items: list[dict]) -> str:
    """直接构造代码项 yml 字符串（保持注释和顺序）."""
    items = _flatten_items(items)
    lines = []
    lines.append("# 固定标识")
    lines.append("type: codeitem")
    lines.append("# 代码名称")
    lines.append(f"name: {name}")
    lines.append("# 代码说明")
    lines.append(f"description: {description}" if description else "description: ")
    lines.append("# 代码子项列表")
    lines.append("items:")
    for item in items:
        lines.append(f'  - codetext: {item["codetext"]}')
        # codevalue 强制加引号保持字符串语义
        codevalue = item["codevalue"]
        lines.append(f'    codevalue: "{codevalue}"')
        if "ordernumber" in item:
            lines.append(f'    ordernumber: {item["ordernumber"]}')
    return "\n".join(lines) + "\n"


def cli():
    parser = argparse.ArgumentParser(description="新建/修改代码项 yml")

    # 模式 1：新建
    parser.add_argument("--app-root", "--metadata", dest="app_root",
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名，仍可用")
    parser.add_argument("--name", help="代码项名称（中文，作为 yml 内 name 字段，也是文件名）")
    parser.add_argument("--description", default="", help="代码项描述")

    # 模式 2：修改
    parser.add_argument("--file", help="已有代码项 yml 路径（修改时必填）")
    parser.add_argument(
        "--append-items",
        help="向已有 yml 追加子项，格式 text:value:ordernumber 用逗号分隔",
    )

    # items 数据
    parser.add_argument(
        "--items",
        help="子项列表，格式 'text:value:ordernumber,text2:value2'",
    )
    parser.add_argument(
        "--items-json",
        help="子项 JSON 数组（完整字段，支持嵌套 children 等）",
    )
    parser.add_argument(
        "--items-file",
        help="子项 JSON 数组文件路径（与 --items-json 二选一；超长/含中文时用文件避免命令行挂起）",
    )

    parser.add_argument(
        "--single-ext", action="store_true",
        help="使用历史单扩展名 .yml（默认 .codeitem.yml；仅兼容旧项目时使用）",
    )
    parser.add_argument(
        "--force", action="store_true", help="文件已存在时覆盖",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只预览将写入的内容，不落盘（逐资产人工确认用）",
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help="确认落盘。落盘前确认红线：不加 --confirm 一律拒绝写文件，必须先 --dry-run 预览",
    )
    parser.add_argument(
        "--allow-empty", action="store_true",
        help="允许创建空 items 代码项（默认拒绝；SKILL.md 资产信息完整性门禁要求先与用户确认子项）",
    )
    args = parser.parse_args()

    # 解析 items（支持 --items-json / --items-file / --items / --append-items）
    items = []
    try:
        json_items = read_json_param(
            args.items_json, args.items_file,
            expected_type=list, label="--items-json/--items-file",
        )
    except ValueError as e:
        print_err(str(e))
        return 1
    if json_items is not None:
        items = json_items
    elif args.items:
        items = parse_items_str(args.items)
    elif args.append_items:
        items = parse_items_str(args.append_items)

    # 模式判断
    if args.file:
        # 修改模式
        target = Path(args.file).resolve()
        if not target.is_file():
            print_err(f"文件不存在: {target}")
            return 1
        try:
            data = yaml_load(target)
        except Exception as e:
            print_err(f"解析 yml 失败: {e}")
            return 1

        current_type = data.get("type")
        if current_type == "code":
            print_warn("文件 type 是旧版 'code'，现在统一要求 'codeitem'；本脚本仅追加子项，不会自动重写 type，请手动改为 'codeitem'")
        elif current_type != "codeitem":
            print_warn(f"文件 type 不是 'codeitem'，是 '{current_type}'，请确认")

        if items:
            existing_items = data.get("items") or []
            existing_items.extend(items)
            data["items"] = existing_items
            preview = yaml_dump_str(data)
            should_write, code = check_landing(
                dry_run=args.dry_run, confirm=args.confirm,
                target=target, preview=preview, asset_label=f"代码项（追加 {len(items)} 子项）",
            )
            if not should_write:
                return code
            yaml_dump(data, target)
            print_ok(f"已向 {target.name} 追加 {len(items)} 个子项")
        else:
            print_warn("未提供 --items / --items-json / --items-file / --append-items，无操作")
        return 0

    # 新建模式
    if not args.app_root or not args.name:
        print_err("新建模式必须提供 --app-root 和 --name")
        return 1

    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir():
        print_err(f"应用根目录不存在: {app_root}")
        return 1
    ok, msg = assert_no_metadata_layer(app_root)
    if not ok:
        print_err(msg)
        return 1

    codeitem_dir = app_root / "codeitem"

    ext = ".yml" if args.single_ext else ".codeitem.yml"
    target = codeitem_dir / f"{safe_filename(args.name)}{ext}"

    if target.exists() and not args.force:
        print_err(f"文件已存在: {target}（如需覆盖加 --force）")
        return 1

    if not items:
        if not args.allow_empty:
            print_err(
                "未提供 items（--items / --items-json 至少传一种）。\n"
                "SKILL.md 「资产信息完整性门禁」要求：codeitem 必须先与用户确认每个子项的 codetext/codevalue 后再生成。\n"
                "如果确实需要先建空骨架（不推荐），请显式加 --allow-empty。"
            )
            return 1
        print_warn("已显式允许创建空 items 代码项（--allow-empty）")
        items = []

    content = build_codeitem_yaml(args.name, args.description, items)
    should_write, code = check_landing(
        dry_run=args.dry_run, confirm=args.confirm,
        target=target, preview=content, asset_label="代码项",
    )
    if not should_write:
        return code
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print_ok(f"代码项已创建: {target}")
    print_info(f"  - 名称: {args.name}")
    print_info(f"  - 子项数: {len(items)}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
