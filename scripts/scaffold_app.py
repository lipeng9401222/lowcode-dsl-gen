#!/usr/bin/env python3
"""scaffold_app.py — 新建一个低代码应用骨架.

会执行：
1. 计算 metadata 目录绝对路径
2. 创建目录（含 7 个子目录：codeitem/mis/module/event/api/workflow/pagedesigne）
3. 渲染并写入 appinfo.lowcode.yml
4. 可选：写入 appref.lowcode.yml
5. 调用 validate_yml.py 自检（appinfo）

用法：
    python scaffold_app.py \\
        --apptag purchaseproject \\
        --name "采购立项" \\
        --action-root /path/to/xxx-action \\
        --kitid businessprocess

    # 仅用户明确要求独立单位时才传：
    #   --baseouguid epoint
"""
from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    compute_metadata_path,
    is_valid_apptag,
    load_template,
    print_err,
    print_info,
    print_ok,
    print_warn,
    render_template,
)


SUBDIRS = [
    "codeitem",
    "mis",
    "module",
    "event",
    "api",
    "workflow",
    "pagedesigne",
]


def cli():
    parser = argparse.ArgumentParser(description="新建低代码应用骨架")
    parser.add_argument("--apptag", required=True, help="应用标识（小写英文+数字）")
    parser.add_argument("--name", required=True, help="应用名称（中文）")
    parser.add_argument(
        "--action-root", required=True,
        help="action 子工程绝对路径（含 src/main/resources/META-INF/resources）",
    )
    parser.add_argument("--developerstag", default="epoint", help="开发商 [epoint]")
    parser.add_argument("--kitid", default="businessprocess", help="套件标识 [businessprocess]")
    parser.add_argument("--baseouguid", default="", help="独立单位 [空；需要时显式传入]")
    parser.add_argument("--tenantguid", default="", help="租户标识 [空]")
    parser.add_argument(
        "--categories", default="",
        help="应用分类目录（多层用 / 分隔，如 trade/tradeprocess）",
    )
    parser.add_argument(
        "--with-appref", action="store_true",
        help="同时创建 appref.lowcode.yml（默认不创建）",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="目标目录已存在时仍继续（覆盖 appinfo.lowcode.yml 需要 --force）",
    )
    parser.add_argument(
        "--no-validate", action="store_true",
        help="跳过 validate_yml.py 自检",
    )
    args = parser.parse_args()

    # 校验 apptag
    if not is_valid_apptag(args.apptag):
        print_err(f"apptag 不合法: {args.apptag}（应为小写字母开头 + 字母/数字）")
        return 1

    action_root = Path(args.action_root).resolve()
    if not action_root.is_dir():
        print_err(f"action 子工程目录不存在: {action_root}")
        return 1

    categories = [c.strip() for c in args.categories.split("/") if c.strip()]
    metadata_path = compute_metadata_path(
        action_root,
        args.apptag,
        developerstag=args.developerstag,
        tenantguid=args.tenantguid,
        baseouguid=args.baseouguid,
        categories=categories,
    )

    print_info(f"目标 metadata 目录：{metadata_path}")

    # 检测已存在
    appinfo_path = metadata_path / "appinfo.lowcode.yml"
    if appinfo_path.exists() and not args.force:
        print_err(
            f"appinfo.lowcode.yml 已存在: {appinfo_path}\n"
            f"如需覆盖请加 --force"
        )
        return 1

    # 创建目录骨架
    metadata_path.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (metadata_path / sub).mkdir(parents=True, exist_ok=True)
    print_ok(f"目录骨架已创建（含 {len(SUBDIRS)} 个子目录）")

    # 渲染 appinfo.lowcode.yml
    template = load_template("appinfo.lowcode.yml")
    rendered = render_template(template, {
        "DEVELOPERSTAG": args.developerstag,
        "APPLICATIONNAME": args.name,
        "APPTAG": args.apptag,
        "KITID": args.kitid,
        "BASEOUGUID": args.baseouguid,
    })
    appinfo_path.write_text(rendered, encoding="utf-8")
    print_ok(f"已写入: {appinfo_path}")

    # 渲染 appref.lowcode.yml（可选）
    if args.with_appref:
        appref_path = metadata_path / "appref.lowcode.yml"
        if appref_path.exists() and not args.force:
            print_warn(f"appref.lowcode.yml 已存在，跳过（需要 --force 覆盖）")
        else:
            # 默认空内容
            appref_path.write_text(
                "# 引用其他应用的组件实例\n"
                "# 每项必须包含 engineguid 和 name\n"
                "# engineguid 取值: codeitem / mis / module / workflow / event / pagedesigne\n"
                "# 示例:\n"
                "# - engineguid: codeitem\n"
                "#   name: [行政区划, 审核状态]\n"
                "#   sourceAppTag: common\n",
                encoding="utf-8",
            )
            print_ok(f"已写入: {appref_path}")

    # 自检
    if not args.no_validate:
        validate_script = Path(__file__).parent / "validate_yml.py"
        if validate_script.is_file():
            print_info("正在执行 validate_yml.py 自检...")
            result = subprocess.run(
                [sys.executable, str(validate_script), str(appinfo_path)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print_ok("校验通过")
            else:
                print_warn("校验有警告或错误：")
                print(result.stdout)
                print(result.stderr, file=sys.stderr)

    print()
    print_ok("应用骨架创建完成")
    print_info(f"路径: {metadata_path}")
    print_info("下一步建议:")
    print(f"  - 添加代码项: python add_codeitem.py --metadata {metadata_path} --name xxx ...")
    print(f"  - 添加数据表: python add_mis_field.py --metadata {metadata_path} --table xxx --create")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
