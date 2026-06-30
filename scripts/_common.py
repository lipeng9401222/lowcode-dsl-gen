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
    workflow/、page/、appinfo.lowcode.yml、appref.lowcode.yml。
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
    KNOWN_ASSETS = {"codeitem", "mis", "module", "event", "workflow", "page", "api"}

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


def yaml_load_str(text: str) -> dict:
    """从 yaml 字符串载入为 dict（用于在内存中预览/改写，不落盘）."""
    _ensure_yaml()
    return _yaml.safe_load(text)


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


def read_json_param(inline_value, file_path, *, expected_type=None, label: str = "JSON"):
    """从内联 JSON 字符串 `--xxx-json` 或文件 `--xxx-file` 读取 JSON，二选一。

    设计目的：超长 / 含大量中文的内联 JSON 会把命令行撑爆，导致部分 Agent 执行环境
    无输出或挂起（参考 testipd 事故）。提供 `--xxx-file` 让调用方把 JSON 写进文件再传路径，
    规避命令行长度与转义问题。

    返回解析后的对象；两者都未提供时返回 None。
    """
    if inline_value and file_path:
        raise ValueError(f"{label}: 内联 JSON 与文件路径二选一，不要同时提供")
    if file_path:
        p = Path(file_path)
        if not p.is_file():
            raise ValueError(f"{label}: 文件不存在: {file_path}")
        return parse_json_arg(p.read_text(encoding="utf-8"), expected_type=expected_type, label=label)
    if inline_value:
        return parse_json_arg(inline_value, expected_type=expected_type, label=label)
    return None


def check_landing(*, dry_run: bool, confirm: bool, target, preview: str,
                  asset_label: str = "资产"):
    """统一的「落盘前确认红线」门禁：先预览、后确认，才允许写文件。

    返回 (should_write: bool, exit_code: int)：
    - dry_run=True：打印预览（不写文件），返回 (False, 0)。
    - 非 dry_run 且 confirm=False：打印拒绝原因，返回 (False, 1)。
    - 非 dry_run 且 confirm=True：返回 (True, 0)，调用方可落盘。

    用法：
        should_write, code = check_landing(
            dry_run=args.dry_run, confirm=args.confirm,
            target=target, preview=content, asset_label="代码项")
        if not should_write:
            return code
        target.write_text(content, ...)
    """
    if dry_run:
        print_info(f"[dry-run] 将创建/修改{asset_label}: {target}")
        print_info("[dry-run] 预览内容如下（未写入任何文件）：")
        print("-" * 60)
        print(preview)
        print("-" * 60)
        print_info("[dry-run] 请人工逐项核对以上内容；确认无误后去掉 --dry-run 并加 --confirm 落盘。")
        return (False, 0)
    if not confirm:
        print_err(
            f"拒绝落盘：{asset_label} 必须经人工预览确认后才能写入。\n"
            f"请先用 --dry-run 预览内容，逐项核对无误后再加 --confirm 落盘。\n"
            f"（落盘前确认红线：禁止未经 dry-run 预览 + --confirm 确认直接写文件，也禁止用批处理脚本绕过）"
        )
        return (False, 1)
    return (True, 0)


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
    """把任意字符串转换为安全的文件名（保留中文，去除特殊字符，强制小写）."""
    # 替换文件系统不允许的字符，并强制小写
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip().lower()


# ============================================================
# spec v2 路径红线
# ============================================================

def assert_no_metadata_layer(app_root: Path) -> tuple[bool, str]:
    """spec v2 路径红线：应用根 = <apptag>/，禁止再有 metadata/ 这一层。

    返回 (ok, error_message)：ok=True 表示路径合法；ok=False 时 error_message
    给出可读说明，调用方应直接 print_err 并退出。
    """
    app_root_str = str(app_root).replace("\\", "/")
    if "/metadata/" in app_root_str + "/" or app_root.name == "metadata":
        return False, (
            "❌ 检测到老结构：应用根目录路径包含 /metadata/ 段。\n"
            f"   传入路径：{app_root}\n"
            "   spec v2 已废弃 metadata/ 层，应用资产应直接挂在 <apptag>/ 下。\n"
            "   请把 --app-root 指向 <apptag>/ 而不是 <apptag>/metadata/。\n"
            "   如确需在老应用上追加内容（兼容场景），请先迁移目录：\n"
            f"     mv {app_root.parent if app_root.name == 'metadata' else app_root}/metadata/* "
            f"{app_root.parent if app_root.name == 'metadata' else app_root}/ && "
            f"rmdir {app_root.parent if app_root.name == 'metadata' else app_root}/metadata"
        )
    return True, ""


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
