#!/usr/bin/env python3
"""validate_plan.py — 审计 .lowcode-plans 计划包的人工确认门禁.

只做计划包静态审计，不生成或修改任何 DSL 资产。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import print_err, print_info, print_ok, print_warn, yaml_load  # noqa: E402


APPROVAL_PATTERN = re.compile(r"(批准创建|按计划生成|可以落盘|批准落盘|确认生成|同意落盘)")
ASSET_ROW_PATTERN = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([a-z-]+)\s*\|\s*([a-z]+)\s*\|")
SUBPLAN_STATUS_PATTERN = re.compile(r"^(?:-\s*)?status:\s*([a-z]+)\s*$", re.MULTILINE)
OPEN_QUESTIONS_BLOCK_PATTERN = re.compile(r"open_questions:\s*\n(?P<body>(?:\s+-.*\n|(?:\s{2,}.*\n))*)")
APPROVED_PENDING_TEXT_PATTERN = re.compile(
    r"(待确认|需确认|待解决|未确认|pending\s+open\s+questions?|open\s+questions?.*pending)",
    re.IGNORECASE,
)
CANONICAL_IR_NAME = "ir.yml"
EXECUTION_STAGE_PATTERN = re.compile(
    r"(dry-run|validated?|validating|generating|generated|landing|landed|executing|executed|"
    r"校验中|校验通过|生成中|已生成|落盘中|已落盘|执行中|已执行)",
    re.IGNORECASE,
)
EXECUTION_RECORD_PATTERN = re.compile(
    r"(dry-run\s*(?:通过|失败|passed|failed)|--dry-run.*(?:通过|失败|passed|failed)|"
    r"validate_ir\.py.*(?:通过|失败|passed|failed)|validate_yml.*(?:通过|失败|passed|failed)|"
    r"check_dsl\.py.*(?:通过|失败|passed|failed)|"
    r"(?:已调用|调用完成|执行完成|已执行)\s*(?:scripts/)?(?:add_[a-z_]+|update_workflow|scaffold_app)\.py)",
    re.IGNORECASE,
)
PLAN_ONLY_PATTERN = re.compile(r"(plan-only|仅生成计划|只生成计划|只做规划|只看规划|先别落盘|不要落盘)")
SUBPLAN_REQUIRED_PATTERNS = (
    ("输入 IR 摘要", re.compile(r"(输入\s*IR\s*摘要|IR\s*摘要|输入IR摘要)", re.IGNORECASE)),
    ("确认项与来源", re.compile(r"(确认项与来源|确认矩阵|来源追踪|来源证据)")),
    ("dry-run 命令和结果", re.compile(r"(dry-run|--dry-run)", re.IGNORECASE)),
    ("生成后校验命令和结果", re.compile(r"(校验命令|校验结果|validate_yml|check_dsl)", re.IGNORECASE)),
)
WORKFLOW_SUBPLAN_REQUIRED_PATTERNS = (
    ("实现效果确认矩阵", re.compile(r"(实现效果确认矩阵|确认矩阵)")),
    ("流程图预览", re.compile(r"(流程图预览|Mermaid|flowchart)", re.IGNORECASE)),
    ("用户纠偏记录", re.compile(r"(用户纠偏记录|纠偏记录|调整记录)")),
    ("活动转换表", re.compile(r"(活动转换表|activity conversion|活动列表)", re.IGNORECASE)),
    ("conditions/contexts/methods/events 摘要", re.compile(r"(conditions|contexts|methods|events|条件|相关数据|外部方法|状态联动)", re.IGNORECASE)),
)


def _normalize_cell(value: str) -> str:
    return value.strip().strip("`").strip()


class PlanValidation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def report(self) -> int:
        for msg in self.errors:
            print_err(msg)
        for msg in self.warnings:
            print_warn(msg)
        if self.errors:
            print_info(f"计划包校验失败：错误 {len(self.errors)}，警告 {len(self.warnings)}")
            return 1
        print_ok(f"计划包校验通过：警告 {len(self.warnings)}")
        return 0


def _read_text(path: Path, result: PlanValidation) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        result.err(f"无法读取计划文件 {path}: {exc}")
        return ""


def _metadata_value(text: str, key: str) -> str:
    match = re.search(rf"^-\s*{re.escape(key)}:\s*(.*)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _has_section(text: str, title: str) -> bool:
    return re.search(rf"^##\s+{re.escape(title)}\s*$", text, re.MULTILINE) is not None


def _extract_main_asset_statuses(text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        match = ASSET_ROW_PATTERN.match(line)
        if not match:
            continue
        asset_id = _normalize_cell(match.group(1))
        status = _normalize_cell(match.group(3))
        if asset_id.lower() in {"asset id", "---"}:
            continue
        statuses[asset_id] = status
    return statuses


def _extract_subplan_status(path: Path, result: PlanValidation) -> str:
    text = _read_text(path, result)
    match = SUBPLAN_STATUS_PATTERN.search(text)
    if match:
        return match.group(1)
    result.err(f"{path} 缺少资产 status")
    return ""


def _validate_subplan_content(path: Path, asset_type: str, result: PlanValidation) -> None:
    text = _read_text(path, result)
    if not text:
        return
    line_count = len([line for line in text.splitlines() if line.strip()])
    if line_count < 24:
        result.err(f"{path} 内容过短，疑似占位子计划；必须写入输入摘要、确认项、dry-run 和校验结果")
    for label, pattern in SUBPLAN_REQUIRED_PATTERNS:
        if not pattern.search(text):
            result.err(f"{path} 缺少子计划必备内容: {label}")
    if asset_type == "workflow":
        for label, pattern in WORKFLOW_SUBPLAN_REQUIRED_PATTERNS:
            if not pattern.search(text):
                result.err(f"{path} 缺少 workflow 子计划必备内容: {label}")


def _extract_ir_path_references(text: str) -> set[str]:
    refs: set[str] = set()
    for match in re.finditer(r"\.lowcode-plans/[^\s`'\"<>]+?\.ya?ml", text):
        refs.add(match.group(0).rstrip(".,;，。；)）]】"))
    return refs


def _approval_status(text: str) -> str:
    return _metadata_value(text, "approval_status")


def _is_plan_only(text: str) -> bool:
    stage = " ".join(
        _metadata_value(text, key)
        for key in ("current_stage", "confirmed_stages", "pending_stages", "next_question")
    )
    return bool(PLAN_ONLY_PATTERN.search(f"{stage}\n{text}"))


def _execution_record_text(text: str) -> str:
    match = re.search(r"^##\s+执行与校验记录\s*$", text, re.MULTILINE)
    if not match:
        return ""
    return text[match.end():]


def _requires_ir(text: str) -> bool:
    if _approval_status(text) == "approved":
        return True
    stage = " ".join(
        _metadata_value(text, key)
        for key in ("current_stage", "confirmed_stages", "pending_stages")
    )
    if EXECUTION_STAGE_PATTERN.search(stage) or EXECUTION_RECORD_PATTERN.search(_execution_record_text(text)):
        return True
    if _is_plan_only(text):
        return False
    return False


def _validate_main_plan(text: str, result: PlanValidation) -> None:
    required_meta = (
        "tool_name",
        "plan_revision",
        "created_at",
        "updated_at",
        "last_interaction_id",
        "current_stage",
        "confirmed_stages",
        "pending_stages",
        "next_question",
        "approval_status",
        "approval_text",
    )
    for key in required_meta:
        if not _metadata_value(text, key):
            result.err(f"主计划缺少元信息: {key}")

    required_sections = (
        "对话确认记录",
        "阶段确认结果",
        "生成计划",
        "执行与校验记录",
    )
    for section in required_sections:
        if not _has_section(text, section):
            result.err(f"主计划缺少章节: {section}")

    approval_status = _metadata_value(text, "approval_status")
    approval_text = _metadata_value(text, "approval_text")
    if approval_status == "approved":
        if not APPROVAL_PATTERN.search(approval_text):
            result.err("approval_status=approved 但 approval_text 没有明确批准落盘语义")
        if "awaiting_user" not in text or "resolved" not in text:
            result.err("approval_status=approved 但对话确认记录缺少 awaiting_user -> resolved 闭环")
        if APPROVED_PENDING_TEXT_PATTERN.search(text):
            result.err("approval_status=approved 但主计划仍包含待确认/open questions/pending 语义")
    elif approval_status != "pending":
        result.err(f"approval_status 非法: {approval_status}")

    for match in OPEN_QUESTIONS_BLOCK_PATTERN.finditer(text):
        if re.search(r"status:\s*pending", match.group("body")):
            if _requires_ir(text):
                result.err("主计划/IR 摘要仍包含 pending open_questions，不能进入生成")


def _validate_ir(ir_path: Path, result: PlanValidation, *, required: bool) -> dict[str, dict[str, str]]:
    if not ir_path.is_file():
        if required:
            result.err(f"缺少 IR 文件: {ir_path}")
        else:
            result.warn(f"规划阶段尚未生成 IR 文件: {ir_path}")
        return {}
    try:
        ir = yaml_load(ir_path)
    except Exception as exc:
        result.err(f"IR 解析失败: {exc}")
        return {}
    if not isinstance(ir, dict):
        result.err("IR 顶层必须是对象")
        return {}
    statuses: dict[str, dict[str, str]] = {}
    for asset in ir.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        asset_id = asset.get("id")
        status = asset.get("status")
        if asset_id:
            statuses[str(asset_id)] = {
                "status": str(status),
                "type": str(asset.get("type") or ""),
            }
    for i, question in enumerate(ir.get("open_questions") or [], start=1):
        if isinstance(question, dict):
            status = question.get("status", "pending")
            if status == "pending":
                if required:
                    result.err(f"ir.yml open_questions[{i}] 仍为 pending，不能进入生成")
            if status == "resolved" and question.get("severity", "blocking") in {"blocking", "confirm"}:
                if not question.get("answer") or "resolvedValue" not in question:
                    result.err(f"ir.yml open_questions[{i}] resolved 但缺少 answer/resolvedValue")
    return statuses


def _validate_status_consistency(
    plan_dir: Path,
    main_statuses: dict[str, str],
    ir_statuses: dict[str, dict[str, str]],
    result: PlanValidation,
    *,
    require_subplans: bool,
) -> None:
    for asset_id, main_status in main_statuses.items():
        ir_status = (ir_statuses.get(asset_id) or {}).get("status")
        if ir_status and ir_status != main_status:
            result.err(f"资产状态不一致: 主计划 {asset_id}={main_status}, ir.yml={ir_status}")

    seen_subplans: set[str] = set()
    declared_asset_ids = set(ir_statuses)
    for subplan in sorted(plan_dir.glob("*/*-plan.md")):
        asset_id = subplan.name.removesuffix("-plan.md")
        if declared_asset_ids and asset_id not in declared_asset_ids:
            result.warn(f"{subplan} 未在 ir.yml assets 中声明，跳过严格子计划审计")
            continue
        seen_subplans.add(asset_id)
        asset_type = subplan.parent.name
        _validate_subplan_content(subplan, asset_type, result)
        sub_status = _extract_subplan_status(subplan, result)
        main_status = main_statuses.get(asset_id)
        ir_status = (ir_statuses.get(asset_id) or {}).get("status")
        if main_status and sub_status and main_status != sub_status:
            result.err(f"资产状态不一致: 主计划 {asset_id}={main_status}, 子计划={sub_status}")
        if ir_status and sub_status and ir_status != sub_status:
            result.err(f"资产状态不一致: ir.yml {asset_id}={ir_status}, 子计划={sub_status}")

    for asset_id, meta in sorted(ir_statuses.items()):
        asset_type = meta.get("type")
        if asset_type not in {"app-shell", "codeitem", "mis", "module", "pagedesigne", "workflow", "event"}:
            continue
        expected = plan_dir / asset_type / f"{asset_id}-plan.md"
        if not expected.is_file():
            if require_subplans:
                result.err(f"缺少资产子计划: {expected}")
            else:
                result.warn(f"规划阶段尚未生成资产子计划: {expected}")
            continue
        if asset_id not in seen_subplans:
            sub_status = _extract_subplan_status(expected, result)
            ir_status = meta.get("status")
            main_status = main_statuses.get(asset_id)
            if main_status and sub_status and main_status != sub_status:
                result.err(f"资产状态不一致: 主计划 {asset_id}={main_status}, 子计划={sub_status}")
            if ir_status and sub_status and ir_status != sub_status:
                result.err(f"资产状态不一致: ir.yml {asset_id}={ir_status}, 子计划={sub_status}")


def _validate_ir_paths(plan_path: Path, plan_dir: Path, text: str, result: PlanValidation) -> Path:
    canonical = plan_dir / CANONICAL_IR_NAME
    legacy = plan_path.parent / f"{plan_dir.name}-ir.yml"
    if legacy.is_file():
        result.err(f"检测到废弃 IR 路径: {legacy}；请迁移为 {canonical}")

    canonical_ref = f".lowcode-plans/{plan_dir.name}/{CANONICAL_IR_NAME}"
    legacy_ref = f".lowcode-plans/{plan_dir.name}-ir.yml"
    for ref in _extract_ir_path_references(text):
        if ref == legacy_ref:
            result.err(f"主计划引用废弃 IR 路径: {ref}；必须改为 {canonical_ref}")
        elif ref.endswith("-ir.yml"):
            result.err(f"主计划引用疑似废弃 IR 路径: {ref}；必须使用 {canonical_ref}")
        elif ref.endswith("/ir.yml") and ref != canonical_ref:
            result.warn(f"主计划引用的 IR 路径不是当前应用 canonical 路径: {ref}")
    return canonical


def validate_plan(plan_path: Path) -> int:
    result = PlanValidation()
    plan_path = plan_path.resolve()
    if not plan_path.is_file():
        result.err(f"主计划文件不存在: {plan_path}")
        return result.report()

    text = _read_text(plan_path, result)
    if text:
        _validate_main_plan(text, result)

    apptag = plan_path.name.removesuffix("-plan.md")
    plan_dir = plan_path.parent / apptag
    if not plan_dir.is_dir():
        result.err(f"缺少计划分区目录: {plan_dir}")
        return result.report()

    ir_path = _validate_ir_paths(plan_path, plan_dir, text, result)
    main_statuses = _extract_main_asset_statuses(text)
    requires_ir = _requires_ir(text)
    ir_statuses = _validate_ir(ir_path, result, required=requires_ir)
    if ir_statuses:
        _validate_status_consistency(
            plan_dir,
            main_statuses,
            ir_statuses,
            result,
            require_subplans=requires_ir,
        )
    return result.report()


def cli() -> int:
    parser = argparse.ArgumentParser(description="校验 lowcode-dsl-gen .lowcode-plans 主计划")
    parser.add_argument("plan", help=".lowcode-plans/<apptag>-plan.md")
    args = parser.parse_args()
    return validate_plan(Path(args.plan))


if __name__ == "__main__":
    sys.exit(cli())
