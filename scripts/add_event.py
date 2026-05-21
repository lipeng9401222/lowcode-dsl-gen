#!/usr/bin/env python3
"""add_event.py — 创建一个标准三段式动作流 yml 骨架.

骨架包含 6 个节点：Webhook触发 → 初始化上下文 → 接口鉴权 → 业务方法 → 构建结果集 → 结束.

用法：
    python add_event.py \\
        --metadata /path/to/.../metadata \\
        --name "获取采购立项列表" \\
        --sign getDataGridModel \\
        --apptag purchaseproject \\
        --biz-action PurchaseProjectListRestService_getDataGridModel \\
        --biz-title "获取列表分页数据" \\
        --context-class com.epoint.ztb.rest.qy.tradeplan.purchaseproject.context.PurchaseProjectContext \\
        --webhook-url "http://localhost:8080/EpointFrame/rest/dynamicapi/getDataGridModel"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    gen_node_ids,
    gen_uuid,
    load_template,
    now_unix,
    print_err,
    print_info,
    print_ok,
    render_template,
    safe_filename,
)


def cli():
    parser = argparse.ArgumentParser(description="创建标准三段式动作流 yml")
    parser.add_argument("--metadata", required=True, help="metadata 目录路径")
    parser.add_argument("--name", required=True, help="动作流名称（中文）")
    parser.add_argument("--sign", required=True, help="接口标识（与 controller 方法名一致）")
    parser.add_argument("--apptag", required=True, help="应用标识")
    parser.add_argument(
        "--biz-action", required=True,
        help="业务方法 action 标识（如 PurchaseProjectListRestService_getDataGridModel）",
    )
    parser.add_argument(
        "--biz-title", default="业务执行",
        help="业务节点标题 [业务执行]",
    )
    parser.add_argument(
        "--context-class", required=True,
        help="上下文 Java 类全限定名（如 com.epoint.xxx.PurchaseProjectContext）",
    )
    parser.add_argument(
        "--webhook-url",
        help="Webhook URL [默认: http://localhost:8080/EpointFrame/rest/dynamicapi/<sign>]",
    )
    parser.add_argument(
        "--single-ext", action="store_true",
        help="使用历史单扩展名 .yml（默认 .event.yml；仅兼容旧项目时使用）",
    )
    parser.add_argument("--filename", help="自定义文件名（不含扩展名），默认基于 sign")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    metadata_dir = Path(args.metadata).resolve()
    if not metadata_dir.is_dir():
        print_err(f"metadata 目录不存在: {metadata_dir}")
        return 1

    event_dir = metadata_dir / "event"
    event_dir.mkdir(parents=True, exist_ok=True)

    # 文件名
    base_name = args.filename or safe_filename(args.sign)
    ext = ".yml" if args.single_ext else ".event.yml"
    target = event_dir / f"{base_name}{ext}"

    if target.exists() and not args.force:
        print_err(f"文件已存在: {target}（--force 覆盖）")
        return 1

    # webhook URL
    webhook_url = args.webhook_url or f"http://localhost:8080/EpointFrame/rest/dynamicapi/{args.sign}"

    # 生成 ID
    event_id = gen_uuid()
    node_ids = gen_node_ids(6)
    formula_value_id = gen_uuid()
    formula_result_id = gen_uuid()
    formula_end_id = gen_uuid()

    # event_code = name 全小写 + 去特殊字符
    event_code = re.sub(r"[^a-z0-9]+", "", args.sign.lower())

    # 加载模板并渲染
    template = load_template("event.yml")
    rendered = render_template(template, {
        "EVENT_NAME": args.name,
        "EVENT_SIGN": args.sign,
        "EVENT_ID": event_id,
        "CREATED_AT": now_unix(),
        "EVENT_CODE": event_code,
        "WEBHOOK_URL": webhook_url,
        "APPTAG": args.apptag,
        "CONTEXT_CLASS": args.context_class,
        "BIZ_ACTION_NAME": args.biz_action,
        "BIZ_TITLE": args.biz_title,
        "NODE_START_ID": node_ids[0],
        "NODE_INIT_ID": node_ids[1],
        "NODE_AUTH_ID": node_ids[2],
        "NODE_BIZ_ID": node_ids[3],
        "NODE_RESULT_ID": node_ids[4],
        "NODE_END_ID": node_ids[5],
        "FORMULA_VALUE_ID": formula_value_id,
        "FORMULA_RESULT_ID": formula_result_id,
        "FORMULA_END_ID": formula_end_id,
    })

    target.write_text(rendered, encoding="utf-8")
    print_ok(f"动作流已创建: {target}")
    print_info(f"  - 名称: {args.name}")
    print_info(f"  - 接口标识 sign: {args.sign}")
    print_info(f"  - 业务方法: {args.biz_action}")
    print_info(f"  - 节点 ID 列表: {node_ids}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
