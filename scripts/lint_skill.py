#!/usr/bin/env python3
"""lint_skill.py — skill 仓库自检看门人.

防止 skill 仓库自身退化到老结构：
1. 不允许 references / assets/templates / scripts 出现已废弃驼峰键（spec v2）
2. 不允许 references / assets/templates 出现 `tableid` / `fromMisTableId` / `fromFieldId`
3. 不允许 references / assets/templates 出现 `<apptag>/metadata/<asset>` 这种老结构示例
4. 不允许 skill 仓库根直接出现"应用产物目录"（如 ipdmanage/ / xmlx/）或上次会话计划文档（*-plan.md）

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

# 老结构路径片段
LEGACY_METADATA_PATTERNS = [
    r"<apptag>/metadata/<asset>",
    r"<apptag>/metadata/[a-z_]+",
    r"/metadata/<asset>",
]

# skill 仓库根禁止出现的"应用产物 / 上次会话产物"
DISALLOWED_APP_DIRS = ["ipdmanage", "xmlx", "purchaseproject"]


def _is_skill_doc_or_template(path: Path, skill_root: Path) -> bool:
    """是否属于"应当遵守 spec v2"的 skill 资产文件。

    references/**/*.md / assets/templates/* / scripts/*.py 都算。
    SKILL.md / README.md 顶层文档也算。
    skill 仓库根直下的 *.md / *.yml 也算（如临时插入的示例不应包含已废弃字段）。
    规范文件本身（Epoint 工作流 YAML 定义规范*.md）跳过 — 它就是 spec 源文件。
    """
    rel = path.relative_to(skill_root)
    name = path.name
    if name.startswith("Epoint工作流YAML定义规范") or name.startswith("Epoint 工作流 YAML 定义规范"):
        return False
    parts = rel.parts
    if parts[0] in ("references", "assets", "scripts"):
        return path.suffix.lower() in (".md", ".yml", ".yaml", ".py", ".json")
    if len(parts) == 1 and path.suffix.lower() in (".md", ".yml", ".yaml"):
        return True  # 仓库根直下的文档
    return False


def _check_forbidden_terms(skill_root: Path) -> list[tuple[Path, int, str, str]]:
    """扫描 skill 资产文件，返回 (file, line, term, category) 命中清单。

    白名单：
    - DEPRECATED_CAMEL / FORBIDDEN_CAMEL / 老结构示例引用 — 这些是"用来报错/指引迁移"的字面量，
      允许出现在 validate_yml.py / lint_skill.py 自身、以及标题为"已废弃 / DEPRECATED / 红线 / 迁移"的文档段。
    """
    SELF_NAMES = {"validate_yml.py", "lint_skill.py"}
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

        for line_no, line in enumerate(text.splitlines(), start=1):
            # 老结构 / 已废弃字段允许出现在以下"白名单段"
            #   - 行内含"已废弃" / "deprecated" / "红线" / "迁移" / "DEPRECATED_CAMEL"
            #   - 行内是 markdown 表格的"老 → 新"映射
            #   - 行内描述校验规则（含 "warn" / "error" / "驼峰" / "命中" 等关键词）
            wl_keywords = ("已废弃", "deprecated", "DEPRECATED",
                           "红线", "迁移", "old → new", "老结构",
                           "兼容", "DEPRECATED_CAMEL", "spec v2",
                           "FORBIDDEN_", "LEGACY_",
                           "warn", "error", "校验", "驼峰", "命中",
                           "举例", "替换为", "→")
            in_whitelist = any(k in line for k in wl_keywords)

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
