#!/usr/bin/env python3
"""Regression checks for validate_plan.py staged IR behavior."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from validate_plan import validate_plan


def _main_plan(
    *,
    apptag: str = "demo",
    approval_status: str = "pending",
    approval_text: str = "未批准",
    current_stage: str = "规划",
    open_questions: str = "",
    asset_rows: str = "",
    execution_record: str = "尚未进入 dry-run。",
) -> str:
    return f"""# {apptag} 计划

- tool_name: lowcode-dsl-gen
- plan_revision: 1
- created_at: 2026-06-11T00:00:00+08:00
- updated_at: 2026-06-11T00:00:00+08:00
- last_interaction_id: i-001
- current_stage: {current_stage}
- confirmed_stages: none
- pending_stages: planning
- next_question: 继续确认
- approval_status: {approval_status}
- approval_text: {approval_text}

## 对话确认记录

- q-001 status: awaiting_user
- q-001 status: resolved

## 阶段确认结果

{open_questions}

## 生成计划

| asset id | type | status |
|---|---|---|
{asset_rows}

## 执行与校验记录

{execution_record}
"""


def _workflow_subplan() -> str:
    lines = [
        "# workflow 子计划",
        "status: pending",
        "## 输入 IR 摘要",
        "asset-workflow-001 workflow 摘要。",
        "## 确认项与来源",
        "实现效果确认矩阵：流程目标、节点链路、处理人、表单、MIS 均已确认。",
        "## 流程图预览",
        "Mermaid flowchart: 申请 --> 审批。",
        "## 用户纠偏记录",
        "无纠偏。",
        "## 活动转换表",
        "活动列表：申请、直接领导审批。",
        "## conditions/contexts/methods/events 摘要",
        "conditions: []",
        "contexts: []",
        "methods: []",
        "events: []",
        "## dry-run 命令和结果",
        "python3 scripts/add_workflow.py --from-ir .lowcode-plans/demo/ir.yml --asset-id asset-workflow-001 --dry-run",
        "dry-run 通过。",
        "## 生成后校验命令和结果",
        "python3 scripts/validate_yml.py <file>",
        "校验结果：待落盘后执行。",
    ]
    lines.extend(f"补充说明 {i}" for i in range(1, 8))
    return "\n".join(lines) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _case_pending_missing_ir(root: Path) -> int:
    base = root / "pending" / ".lowcode-plans"
    (base / "demo").mkdir(parents=True)
    _write(
        base / "demo-plan.md",
        _main_plan(
            open_questions="""open_questions:
  - id: q-001
    status: pending
""",
        ),
    )
    return validate_plan(base / "demo-plan.md")


def _case_plan_only_missing_ir(root: Path) -> int:
    base = root / "plan-only" / ".lowcode-plans"
    (base / "demo").mkdir(parents=True)
    _write(
        base / "demo-plan.md",
        _main_plan(
            current_stage="plan-only",
            approval_text="先别落盘，只做规划",
        ),
    )
    return validate_plan(base / "demo-plan.md")


def _case_approved_missing_ir(root: Path) -> int:
    base = root / "approved" / ".lowcode-plans"
    (base / "demo").mkdir(parents=True)
    _write(
        base / "demo-plan.md",
        _main_plan(
            approval_status="approved",
            approval_text="按计划生成",
            current_stage="待落盘",
            execution_record="尚未执行。",
        ),
    )
    return validate_plan(base / "demo-plan.md")


def _case_dry_run_workflow_with_ir(root: Path) -> int:
    base = root / "dry-run" / ".lowcode-plans"
    plan_dir = base / "demo"
    _write(
        base / "demo-plan.md",
        _main_plan(
            current_stage="dry-run",
            asset_rows="| asset-workflow-001 | workflow | pending |",
            execution_record="dry-run 通过。",
        ),
    )
    _write(
        plan_dir / "ir.yml",
        """version: "1.0"
application:
  apptag: "demo"
  applicationname: "演示应用"
assets:
  - id: "asset-workflow-001"
    type: "workflow"
    status: "pending"
    dependencies: []
    spec: {}
    errors: []
open_questions: []
validation:
  status: "pending"
  reports: []
""",
    )
    _write(plan_dir / "workflow" / "asset-workflow-001-plan.md", _workflow_subplan())
    return validate_plan(base / "demo-plan.md")


def _mis_subplan() -> str:
    lines = [
        "# mis 子计划",
        "status: pending",
        "## 输入 IR 摘要",
        "asset-mis-001 mis 表 blueprintinfo 摘要。",
        "## 确认项与来源",
        "字段、类型、长度、必填均已 user_confirmed；来源证据见对话 i-001。",
        "## dry-run 命令和结果",
        "python3 scripts/add_mis_field.py --app-root <app> --table blueprintinfo --create --dry-run",
        "dry-run 通过。",
        "## 生成后校验命令和结果",
        "python3 scripts/validate_yml.py <file>",
        "校验结果：待落盘后执行。",
    ]
    lines.extend(f"补充说明 {i}" for i in range(1, 14))
    return "\n".join(lines) + "\n"


def _case_approved_no_ir_with_subplan(root: Path) -> int:
    """approved 且无 ir.yml，但主计划有资产队列 + 完整子计划：应通过（IR 可选）。"""
    base = root / "approved-no-ir" / ".lowcode-plans"
    plan_dir = base / "demo"
    _write(
        base / "demo-plan.md",
        _main_plan(
            approval_status="approved",
            approval_text="按计划生成",
            current_stage="待落盘",
            asset_rows="| asset-mis-001 | mis | pending |",
            execution_record="尚未执行。",
        ),
    )
    _write(plan_dir / "mis" / "asset-mis-001-plan.md", _mis_subplan())
    return validate_plan(base / "demo-plan.md")


def main() -> int:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = {
            "pending_missing_ir": (_case_pending_missing_ir(root), 0),
            "plan_only_missing_ir": (_case_plan_only_missing_ir(root), 0),
            "approved_missing_ir": (_case_approved_missing_ir(root), 1),
            "approved_no_ir_with_subplan": (_case_approved_no_ir_with_subplan(root), 0),
            "dry_run_workflow_with_ir": (_case_dry_run_workflow_with_ir(root), 0),
        }

    failed: list[str] = []
    for name, (actual, expected) in cases.items():
        ok = (actual == 0) if expected == 0 else (actual != 0)
        if not ok:
            failed.append(f"{name}: expected {'pass' if expected == 0 else 'fail'}, got {actual}")

    if failed:
        print("validate_plan regression failed:")
        for item in failed:
            print(f"- {item}")
        return 1
    print("validate_plan regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
