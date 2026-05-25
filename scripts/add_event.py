#!/usr/bin/env python3
"""add_event.py — 创建一个标准三段式动作流 yml 骨架.

⚠️ 边界提示：标准 CRUD（list / detail / save / delete）不要走此脚本！
   - 列表 / 详情 / 新增 / 修改 / 删除 → 走 MIS 接口或 REST 接口标准方法

✅ 当前阶段 skill 默认只把"状态变更联动"作为主动建议生成 event 的场景：
   - 状态变更联动（dispatch / approve / reject / archive / cancel / submit / revoke，
     需同时改状态位、写日志、发消息）

🟡 以下属于"高级场景"，仅当用户明确表达诉求时才考虑生成 event，不要主动建议：
   - 跨系统推送拉取（push / pull / notify / sync）
   - 定时同步（Cron）
   - 工作流回调（method.ruleguid / workflowEvent.ruleGuid 引用）
   - 多节点编排（含条件、迭代、代码节点）

骨架包含 6 个节点：Webhook触发 → 初始化上下文 → 接口鉴权 → 业务方法 → 构建结果集 → 结束.

用法：
    python add_event.py \\
        --app-root /path/to/.../<apptag> \\
        --name "调度车辆" \\
        --sign dispatch \\
        --apptag carapply \\
        --biz-action CarApplyRestService_dispatch \\
        --biz-title "调度车辆并更新状态" \\
        --context-class com.epoint.ycsq.context.CarApplyContext \\
        --webhook-url "http://localhost:8080/EpointFrame/rest/dynamicapi/dispatch"

兼容：--metadata 旧参数仍可用，等价于 --app-root（输出 deprecation warn）。
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
    print_warn,
    render_template,
    safe_filename,
)


def cli():
    parser = argparse.ArgumentParser(description="创建标准三段式动作流 yml")
    parser.add_argument("--app-root", "--metadata", dest="app_root", required=True,
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名")
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

    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir():
        print_err(f"应用根目录不存在: {app_root}")
        return 1

    event_dir = app_root / "event"
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
