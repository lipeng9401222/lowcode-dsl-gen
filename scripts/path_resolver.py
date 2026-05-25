#!/usr/bin/env python3
"""path_resolver.py — 给定 apptag 或路径，定位/计算应用根目录绝对路径.

新结构：应用根目录 = `<...>/META-INF/resources/<...>/<apptag>/`，
应用资产（codeitem/mis/module/event/workflow/pagedesigne/api）直接挂在
应用根下，**不再有 metadata/ 这一层**。老结构 `<apptag>/metadata/` 仅作向后兼容读取。

用法：
    # 1) 基于 apptag 在 workspace 中查找已存在的应用根目录
    python path_resolver.py --apptag xmlx --workspace /path/to/epoint-ipd-parent

    # 2) 计算新应用的应用根路径（不一定存在）
    python path_resolver.py --apptag purchaseproject \\
        --action-root /path/to/xxx-action \\
        --developerstag epoint \\
        --categories trade,tradeprocess

    # 仅用户明确要求独立单位时才加 --baseouguid epoint

    # 3) 仅打印工程根/action 子工程根
    python path_resolver.py --find-action-root /any/path/inside/project
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接 python path_resolver.py 调用
sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    compute_app_root,
    find_action_root,
    find_existing_apptag,
    find_workspace_root,
    is_valid_apptag,
    print_err,
    print_info,
    print_ok,
)


def cli():
    parser = argparse.ArgumentParser(description="解析/计算应用根目录路径（新结构去掉 metadata/ 层）")
    parser.add_argument("--apptag", help="应用标识")
    parser.add_argument("--workspace", help="工作区根目录（默认从 cwd 向上找 .git 根）")
    parser.add_argument(
        "--action-root",
        help="action 子工程绝对路径（含 src/main/resources/META-INF/resources）",
    )
    parser.add_argument("--developerstag", default="epoint", help="开发商标识 [epoint]")
    parser.add_argument("--tenantguid", default="", help="租户标识 [空]")
    parser.add_argument("--baseouguid", default="", help="独立单位标识 [空；需要时显式传入]")
    parser.add_argument(
        "--categories",
        default="",
        help="应用分类（多层用逗号分隔，如 trade,tradeprocess）",
    )
    parser.add_argument(
        "--find-action-root",
        help="给定路径，向上查找最近的 action 子工程根并打印",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "find", "compute"],
        default="auto",
        help="auto: 自动判断（apptag 可在 workspace 找到则 find，否则 compute）",
    )
    args = parser.parse_args()

    # 模式 0：仅查找 action root
    if args.find_action_root:
        action_root = find_action_root(Path(args.find_action_root))
        if action_root:
            print(action_root)
            return 0
        print_err(f"未找到 action 子工程根：{args.find_action_root}")
        return 1

    if not args.apptag:
        parser.error("--apptag 必填（除非用 --find-action-root）")

    if not is_valid_apptag(args.apptag):
        print_err(f"apptag 不合法: {args.apptag}（应为小写字母开头 + 字母/数字）")
        return 1

    workspace = Path(args.workspace) if args.workspace else find_workspace_root(Path.cwd())
    if not workspace:
        print_err("找不到工作区根目录，请指定 --workspace")
        return 1
    workspace = workspace.resolve()

    # 优先尝试在 workspace 中查找已存在的 apptag
    if args.mode in ("auto", "find"):
        existing = find_existing_apptag(workspace, args.apptag)
        if existing:
            print_ok(f"在 workspace 中找到已存在的应用：{args.apptag}")
            print(existing)
            return 0
        if args.mode == "find":
            print_err(f"未找到 apptag={args.apptag} 的现有应用根目录")
            return 1

    # 计算新路径
    if not args.action_root:
        # 尝试从 workspace 推断单一 action 子工程
        candidates = list(workspace.glob("*/src/main/resources/META-INF/resources"))
        candidates = [c.parents[4] for c in candidates if c.is_dir()]  # action_root
        if len(candidates) == 1:
            action_root = candidates[0]
            print_info(f"自动推断 action 子工程：{action_root.name}")
        elif len(candidates) > 1:
            print_err(
                f"workspace 内有多个 action 子工程，请用 --action-root 指定：\n  "
                + "\n  ".join(str(c) for c in candidates)
            )
            return 1
        else:
            print_err("未找到任何 action 子工程，请用 --action-root 指定")
            return 1
    else:
        action_root = Path(args.action_root).resolve()

    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    app_root = compute_app_root(
        action_root,
        args.apptag,
        developerstag=args.developerstag,
        tenantguid=args.tenantguid,
        baseouguid=args.baseouguid,
        categories=categories,
    )
    exists = app_root.is_dir()
    print_info(f"计算路径（{'已存在' if exists else '不存在'}）：")
    print(app_root)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
