"""通用工具：路径解析、模板渲染、UUID 生成、时间戳等.

被 scaffold_app.py / add_codeitem.py / add_mis_field.py / add_event.py / add_workflow.py /
validate_yml.py / path_resolver.py 共用.
"""
from __future__ import annotations

import os
import re
import sys
import time
import uuid
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional


# ============================================================
# 路径解析
# ============================================================

def find_action_root(start: Path) -> Optional[Path]:
    """从给定路径向上查找最近的 action 子工程根（包含 src/main/resources/META-INF/resources）.

    返回 action 子工程根 Path 或 None.
    """
    current = start.resolve()
    while current != current.parent:
        candidate = current / "src" / "main" / "resources" / "META-INF" / "resources"
        if candidate.is_dir():
            return current
        current = current.parent
    return None


def find_workspace_root(start: Path) -> Optional[Path]:
    """从给定路径向上查找最近的 workspace 根（含 .git）."""
    current = start.resolve()
    while current != current.parent:
        if (current / ".git").is_dir():
            return current
        current = current.parent
    return None


def compute_app_root(
    action_root: Path,
    apptag: str,
    *,
    developerstag: str = "epoint",
    tenantguid: str = "",
    baseouguid: str = "",
    categories: Optional[list[str]] = None,
) -> Path:
    """根据应用归属计算应用根目录绝对路径（去掉 metadata 层）.

    新结构：<action_root>/src/main/resources/META-INF/resources/
        <developerstag>/[<tenantguid>/][<baseouguid>/]<categories...>/<apptag>/

    应用资产直接挂在 <apptag>/ 下：codeitem/、mis/、module/、event/、
    workflow/、pagedesigne/、appinfo.lowcode.yml、appref.lowcode.yml。
    """
    parts = [
        action_root,
        "src", "main", "resources", "META-INF", "resources",
        developerstag,
    ]
    if tenantguid:
        parts.append(tenantguid)
    if baseouguid:
        parts.append(baseouguid)
    if categories:
        parts.extend(categories)
    parts.append(apptag)
    return Path(*[str(p) for p in parts])


def compute_metadata_path(*args, **kwargs) -> Path:
    """[已废弃] 兼容老 API，等价于 compute_app_root.

    新结构去掉了 metadata/ 层级；此函数返回与 compute_app_root 相同的路径。
    """
    import warnings
    warnings.warn(
        "compute_metadata_path 已废弃，请改用 compute_app_root（新结构去掉了 metadata/ 层）",
        DeprecationWarning,
        stacklevel=2,
    )
    return compute_app_root(*args, **kwargs)


EXCLUDE_DIRS = {"target", "build", "out", "dist", "node_modules", ".git", ".idea", ".vscode", ".history", "classes"}


def _is_in_excluded(path: Path, workspace_root: Path) -> bool:
    """判断 path 是否处于被排除的目录（target/build/node_modules 等）下."""
    try:
        rel = path.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return False
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def find_existing_apptag(workspace_root: Path, apptag: str) -> Optional[Path]:
    """在 workspace 中查找已存在的指定 apptag 的应用根目录.

    新结构：`<...>/META-INF/resources/<...>/<apptag>/` 下直接含 codeitem/mis/...
    老结构（向后兼容）：`<...>/META-INF/resources/<...>/<apptag>/metadata/<asset>/...`

    返回应用根目录路径（不含 metadata/ 层）。如检测到老结构，会通过 print 给警告。
    """
    if not workspace_root or not workspace_root.is_dir():
        return None
    import sys as _sys
    KNOWN_ASSETS = {"codeitem", "mis", "module", "event", "workflow", "pagedesigne", "api"}

    def _looks_like_app_root(path: Path) -> bool:
        # 含 appinfo.lowcode.yml 或任意一个资产子目录
        if (path / "appinfo.lowcode.yml").is_file():
            return True
        for asset in KNOWN_ASSETS:
            if (path / asset).is_dir():
                return True
        return False

    # 1) 优先扫新结构：<apptag>/ 下直接放资产
    pattern_new = f"**/src/main/resources/META-INF/resources/**/{apptag}"
    for candidate in workspace_root.glob(pattern_new):
        if not candidate.is_dir():
            continue
        if _is_in_excluded(candidate, workspace_root):
            continue
        if _looks_like_app_root(candidate):
            return candidate

    # 2) 兼容老结构：<apptag>/metadata/
    pattern_old = f"**/src/main/resources/META-INF/resources/**/{apptag}/metadata"
    for candidate in workspace_root.glob(pattern_old):
        if not candidate.is_dir():
            continue
        if _is_in_excluded(candidate, workspace_root):
            continue
        # 老结构：返回 <apptag>/ 而非 metadata/，并提示
        legacy_app_root = candidate.parent
        print(
            f"⚠️ 检测到老结构应用根：{legacy_app_root}/metadata/。"
            f"建议迁移到新结构（去掉 metadata 层），让资产直接挂在 {legacy_app_root}/ 下。",
            file=_sys.stderr,
        )
        return legacy_app_root

    # 3) 兜底：放宽 src/main/resources 限制
    for candidate in workspace_root.glob(f"**/META-INF/resources/**/{apptag}"):
        if not candidate.is_dir():
            continue
        if _is_in_excluded(candidate, workspace_root):
            continue
        if _looks_like_app_root(candidate):
            return candidate
    return None


# ============================================================
# 模板渲染
# ============================================================

SKILL_ROOT = Path(__file__).parent.parent  # 指向 lowcode-dsl-gen/
TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"


