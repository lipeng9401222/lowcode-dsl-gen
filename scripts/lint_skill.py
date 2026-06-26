#!/usr/bin/env python3
"""lint_skill.py — skill 仓库自检看门人.

防止 skill 仓库自身退化到老结构：
1. 不允许 references / assets/templates / scripts 出现已废弃驼峰键（spec v2）
2. 不允许 references / assets/templates 出现 `tableid` / `fromMisTableId` / `fromFieldId`
3. 不允许 references / assets/templates 出现 `<apptag>/metadata/<asset>` 这种老结构示例
4. 不允许 skill 仓库根直接出现"应用产物目录"（如 ipdmanage/ / xmlx/）或上次会话计划文档（*-plan.md）
5. 要求 SKILL.md 与生成计划模板保留计划追溯关键字段（问题 / 选项 / 用户回复 / 确认结果）
6. 不允许 workflow 正例/知识库重新引入旧结构：workflowVersion 数组、versionnum、formid、
   workflowMethodParameter、workflowPvMisTableSet.rowguid 等

用法：
    python scripts/lint_skill.py        # 在 skill 仓库根运行
    python scripts/lint_skill.py --skill-root /path/to/lowcode-dsl-gen

退出码：0 通过；1 有违规；2 警告（默认非阻断，--strict 模式升级为 1）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# 已废弃的驼峰键名（spec v2 要求全小写下划线）。
# 这里只列"高频且最可能误用"的；validate_yml.py 的 DEPRECATED_CAMEL 是更全的清单。
FORBIDDEN_CAMEL = [
    "isDefault",
    "isPassWhenNoTransactor",
    "isLockWhenMultiTransactor",
    "mobileHandleType",
    "isAllowAddAttachFile",
    "multiTransctorMode",
    "subProMultiTransctorMode",
    "subProcessSyncType",
    "callSubProcessGuid",
    "targetActivityTransactorSource",
    "isTargetTransactorEditable",
    "isShowAsOperationButton",
    "stateLevel",
    "isShowOpinionTemplete",
    "is_ShowOpinionTemplete",
    "isShowLineGraph",
    "isShowNodeSimple",
    "revokeOption",
    "revokeAllowDay",
    "revokeRemindOption",
    "noParticipatorOption",
    "defaultUserGuid",
    "fromMisTableId",
    "fromFieldId",
]

# 已废弃字段名（spec v2 移除）
FORBIDDEN_FIELDS = [
    "tableid",  # workflowPvMisTableSet.tableid 已废弃
]

FORBIDDEN_WORKFLOW_TERMS = [
    "workflowMethodParameter",
    "versionnum",
    "isactive",
    "formid",
    "formId",
    "materialtype",
]

# 老结构路径片段
LEGACY_METADATA_PATTERNS = [
    r"<apptag>/metadata/<asset>",
    r"<apptag>/metadata/[a-z_]+",
    r"/metadata/<asset>",
]

# skill 仓库根禁止出现的"应用产物 / 上次会话产物"
DISALLOWED_APP_DIRS = ["ipdmanage", "xmlx", "purchaseproject"]

# 计划文档追溯契约：这些词必须出现在核心规范和标准模板里，防止后续改动把审计台账退化成
# 只有最终方案、没有问答过程的普通计划。
REQUIRED_AUDIT_CONTRACT = {
    "SKILL.md": [
        "plan_revision",
        "last_interaction_id",
        "对话确认记录",
        "阶段确认结果",
        "生成计划",
        "执行与校验记录",
        "问题、选项、用户回复和确认结果",
    ],
    "references/workflow/工作流/生成与校验/04-生成计划.md": [
        "plan_revision",
        "last_interaction_id",
        "对话确认记录",
        "阶段确认结果",
        "生成计划",
        "执行与校验记录",
        "user_reply",
        "parsed_result",
        "stage_effect",
    ],
}


def _is_skill_doc_or_template(path: Path, skill_root: Path) -> bool:
    """是否属于"应当遵守 spec v2"的 skill 资产文件。

    references/**/*.md / assets/templates/* / scripts/*.py 都算。
    SKILL.md / README.md 顶层文档也算。
    skill 仓库根直下的 *.md / *.yml 也算（如临时插入的示例不应包含已废弃字段）。
    规范文件本身（Epoint 工作流 YAML 定义规范*.md）跳过 — 它就是 spec 源文件。
    """
    rel = path.relative_to(skill_root)
    name = path.name
    if name.startswith("Epoint工作流YAML定义规范"):
        return False
    parts = rel.parts
    if parts[0] in ("references", "assets", "scripts"):
        return path.suffix.lower() in (".md", ".yml", ".yaml", ".py", ".json")
    if parts[0] == "evals":
        return path.suffix.lower() in (".md", ".yml", ".yaml", ".json")
    if len(parts) == 1 and path.suffix.lower() in (".md", ".yml", ".yaml"):
        return True  # 仓库根直下的文档
    return False


def _is_negative_fixture(path: Path) -> bool:
    lower = path.name.lower()
    return "bad" in lower or "invalid" in lower or "legacy" in lower


def _is_workflow_hardening_scope(path: Path, skill_root: Path) -> bool:
    """是否属于 workflow 防幻觉规则需要扫描的正例知识库范围。"""
    rel = path.relative_to(skill_root)
    parts = rel.parts
    if rel.as_posix() in {"SKILL.md", "docs/SKILL-DESIGN.md"}:
        return True
    if len(parts) >= 2 and parts[0] == "references" and parts[1] == "workflow":
        return True
    if len(parts) >= 3 and parts[0] == "assets" and parts[1] == "templates":
        return "workflow" in path.name.lower()
    if len(parts) >= 2 and parts[0] == "evals":
        return "workflow" in path.name.lower()
    if len(parts) == 1 and path.suffix.lower() in (".yml", ".yaml"):
        return "workflow" in path.name.lower()
    return False


def _check_forbidden_terms(skill_root: Path) -> list[tuple[Path, int, str, str]]:
    """扫描 skill 资产文件，返回 (file, line, term, category) 命中清单。

    白名单：
    - DEPRECATED_CAMEL / FORBIDDEN_CAMEL / 老结构示例引用 — 这些是"用来报错/指引迁移"的字面量，
      允许出现在 validate_yml.py / lint_skill.py 自身、以及标题为"已废弃 / DEPRECATED / 红线 / 迁移"的文档段。
    """
    SELF_NAMES = {"validate_yml.py", "lint_skill.py", "field_schema.py"}
    hits: list[tuple[Path, int, str, str]] = []
    for path in skill_root.rglob("*"):
        if not path.is_file():
            continue
        if not _is_skill_doc_or_template(path, skill_root):
            continue
        if path.name in SELF_NAMES:
            continue  # 校验器自身允许枚举废弃字段名
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            # 老结构 / 已废弃字段允许出现在以下"白名单段"
            #   - 行内含"已废弃" / "deprecated" / "红线" / "迁移" / "DEPRECATED_CAMEL"
            #   - 行内是 markdown 表格的"老 → 新"映射
            #   - 行内描述校验规则（含 "warn" / "error" / "驼峰" / "命中" 等关键词）
            wl_keywords = ("已废弃", "deprecated", "DEPRECATED",
                           "红线", "迁移", "old → new", "老结构",
                           "兼容", "DEPRECATED_CAMEL", "spec v2",
                           "FORBIDDEN_", "LEGACY_",
                           "warn", "error", "校验", "驼峰", "命中",
                           "举例", "替换为", "禁止", "非法", "移除",
                           "删除", "反例", "反面模式", "错误写法",
                           "正确写法", "易混淆", "→")
            context = "\n".join(lines[max(0, line_no - 8):line_no + 1])
            in_whitelist = any(k in line for k in wl_keywords) or (
                line.lstrip().startswith("|") and any(k in context for k in wl_keywords)
            )

            for term in FORBIDDEN_CAMEL:
                if not re.search(rf"\b{re.escape(term)}\b", line):
                    continue
                if in_whitelist:
                    continue
                hits.append((path, line_no, term, "deprecated_camel"))

            for term in FORBIDDEN_FIELDS:
                # 仅匹配 yaml-key 写法：开头是 "tableid:" / "<spaces>tableid:"
                if not re.search(rf"(^|[\s\"'])({re.escape(term)})\s*:", line):
                    continue
                if in_whitelist:
                    continue
                hits.append((path, line_no, term, "deprecated_field"))

            for pat in LEGACY_METADATA_PATTERNS:
                if re.search(pat, line) and not in_whitelist:
                    hits.append((path, line_no, pat, "legacy_metadata"))

            if not _is_negative_fixture(path) and _is_workflow_hardening_scope(path, skill_root):
                for term in FORBIDDEN_WORKFLOW_TERMS:
                    if re.search(rf"\b{re.escape(term)}\b", line) and not in_whitelist:
                        hits.append((path, line_no, term, "forbidden_workflow_term"))

        if not _is_negative_fixture(path) and _is_workflow_hardening_scope(path, skill_root):
            in_table_set = False
            table_set_indent = 0
            pending_workflow_version_child = False
            workflow_version_indent = 0
            for line_no, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                indent = len(line) - len(line.lstrip(" "))
                if re.match(r"workflowVersion\s*:", stripped):
                    pending_workflow_version_child = True
                    workflow_version_indent = indent
                    continue
                if pending_workflow_version_child and indent <= workflow_version_indent:
                    pending_workflow_version_child = False
                if pending_workflow_version_child and re.match(r"-\s+\w", stripped):
                    hits.append((path, line_no, "workflowVersion[]", "forbidden_workflow_term"))
                    pending_workflow_version_child = False
                if pending_workflow_version_child and indent > workflow_version_indent:
                    pending_workflow_version_child = False
                if re.match(r"workflowPvMisTableSet\s*:", stripped):
                    in_table_set = True
                    table_set_indent = indent
                    continue
                if in_table_set and indent <= table_set_indent:
                    in_table_set = False
                if in_table_set and re.match(r"-?\s*rowguid\s*:", stripped):
                    hits.append((path, line_no, "workflowPvMisTableSet.rowguid", "forbidden_workflow_term"))
    return hits


def _check_disallowed_root_dirs(skill_root: Path) -> list[Path]:
    """skill 仓库根禁止出现"应用产物目录""上次会话计划文档"。"""
    bad: list[Path] = []
    for name in DISALLOWED_APP_DIRS:
        p = skill_root / name
        if p.is_dir():
            bad.append(p)
    for plan in skill_root.glob("*-plan.md"):
        bad.append(plan)
    return bad


def _check_required_audit_contract(skill_root: Path) -> list[str]:
    """确认计划文档追溯契约没有被后续编辑删掉。"""
    errors: list[str] = []
    for rel_path, terms in REQUIRED_AUDIT_CONTRACT.items():
        path = skill_root / rel_path
        if not path.is_file():
            errors.append(f"❌ 缺少计划追溯契约文件：{rel_path}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"❌ 无法读取计划追溯契约文件：{rel_path} ({exc})")
            continue
        missing = [term for term in terms if term not in text]
        if missing:
            errors.append(
                f"❌ {rel_path} 缺少计划追溯关键字段：{', '.join(missing)}"
            )
    return errors


def cli():
    parser = argparse.ArgumentParser(description="skill 仓库自检看门人")
    parser.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="skill 仓库根目录（默认是脚本所在目录的父目录）",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="严格模式：警告也作为错误返回非零退出码",
    )
    args = parser.parse_args()

    skill_root = Path(args.skill_root).resolve()
    if not (skill_root / "SKILL.md").is_file():
        print(f"❌ {skill_root} 不像 skill 仓库根（缺少 SKILL.md）", file=sys.stderr)
        return 1

    print(f"🔍 lint_skill: 扫描 {skill_root}")

    errors: list[str] = []
    warnings: list[str] = []

    bad_dirs = _check_disallowed_root_dirs(skill_root)
    for p in bad_dirs:
        errors.append(
            f"❌ skill 仓库根禁止出现应用产物 / 上次会话计划文档：{p}\n"
            f"   建议：把它移走（或加入 .gitignore），保持 skill 仓库只承载 skill 资产。"
        )

    errors.extend(_check_required_audit_contract(skill_root))

    hits = _check_forbidden_terms(skill_root)
    for path, line_no, term, category in hits:
        rel = path.relative_to(skill_root)
        if category == "deprecated_camel":
            warnings.append(
                f"⚠️  {rel}:{line_no} 出现已废弃驼峰键 '{term}'（spec v2）。"
                f"如果是反例/迁移说明，请放在含'已废弃 / 迁移 / 老结构'的段落里。"
            )
        elif category == "deprecated_field":
            warnings.append(
                f"⚠️  {rel}:{line_no} 出现已废弃字段 '{term}: ...'（spec v2 已删除）。"
            )
        elif category == "legacy_metadata":
            warnings.append(
                f"⚠️  {rel}:{line_no} 出现老结构路径片段 '{term}'（spec v2 应用资产直接挂在 <apptag>/ 下）。"
            )
        elif category == "forbidden_workflow_term":
            warnings.append(
                f"⚠️  {rel}:{line_no} 出现 workflow 已禁止字段/结构 '{term}'。"
                f"如为反例 fixture，请将文件名标记为 bad/invalid/legacy。"
            )

    for e in errors:
        print(e, file=sys.stderr)
    for w in warnings:
        print(w, file=sys.stderr)

    print()
    print(f"通过文件数（按检查项）：errors={len(errors)} warnings={len(warnings)}")

    if errors:
        return 1
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(cli())
