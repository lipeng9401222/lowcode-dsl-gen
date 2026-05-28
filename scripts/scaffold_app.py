#!/usr/bin/env python3
"""scaffold_app.py — 新建一个低代码应用骨架.

会执行：
1. 计算应用根目录绝对路径（新结构去掉 metadata/ 层）
2. 创建目录（含 7 个子目录：codeitem/mis/module/event/api/workflow/pagedesigne）
3. 渲染并写入 appinfo.lowcode.yml
4. 可选：写入 appref.lowcode.yml
5. 调用 validate_yml.py 自检（appinfo）

新结构：应用根 = `<...>/META-INF/resources/<...>/<apptag>/`，资产直接挂在
应用根下，不再包一层 metadata/。

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
    assert_no_metadata_layer,
    compute_app_root,
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
    app_root = compute_app_root(
        action_root,
        args.apptag,
        developerstag=args.developerstag,
        tenantguid=args.tenantguid,
        baseouguid=args.baseouguid,
        categories=categories,
    )

    print_info(f"目标应用根目录：{app_root}")

    # spec v2 路径红线：新结构下应用根 = <apptag>/，禁止再有 metadata/ 这一层
    ok, msg = assert_no_metadata_layer(app_root)
    if not ok:
        print_err(msg)
        return 1

    # 检测老结构（<apptag>/metadata/）残留
    legacy_metadata = app_root / "metadata"
    if legacy_metadata.is_dir() and not args.force:
        print_err(
            f"检测到老结构残留：{legacy_metadata}/\n"
            f"新结构已去掉 metadata/ 层。请先迁移内部资产到 {app_root}/，再删除 metadata/，\n"
            f"或加 --force 强制在新结构下继续创建（不会动老 metadata/ 目录）。"
        )
        return 1

    # 检测已存在
    appinfo_path = app_root / "appinfo.lowcode.yml"
    if appinfo_path.exists() and not args.force:
        print_err(
            f"appinfo.lowcode.yml 已存在: {appinfo_path}\n"
            f"如需覆盖请加 --force"
        )
        return 1

    # 创建目录骨架
    app_root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (app_root / sub).mkdir(parents=True, exist_ok=True)
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
        appref_path = app_root / "appref.lowcode.yml"
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
    print_info(f"路径: {app_root}")
    print_info("下一步建议:")
    print(f"  - 添加代码项: python add_codeitem.py --app-root {app_root} --name xxx ...")
    print(f"  - 添加数据表: python add_mis_field.py --app-root {app_root} --table xxx --create")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