def load_template(template_name: str) -> str:
    """加载 assets/templates/ 下的模板文件.

    Args:
        template_name: 模板文件名（如 'codeitem.yml', 'appinfo.lowcode.yml'）

    Returns:
        模板内容字符串
    """
    path = TEMPLATES_DIR / template_name
    if not path.is_file():
        raise FileNotFoundError(f"模板文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def render_template(template: str, variables: dict) -> str:
    """简单的 {{KEY}} 占位符替换."""
    result = template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    # 检查未替换的占位符
    remaining = re.findall(r"\{\{[A-Z_0-9]+\}\}", result)
    if remaining:
        # 不抛异常，但提示
        for placeholder in set(remaining):
            print(f"⚠️  警告：未替换的占位符 {placeholder}", file=sys.stderr)
    return result


def render_json_template(template_name: str, variables: dict) -> dict:
    """渲染 assets/templates 下的 JSON 模板并解析成 dict."""
    return json.loads(render_template(load_template(template_name), variables))


# ============================================================
# UUID / 时间戳
# ============================================================

def gen_uuid() -> str:
    """生成标准 UUIDv4."""
    return str(uuid.uuid4())


def gen_node_id() -> str:
    """生成动作流节点 ID（毫秒时间戳风格）."""
    return str(int(time.time() * 1000))


def gen_node_ids(n: int) -> list[str]:
    """生成 n 个唯一的节点 ID（毫秒时间戳，递增间隔避免冲突）."""
    base = int(time.time() * 1000)
    return [str(base + i * 13) for i in range(n)]


def gen_page_id(title: str, *, prefix: str = "page") -> str:
    """生成稳定页面 id。

    优先提取标题中的 ASCII 单词；纯中文标题用 sha1 短摘要，避免引入拼音依赖。
    """
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", title or "")
    if words:
        slug = "-".join(w.lower() for w in words)
    else:
        digest = hashlib.sha1((title or prefix).encode("utf-8")).hexdigest()[:8]
        slug = f"{prefix}-{digest}"
    return re.sub(r"-+", "-", slug).strip("-") or prefix


def now_unix() -> int:
    """当前 Unix 秒级时间戳."""
    return int(time.time())


def now_str() -> str:
    """当前时间格式化为 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# YAML 安全读写（依赖 pyyaml；若未安装也保留原始字符串模板能力）
# ============================================================

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def _ensure_yaml():
    if not _HAS_YAML:
        raise RuntimeError(
            "需要 pyyaml. 请安装：pip install pyyaml"
        )


def yaml_load(path: Path) -> dict:
    """加载 yaml 文件为 dict."""
    _ensure_yaml()
    return _yaml.safe_load(path.read_text(encoding="utf-8"))


def yaml_dump_str(data) -> str:
    """转 dict 为 yaml 字符串（保留中文不转义）."""
    _ensure_yaml()
    return _yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


def yaml_dump(data, path: Path) -> None:
    """写 dict 到 yaml 文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_dump_str(data), encoding="utf-8")


def json_load(path: Path) -> dict:
    """加载 JSON 文件."""
    return json.loads(path.read_text(encoding="utf-8"))


def json_dump(data, path: Path, *, indent: int = 2) -> None:
    """写 JSON 文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=indent, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_json_arg(value: str, *, expected_type=None, label: str = "JSON"):
    """解析命令行 JSON 字符串，并可校验顶层类型."""
    try:
        data = json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"{label} 解析失败: {e}") from e
    if expected_type and not isinstance(data, expected_type):
        raise ValueError(f"{label} 顶层应为 {expected_type.__name__}")
    return data


# ============================================================
# 命名校验
# ============================================================

APPTAG_PATTERN = re.compile(r"^[a-z][a-z0-9]*$")
MIS_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*$")
FIELD_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
# Backward-compatible aliases for older scripts/imports. New code should choose
# is_valid_mis_name for table/name fields and is_valid_field_name for fields.
TABLENAME_PATTERN = FIELD_NAME_PATTERN
FIELDNAME_PATTERN = FIELD_NAME_PATTERN
MODEL_PATH_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)?$")


def is_valid_apptag(apptag: str) -> bool:
    """校验 apptag 是否合法（小写英文 + 数字，首字符是字母）."""
    return bool(APPTAG_PATTERN.match(apptag))


def is_valid_mis_name(name: str) -> bool:
    """校验 MIS 表名/name/tableName（小写英文数字，不允许下划线）."""
    return bool(MIS_NAME_PATTERN.match(name or ""))


def is_valid_field_name(name: str) -> bool:
    """校验 MIS 字段名（小写英文数字，可包含下划线）."""
    return bool(FIELD_NAME_PATTERN.match(name or ""))


def is_valid_tablename(tablename: str) -> bool:
    """兼容旧接口：校验字段名风格。新代码请使用 is_valid_mis_name/is_valid_field_name."""
    return is_valid_field_name(tablename)


def is_valid_model_path(path: str) -> bool:
    """校验页面模型短路径，如 employee.name 或 employeeList."""
    return bool(MODEL_PATH_PATTERN.match(path or ""))


def safe_filename(name: str) -> str:
    """把任意字符串转换为安全的文件名（保留中文，去除特殊字符）."""
    # 仅替换文件系统不允许的字符
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


# ============================================================
# 控制台输出
# ============================================================

def print_ok(msg: str):
    print(f"✅ {msg}")


def print_err(msg: str):
    print(f"❌ {msg}", file=sys.stderr)


def print_warn(msg: str):
    print(f"⚠️  {msg}", file=sys.stderr)


def print_info(msg: str):
    print(f"ℹ️  {msg}")
