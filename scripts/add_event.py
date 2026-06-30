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

兼容：--metadata 旧参数仍可用，等价于 --app-root（输出 deprecation warn）。--from-ir 仍可用，
但默认建议直接传 CLI 参数。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ir_to_event_args import event_args_from_ir  # noqa: E402
from _common import (  # noqa: E402
    assert_no_metadata_layer,
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
    parser.add_argument("--from-ir", help="兼容：从 lowcode-dsl-gen IR 文件读取 event spec")
    parser.add_argument("--asset-id", help="兼容：IR 中 event asset id；多个 event 时必填")
    parser.add_argument("--dry-run", action="store_true", help="只校验/打印参数，不创建目录、不写文件")
    parser.add_argument("--confirm", action="store_true",
                        help="确认落盘。不加 --confirm 一律拒绝写文件，必须先 --dry-run 预览（落盘前确认红线）")
    parser.add_argument("--app-root", "--metadata", dest="app_root",
                        help="应用根目录路径（<apptag>/）。--metadata 是旧别名")
    parser.add_argument("--name", help="动作流名称（中文）")
    parser.add_argument("--sign", help="接口标识（与 controller 方法名一致）")
    parser.add_argument("--apptag", help="应用标识")
    parser.add_argument(
        "--biz-action",
        help="业务方法 action 标识（如 PurchaseProjectListRestService_getDataGridModel）",
    )
    parser.add_argument(
        "--biz-title", default="业务执行",
        help="业务节点标题 [业务执行]",
    )
    parser.add_argument(
        "--context-class",
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

    if args.from_ir:
        ir_path = Path(args.from_ir).resolve()
        if ir_path.parent.name == ".lowcode-plans" and ir_path.name.endswith("-ir.yml"):
            print_err(
                "IR 文件路径已废弃：请使用 .lowcode-plans/<apptag>/ir.yml，"
                f"当前是 {ir_path}"
            )
            return 1
        try:
            from _common import yaml_load  # noqa: E402
            converted = event_args_from_ir(yaml_load(ir_path), args.asset_id)
        except Exception as e:
            print_err(f"--from-ir 解析失败: {e}")
            return 1
        for key, value in converted.items():
            if value not in (None, ""):
                setattr(args, key, value)

    for field in ("app_root", "name", "sign", "apptag", "biz_action", "context_class"):
        if not getattr(args, field, None):
            print_err(f"--{field.replace('_', '-')} 必填（或通过 --from-ir 提供）")
            return 1

    if "--metadata" in sys.argv:
        print_warn("--metadata 已废弃，建议改用 --app-root（功能相同，下版本将移除）")

    app_root = Path(args.app_root).resolve()
    if not app_root.is_dir() and not args.dry_run:
        print_err(f"应用根目录不存在: {app_root}")
        return 1
    if not app_root.is_dir() and args.dry_run:
        print_warn(f"应用根目录暂不存在，dry-run 仅校验参数与目标路径: {app_root}")
    ok, msg = assert_no_metadata_layer(app_root)
    if not ok:
        print_err(msg)
        return 1

    event_dir = app_root / "event"

    # 文件名
    base_name = args.filename or safe_filename(args.sign)
    ext = ".yml" if args.single_ext else ".event.yml"
    target = event_dir / f"{base_name}{ext}"

    if target.exists() and not args.force and not args.dry_run:
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

    # 加载模板并渲染
    template = load_template("event.yml")
    rendered = render_template(template, {
        "EVENT_NAME": args.name,
        "EVENT_SIGN": args.sign,
        "EVENT_ID": event_id,
        "CREATED_AT": now_unix(),
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

    if args.dry_run:
        print_ok(f"event dry-run 通过: {target}")
    elif not args.confirm:
        print_err(
            "拒绝落盘：动作流必须经人工预览确认后才能写入。\n"
            "请先用 --dry-run 预览，确认无误后再加 --confirm 落盘。\n"
            "（落盘前确认红线：禁止未经 dry-run 预览 + --confirm 确认直接写文件）"
        )
        return 1
    else:
        event_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        print_ok(f"动作流已创建: {target}")
    print_info(f"  - 名称: {args.name}")
    print_info(f"  - 接口标识 sign: {args.sign}")
    print_info(f"  - 业务方法: {args.biz_action}")
    print_info(f"  - 节点 ID 列表: {node_ids}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
