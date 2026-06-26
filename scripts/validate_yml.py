#!/usr/bin/env python3
"""validate_yml.py — 静态校验单个 yml 文件 或 整个应用根目录（spec v2 推荐 `<apptag>/`）.

支持的校验类型：
- appinfo.lowcode.yml  → 必填字段、apptag 与目录一致
- appref.lowcode.yml   → 数组结构、engineguid 枚举
- codeitem yml         → type=codeitem、items 结构
- mis yml              → type=mis、字段必填属性、type 枚举
- module yml           → type=module、parentGuid 闭合
- event yml            → type=event、节点 ID 唯一、edges 引用
- workflow yml         → type=workflow、活动/变迁完整性
- pagedesigne yml/json → kind=page、schemaVersion 正确

用法：
    python validate_yml.py <文件或目录路径>
    python validate_yml.py --strict <文件或目录路径>     # 严格模式：警告也当错误
    python validate_yml.py --check-refs <应用根目录>     # 跨文件引用校验（新结构 <apptag>/ 或老结构 <apptag>/metadata/）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    APPTAG_PATTERN,
    FIELD_NAME_PATTERN,
    MIS_NAME_PATTERN,
    print_err,
    print_info,
    print_ok,
    print_warn,
    yaml_load,
)
from field_schema import (  # noqa: E402
    ASSET_NODE_SCHEMAS,
    WORKFLOW_NODE_SCHEMAS,
    check_node_fields,
    extract_placeholders,
    is_context_reference,
)
from mis_defaults import (  # noqa: E402
    MIS_FIELD_REQUIRED_TEMPLATE_KEYS,
    VALID_MIS_TYPES as DEFAULT_VALID_MIS_TYPES,
)
from workflow_defaults import (  # noqa: E402
    DEFAULT_IS_CHECKMATERIALSUBMIT,
    FLOW_BRANCH_ICON_Y,
    FLOW_BROWSE_ICON_X,
    FLOW_BROWSE_ICON_Y,
    FLOW_FIRST_ACTIVITY_ICON_X,
    FLOW_MIN_STEP_X,
    HANDLE_URL_ACTIVITY_TYPES,
    WORKFLOW_RENDERER_PREFIX,
    default_operationvisiablecase,
    default_splittype,
    flow_step_after,
)


def apply_node_schema(result: "ValidationResult", path: str, label: str, node, schema_key: str,
                      registry: dict | None = None) -> None:
    """按 field_schema 注册表对单个节点做字段白名单/必填/别名强校验。

    - error 级（命中别名、缺必填）直接登记为错误；
    - warn 级（未知字段）登记为 warn_strict_error：默认 warn，--strict 升 error。
    """
    registry = registry if registry is not None else WORKFLOW_NODE_SCHEMAS
    schema = registry.get(schema_key)
    if not schema:
        return
    for severity, msg in check_node_fields(label, node, schema):
        if severity == "error":
            result.err(path, msg)
        else:
            result.warn_strict_error(path, msg)


VALID_ENGINEGUIDS = {"codeitem", "mis", "module", "event", "workflow", "pagedesigne", "api"}
VALID_MIS_TYPES = DEFAULT_VALID_MIS_TYPES
BARE_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
VALID_DISPLAY_TYPES = {
    "textbox", "combobox", "datagrid", "radiobuttonlist", "checkbox",
    "spinner", "datepicker", "ouradiotree", "ouchecktree",
    "userradiotree", "userchecktree", "webuploader", "webeditor",
    "textarea", "dropdownradiotree", "dropdownchecktree",
    "fckeditor", "checkboxlist",
}


class ValidationResult:
    def __init__(self):
        self.errors: list[tuple[str, str]] = []  # (path, message)
        self.warnings: list[tuple[str, str]] = []
        self.passed: list[str] = []
        # spec v2: 这组 warning 在 --strict 模式下升级为 error。
        # 调用方用 warn_strict_error 把"已废弃字段命中"等问题登记到这里。
        self.strict_only_errors: list[tuple[str, str]] = []

    def err(self, path: str, msg: str):
        self.errors.append((path, msg))

    def warn(self, path: str, msg: str):
        self.warnings.append((path, msg))

    def warn_strict_error(self, path: str, msg: str):
        """spec v2 已废弃字段：默认 warn，--strict 模式升级为 error。"""
        self.strict_only_errors.append((path, msg))

    def ok(self, path: str):
        self.passed.append(path)

    def report(self, strict: bool = False) -> int:
        # strict 模式：把 strict_only_errors 升级为 errors；否则当 warnings 显示
        if strict:
            for item in self.strict_only_errors:
                self.errors.append(item)
        else:
            for item in self.strict_only_errors:
                self.warnings.append(item)
        error_paths = {p for p, _ in self.errors}
        passed = [p for p in self.passed if p not in error_paths]
        for p, m in self.errors:
            print(f"❌ {p}: {m}", file=sys.stderr)
        for p, m in self.warnings:
            print(f"⚠️  {p}: {m}", file=sys.stderr)
        for p in passed:
            print(f"✅ {p}")
        print()
        print(f"通过: {len(passed)}  警告: {len(self.warnings)}  错误: {len(self.errors)}")
        if self.errors:
            return 1
        if strict and self.warnings:
            return 2
        return 0


def is_valid_uuid(s: str) -> bool:
    """检查是否合法 UUIDv4 或 V1-XXX-XXX-XXX-XXX 类语义化."""
    if not isinstance(s, str):
        return False
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


CONDITION_REF_PATTERN = re.compile(r"\[(\d+)\]")
CONDITION_EXPR_TOKEN_PATTERN = re.compile(r"\s*(\[\d+\]|\(|\)|AND|OR|NOT)\s*", re.IGNORECASE)


def condition_sort_key(indexed_condition: tuple[int, dict]) -> tuple[int, int]:
    index, condition = indexed_condition
    try:
        return int(condition.get("ordernum", index)), index
    except (TypeError, ValueError):
        return index, index


def validate_condition_expression_text(expression: str, single_count: int) -> str | None:
    expression = expression or ""
    refs = [int(value) for value in CONDITION_REF_PATTERN.findall(expression or "")]
    if not refs:
        return "conditionexpression 必须引用同一变迁下的单一表达式序号，如 [1] AND [2]"
    seen_refs: set[int] = set()
    for ref in refs:
        if ref in seen_refs:
            return f"conditionexpression 重复引用 [{ref}]"
        seen_refs.add(ref)
        if ref < 1 or ref > single_count:
            return f"conditionexpression 引用 [{ref}] 越界，同一变迁下只有 {single_count} 条 type=10 条件"

    compact = re.sub(r"\s+", "", expression or "")
    tokens: list[str] = []
    position = 0
    while position < len(expression or ""):
        match = CONDITION_EXPR_TOKEN_PATTERN.match(expression, position)
        if not match:
            return "conditionexpression 仅支持 [n]、AND、OR、NOT 和括号"
        tokens.append(match.group(1).upper())
        position = match.end()
    if re.sub(r"\s+", "", "".join(tokens)).upper() != compact.upper():
        return "conditionexpression 包含无法识别的内容"

    position = 0

    def parse_expression() -> bool:
        return parse_or()

    def parse_or() -> bool:
        if not parse_and():
            return False
        while position < len(tokens) and tokens[position] == "OR":
            advance()
            if not parse_and():
                return False
        return True

    def parse_and() -> bool:
        if not parse_not():
            return False
        while position < len(tokens) and tokens[position] == "AND":
            advance()
            if not parse_not():
                return False
        return True

    def parse_not() -> bool:
        if position < len(tokens) and tokens[position] == "NOT":
            advance()
            return parse_not()
        return parse_primary()

    def parse_primary() -> bool:
        if position >= len(tokens):
            return False
        token = tokens[position]
        if CONDITION_REF_PATTERN.fullmatch(token):
            advance()
            return True
        if token == "(":
            advance()
            if not parse_expression():
                return False
            if position >= len(tokens) or tokens[position] != ")":
                return False
            advance()
            return True
        return False

    def advance() -> None:
        nonlocal position
        position += 1

    if not parse_expression() or position != len(tokens):
        return "conditionexpression 语法不合法，仅支持 [n]、AND、OR、NOT 和括号组合"
    return None


def condition_expression_type(condition: dict) -> int | None:
    try:
        return int(condition.get("conditionexpressiontype", 10))
    except (TypeError, ValueError):
        return None


def detect_yml_type(path: Path, data: Optional[dict] = None) -> str:
    """根据文件名 + 内容识别 yml 类型."""
    name = path.name
    if name == "appinfo.lowcode.yml":
        return "appinfo"
    if name == "appref.lowcode.yml":
        return "appref"
    if data is None:
        return "unknown"

    # 看顶层 type 字段
    t = data.get("type") if isinstance(data, dict) else None
    # codeitem 类标准值是 'codeitem'；旧版 'code' 也当 codeitem 识别，后续校验会报错提示修复
    if t in ("codeitem", "code"):
        return "codeitem"
    if t == "mis":
        return "mis"
    if t == "module":
        return "module"
    if t == "event":
        return "event"
    if t == "workflow":
        return "workflow"

    # 没 type，根据父目录推断
    parent = path.parent.name
    if parent == "codeitem":
        return "codeitem"
    if parent == "mis":
        return "mis"
    if parent == "module":
        return "module"
    if parent == "event":
        return "event"
    if parent == "workflow":
        return "workflow"
    if parent == "page":
        return "pagedesigne"

    return "unknown"


def validate_appinfo(path: Path, data: dict, result: ValidationResult):
    p = str(path)
    required = ["developerstag", "applicationname", "apptag"]
    for f in required:
        if not data.get(f):
            result.err(p, f"必填字段缺失或为空: {f}")
            return

    apptag = data["apptag"]
    if not APPTAG_PATTERN.match(apptag):
        result.err(p, f"apptag '{apptag}' 不合法（应为小写字母开头 + 字母/数字）")

    # apptag 与目录名一致：
    # 新结构 appinfo.lowcode.yml 直接在 <apptag>/ 下 → path.parent.name 即 apptag
    # 老结构 appinfo.lowcode.yml 在 <apptag>/metadata/ 下 → path.parent.parent.name 即 apptag
    if path.parent.name == "metadata":
        apptag_dir = path.parent.parent.name
    else:
        apptag_dir = path.parent.name
    if apptag != apptag_dir:
        result.err(p, f"apptag '{apptag}' 与目录名 '{apptag_dir}' 不一致")

    # developerstag 与目录树一致：找 META-INF/resources 后面的第一层目录
    developerstag = data["developerstag"]
    parts = path.parts
    try:
        idx = parts.index("META-INF")
        # META-INF/resources/<开发商>
        if parts[idx + 1] == "resources":
            dev_dir = parts[idx + 2]
            if developerstag != dev_dir:
                result.warn(p, f"developerstag '{developerstag}' 与目录 '{dev_dir}' 不一致")
    except (ValueError, IndexError):
        pass

    if not data.get("kitid"):
        result.warn(p, "kitid 未设置（多套件场景下必填）")

    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_appref(path: Path, data, result: ValidationResult):
    p = str(path)
    if data is None:
        # 空文件也允许
        result.ok(p)
        return
    if not isinstance(data, list):
        result.err(p, f"顶层应为数组，实际是 {type(data).__name__}")
        return
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            result.err(p, f"第 {i + 1} 项不是对象")
            continue
        eg = item.get("engineguid")
        if not eg:
            result.err(p, f"第 {i + 1} 项缺少 engineguid")
        elif eg not in VALID_ENGINEGUIDS:
            result.err(p, f"第 {i + 1} 项 engineguid '{eg}' 不在合法枚举: {sorted(VALID_ENGINEGUIDS)}")
        names = item.get("name")
        if not names:
            result.err(p, f"第 {i + 1} 项缺少 name")
        elif not isinstance(names, list):
            result.err(p, f"第 {i + 1} 项 name 必须是数组")
    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_codeitem(path: Path, data: dict, result: ValidationResult):
    p = str(path)
    t = data.get("type")
    if t == "code":
        result.err(p, "type 是旧版 'code'，现在统一要求 'codeitem'，请将第一行改为 `type: codeitem`")
        return
    if t != "codeitem":
        result.err(p, f"type 应为 'codeitem'，实际 '{t}'")
        return
    if not data.get("name"):
        result.err(p, "缺少 name")
    items = data.get("items")
    if items is None:
        result.warn(p, "items 字段缺失或为空")
    elif not isinstance(items, list):
        result.err(p, "items 必须是数组")
    else:
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            if not item.get("codetext"):
                result.err(p, f"第 {i + 1} 项 codetext 缺失")
            if "codevalue" not in item:
                result.err(p, f"第 {i + 1} 项 codevalue 缺失")
            elif not isinstance(item["codevalue"], str):
                result.warn(
                    p,
                    f"第 {i + 1} 项 codevalue 应为字符串（加引号），实际 {type(item['codevalue']).__name__}",
                )
    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_mis(path: Path, data: dict, result: ValidationResult):
    p = str(path)
    if data.get("type") != "mis":
        result.err(p, f"type 应为 'mis'，实际 '{data.get('type')}'")
        return
    name = data.get("name")
    if not name:
        result.err(p, "缺少 name")
    elif not MIS_NAME_PATTERN.match(str(name)):
        result.err(p, f"name '{name}' 不合法（MIS 表名/name 必须小写英文数字，不能包含下划线）")
    table_name = data.get("tableName")
    if not table_name:
        result.err(p, "缺少 tableName")
    elif not MIS_NAME_PATTERN.match(str(table_name)):
        result.err(p, f"tableName '{table_name}' 不合法（必须小写英文数字，不能包含下划线）")
    if name and table_name and name != table_name:
        result.err(p, f"name '{name}' 与 tableName '{table_name}' 必须一致")
    fields = data.get("fields") or []
    if not fields:
        result.warn(p, "fields 为空")
    else:
        names_seen = set()
        for i, f in enumerate(fields):
            if not isinstance(f, dict):
                continue
            fname = f.get("name")
            if not fname:
                result.err(p, f"字段 {i + 1} 缺少 name")
                continue
            if not FIELD_NAME_PATTERN.match(str(fname)):
                result.err(p, f"字段名 '{fname}' 非法（应为小写英文数字，可包含下划线）")
            if fname in names_seen:
                result.err(p, f"字段名重复: {fname}")
            names_seen.add(fname)
            ftype = f.get("type")
            if not ftype:
                result.err(p, f"字段 {fname} 缺少 type")
            elif ftype not in VALID_MIS_TYPES:
                result.warn(
                    p, f"字段 {fname} type '{ftype}' 不在常用枚举: {sorted(VALID_MIS_TYPES)}",
                )
            if not f.get("description"):
                result.warn_strict_error(p, f"字段 {fname} 缺少 description")
            if "length" not in f:
                result.warn_strict_error(p, f"字段 {fname} 缺少 length")
            disp = f.get("fielddisplaytype")
            if not disp:
                result.warn_strict_error(p, f"字段 {fname} 缺少 fielddisplaytype")
            elif disp not in VALID_DISPLAY_TYPES:
                result.warn(
                    p, f"字段 {fname} fielddisplaytype '{disp}' 不在合法枚举",
                )
            if f.get("datasourceCodename") and disp != "combobox":
                result.warn_strict_error(
                    p,
                    f"字段 {fname} 绑定 datasourceCodename='{f.get('datasourceCodename')}'，"
                    "fielddisplaytype 建议为 combobox",
                )
            missing_template_keys = [
                key for key in MIS_FIELD_REQUIRED_TEMPLATE_KEYS
                if key not in f
            ]
            if missing_template_keys:
                result.warn_strict_error(
                    p,
                    f"字段 {fname} 缺少 MIS 模板必备属性: {', '.join(missing_template_keys)}",
                )
    # tableName 与文件名一致性
    fname_no_ext = re.sub(r"\.(mis\.)?ya?ml$", "", path.name)
    if not MIS_NAME_PATTERN.match(fname_no_ext):
        result.err(p, f"文件名前缀 '{fname_no_ext}' 不合法（MIS 英文文件名必须小写英文数字，不能包含下划线）")
    if table_name and fname_no_ext != table_name:
        result.warn(p, f"tableName '{table_name}' 与文件名 '{fname_no_ext}' 不一致")

    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_module(path: Path, data: dict, result: ValidationResult):
    p = str(path)
    if data.get("type") != "module":
        result.err(p, f"type 应为 'module'，实际 '{data.get('type')}'")
        return
    if not data.get("name"):
        result.err(p, "缺少 name")
    if not data.get("guid"):
        result.err(p, "缺少 guid")
    elif not is_valid_uuid(data["guid"]):
        result.warn(p, f"guid '{data['guid']}' 不是合法 UUID")
    code = data.get("code")
    if not code:
        result.warn(p, "缺少 code")
    elif not isinstance(code, str):
        result.warn(p, f"code 应为字符串，实际 {type(code).__name__}")

    # 子模块 parentGuid 校验
    items = data.get("items") or []
    root_guid = data.get("guid")
    for i, sub in enumerate(items):
        if not isinstance(sub, dict):
            continue
        if sub.get("parentGuid") != root_guid:
            result.warn(p, f"子模块 {i + 1} parentGuid 不指向根模块 guid")

    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_event(path: Path, data: dict, result: ValidationResult):
    p = str(path)
    if data.get("type") != "event":
        # 老示例可能省略 type，给警告
        result.warn(p, f"type 缺失或不是 'event'（实际: {data.get('type')}）")

    app = data.get("app") or {}
    if app.get("mode") != "actflow":
        result.warn(p, f"app.mode 应为 'actflow'（实际: {app.get('mode')}）")
    if not app.get("name"):
        result.err(p, "app.name 缺失")
    if not app.get("sign") and not app.get("code"):
        result.warn(p, "app.sign 和 app.code 都缺失，建议至少填一个作为接口标识")
    if app.get("id") and app.get("rowguid") and app["id"] != app["rowguid"]:
        result.warn(p, "app.id 与 app.rowguid 应相等")

    workflow = data.get("workflow") or {}
    graph = workflow.get("graph") or {}
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []

    # 节点 ID 唯一性
    node_ids = [n.get("id") for n in nodes if isinstance(n, dict)]
    dup = [x for x in set(node_ids) if node_ids.count(x) > 1]
    if dup:
        result.err(p, f"节点 ID 重复: {dup}")

    # 至少一个 start 节点 + 一个 end 节点
    has_start = any(
        (n.get("data") or {}).get("type") == "start"
        for n in nodes if isinstance(n, dict)
    )
    has_end = any(
        (n.get("data") or {}).get("type") in ("end", "end-vue")
        for n in nodes if isinstance(n, dict)
    )
    if not has_start:
        result.err(p, "缺少 start 节点")
    if not has_end:
        result.err(p, "缺少 end / end-vue 节点")

    # edges 引用闭合
    ids_set = set(node_ids)
    for e in edges:
        if not isinstance(e, dict):
            continue
        if e.get("source") not in ids_set:
            result.err(p, f"edge.source '{e.get('source')}' 在 nodes 中不存在")
        if e.get("target") not in ids_set:
            result.err(p, f"edge.target '{e.get('target')}' 在 nodes 中不存在")

    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_workflow(path: Path, data: dict, result: ValidationResult):
    """工作流 yml 校验.

    红线（强校验）:
        1. 必含 5 类节点: 开始(10) + 申请(30) + N 个审批(30) + 结束(20) + 浏览(100)
        2. 开始节点(10) 与 申请节点(30) 必须分拆为两个独立 activity
        3. 开始节点名称固定 '开始'；结束节点名称固定 '结束'
        4. 开始/结束/浏览节点的 handleurl/multitransactormode/timelimitenable/
           earlywarning_enable/isallowaddattachfile/is_passwhennotransactor 应为空
           （开始/结束节点的 handleurl 必须为空；浏览节点的这些字段也应为空）
        5. processversionguid 在所有子节点中必须一致
        6. 退回按钮(operationtype=30)必须有对应 workflowConfig(belongto=22, configname=backTargetScope)
        7. activity/transition 的 vmlid 唯一；transition.from/to 必须能在 activity 中找到
    """
    p = str(path)
    if data.get("type") != "workflow":
        result.err(p, f"type 应为 'workflow'，实际 '{data.get('type')}'")
        return

    # 兼容大小写：优先识别规范的小写键，未命中再降级查驼峰键并给警告
    wf = data.get("workFlow")
    if wf is None and "WorkFlow" in data:
        result.warn(p, "顶层应为 workFlow（小写 w 开头），不是 WorkFlow；按规范改正")
        wf = data.get("WorkFlow")
    wf = wf or {}

    process = wf.get("workflowProcess")
    if process is None and "WorkflowProcess" in wf:
        result.warn(p, "应为 workflowProcess（小写 w 开头），不是 WorkflowProcess")
        process = wf.get("WorkflowProcess")
    process = process or {}

    process_guid = process.get("processguid") or process.get("processguid")
    if not process_guid:
        result.err(p, "workflowProcess.processguid 缺失")
    if not (process.get("processname") or process.get("processname")):
        result.err(p, "workflowProcess.processname 缺失")

    version = wf.get("workflowVersion")
    if version is None and "WorkFlowVersion" in wf:
        result.warn(p, "应为 workflowVersion（小写 w 开头），不是 WorkFlowVersion")
        version = wf.get("WorkFlowVersion")
    if isinstance(version, list):
        result.err(p, "workFlow.workflowVersion 必须是单个对象，不能是数组；当前规范默认 1 个流程只有 1 个启用版本")
        version = version[0] if len(version) == 1 and isinstance(version[0], dict) else {}
    elif version is not None and not isinstance(version, dict):
        result.err(p, f"workFlow.workflowVersion 必须是对象，实际是 {type(version).__name__}")
        version = {}
    version = version or {}

    activities = version.get("activity")
    if activities is None and "Activity" in version:
        result.warn(p, "应为 activity（小写），不是 Activity")
        activities = version.get("Activity")
    activities = activities or []

    transitions = version.get("transition")
    if transitions is None and "Transition" in version:
        result.warn(p, "应为 transition（小写），不是 Transition")
        transitions = version.get("Transition")
    transitions = transitions or []

    workflow_config = version.get("workflowConfig") or version.get("WorkflowConfig") or []
    pv_material = (
        version.get("workflowPvMaterial")
        or version.get("WorkflowPvMaterial")
        or []
    )
    pv_mistableset = (
        version.get("workflowPvMisTableSet")
        or version.get("WorkflowPvMisTableSet")
        or []
    )

    # ============================================================
    # 收集 activity 字段，识别新旧两种结构（平铺 vs WorkflowActivity 包装）
    # ============================================================
    parsed_activities = []  # [(act_dict, owner_label_for_error)]
    for i, raw in enumerate(activities):
        if not isinstance(raw, dict):
            continue
        # 兼容旧结构：activity[i] = { WorkflowActivity: {...}, WorkflowActivityOperation: [...] }
        if "WorkflowActivity" in raw and "activityguid" not in raw and "activityguid" not in raw:
            inner = raw.get("WorkflowActivity") or {}
            ops = raw.get("WorkflowActivityOperation") or []
            if not isinstance(inner, dict):
                continue
            merged = dict(inner)
            if ops:
                merged["workflowActivityOperation"] = ops
            result.warn(p, f"activity[{i}] 仍带 WorkflowActivity 包装层，请按规范平铺为同级字段")
            parsed_activities.append((merged, f"activity[{i}]"))
        else:
            parsed_activities.append((raw, f"activity[{i}]"))

    # ============================================================
    # 红线 1：必含 5 类节点
    # ============================================================
    activity_guids: set[str] = set()
    process_version_guids: set[str] = set()
    type_count = {10: 0, 20: 0, 30: 0, 40: 0, 90: 0, 100: 0}
    start_acts: list[dict] = []
    end_acts: list[dict] = []
    apply_acts: list[dict] = []  # 申请节点：activitytype=30 + name == '申请'
    approve_acts: list[dict] = []  # 普通审批节点：activitytype=30 + name != '申请'
    route_acts: list[dict] = []
    subprocess_acts: list[dict] = []
    browse_acts: list[dict] = []
    vmlid_seen: dict[int, str] = {}
    coord_seen: dict[tuple[object, object], str] = {}
    custom_design_operation_count = 0

    for act, owner in parsed_activities:
        atype = act.get("activitytype", act.get("activityType"))
        aname = act.get("activityname") or act.get("activityname") or ""
        aguid = act.get("activityguid") or act.get("activityguid")
        avml = act.get("vmlid", act.get("vmlId"))
        apvg = act.get("processversionguid") or act.get("processversionguid")

        if aguid:
            if aguid in activity_guids:
                result.err(p, f"{owner} activityguid 重复: {aguid}")
            activity_guids.add(aguid)
        else:
            result.err(p, f"{owner} 缺少 activityguid")

        if apvg:
            process_version_guids.add(apvg)

        if atype not in (10, 20, 30, 40, 50, 90, 100, 110):
            result.err(p, f"{owner} activitytype '{atype}' 不在合法枚举 [10/20/30/40/50/90/100/110]")
        else:
            if atype in type_count:
                type_count[atype] += 1
            if atype == 10:
                start_acts.append(act)
            elif atype == 20:
                end_acts.append(act)
            elif atype == 100:
                browse_acts.append(act)
            elif atype == 40:
                route_acts.append(act)
            elif atype == 90:
                subprocess_acts.append(act)
            elif atype == 30:
                if aname == "申请":
                    apply_acts.append(act)
                else:
                    approve_acts.append(act)

            actual_splittype = act.get("splittype")
            expected_splittype = default_splittype(atype)
            if actual_splittype != expected_splittype:
                result.warn(
                    p,
                    f"{owner}.splittype 应按 activitytype={atype} 默认为 {expected_splittype!r}，"
                    f"实际 {actual_splittype!r}",
                )

        coord = (act.get("iconx"), act.get("icony"))
        if coord[0] is not None and coord[1] is not None:
            if coord in coord_seen:
                result.warn(
                    p,
                    f"{owner} 坐标 iconx/icony={coord!r} 与 {coord_seen[coord]} 重复，"
                    "横向布局下建议避免活动节点重叠",
                )
            else:
                coord_seen[coord] = owner

        if atype == 100 and coord != (FLOW_BROWSE_ICON_X, FLOW_BROWSE_ICON_Y):
            result.warn(
                p,
                f"{owner} 是浏览节点（activitytype=100），建议坐标为 "
                f"iconx='{FLOW_BROWSE_ICON_X}', icony='{FLOW_BROWSE_ICON_Y}'，实际 {coord!r}",
            )

        if avml is not None:
            try:
                avml_int = int(avml)
            except (TypeError, ValueError):
                result.err(p, f"{owner} vmlid '{avml}' 不是整数")
            else:
                if avml_int in vmlid_seen:
                    result.err(p, f"{owner} vmlid={avml_int} 重复（已被 {vmlid_seen[avml_int]} 占用）")
                else:
                    vmlid_seen[avml_int] = owner

        ops = act.get("workflowActivityOperation") or act.get("WorkflowActivityOperation") or []
        if isinstance(ops, list):
            for j, op in enumerate(ops):
                if not isinstance(op, dict):
                    continue
                otype = op.get("operationtype", op.get("operationType"))
                if otype == 80:
                    custom_design_operation_count += 1
                actual_check = op.get("is_checkmaterialsubmit")
                if actual_check != DEFAULT_IS_CHECKMATERIALSUBMIT:
                    result.warn(
                        p,
                        f"{owner}.operations[{j}].is_checkmaterialsubmit 默认应为 "
                        f"{DEFAULT_IS_CHECKMATERIALSUBMIT}，实际 {actual_check!r}",
                    )
                actual_visible_case = op.get("operationvisiablecase")
                expected_visible_case = default_operationvisiablecase(otype)
                if actual_visible_case != expected_visible_case:
                    result.warn(
                        p,
                        f"{owner}.operations[{j}].operationvisiablecase 应按 operationtype={otype} "
                        f"默认为 '{expected_visible_case}'，实际 {actual_visible_case!r}",
                    )

        if atype == 40:
            jointype = act.get("jointype", act.get("joinType"))
            if jointype == 40 and not (act.get("joinmethodguid") or act.get("joinMethodGuid")):
                result.err(p, f"{owner} 是自定义会合路由节点（activitytype=40/jointype=40），必须配置 joinmethodguid")
            if ops:
                result.warn(p, f"{owner} 是路由节点（activitytype=40），通常不应配置 workflowActivityOperation 按钮")

        if atype == 90:
            if not (act.get("callsubprocessguid") or act.get("callSubProcessGuid")):
                result.err(p, f"{owner} 是子流程节点（activitytype=90），必须配置 callsubprocessguid")
            if act.get("subprocesssynctype", act.get("subprocessSyncType")) not in (10, 20):
                result.err(p, f"{owner} 是子流程节点（activitytype=90），subprocesssynctype 必须为 10(异步) 或 20(同步)")

    # 红线 1：5 类节点完整性
    if type_count[10] == 0:
        result.err(p, "缺少开始节点（activitytype: 10）")
    if type_count[10] > 1:
        result.err(p, f"开始节点（activitytype: 10）只能有 1 个，当前 {type_count[10]} 个")
    if type_count[20] == 0:
        result.err(p, "缺少结束节点（activitytype: 20）")
    if type_count[20] > 1:
        result.err(p, f"结束节点（activitytype: 20）只能有 1 个，当前 {type_count[20]} 个")
    if not apply_acts:
        result.err(p, "缺少申请节点（activitytype: 30 且 activityname: 申请），按规范申请节点必须独立于开始节点")
    if not approve_acts:
        result.err(p, "缺少审批节点（activitytype: 30，activityname 不为'申请'），至少 1 个")
    if not browse_acts:
        result.err(p, "缺少浏览节点（activitytype: 100），按规范必须有 1 个浏览节点")
    if len(browse_acts) > 1:
        result.warn(p, f"浏览节点（activitytype: 100）建议只有 1 个，当前 {len(browse_acts)} 个")

    # 红线 3：开始/结束节点名称固定
    for act in start_acts:
        name = act.get("activityname") or act.get("activityname") or ""
        if name != "开始":
            result.err(p, f"开始节点 activityname 必须为 '开始'，实际 '{name}'")
    for act in end_acts:
        name = act.get("activityname") or act.get("activityname") or ""
        if name != "结束":
            result.err(p, f"结束节点 activityname 必须为 '结束'，实际 '{name}'")

    # 红线 4：开始/结束/浏览节点的"应为空"字段
    def _is_empty(value) -> bool:
        return value is None or value == "" or value == "null"

    def _to_int_or_none(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    must_empty_fields = {
        "handleurl": ("handleurl", "handleUrl"),
        "mobilehandleurl": ("mobilehandleurl", "mobileHandleURL", "mobilehandleUrl"),
        "multitransactormode": ("multitransactormode", "multiTransactorMode"),
        "earlywarning_enable": ("earlywarning_enable", "earlyWarning_enable", "earlyWarningEnable"),
        "isallowaddattachfile": ("isallowaddattachfile", "isAllowAddAttachFile"),
        "timelimitenable": ("timelimitenable", "timeLimitEnable"),
        "is_passwhennotransactor": ("is_passwhennotransactor", "isPassWhenNoTransactor"),
    }
    for label, acts in (("开始", start_acts), ("结束", end_acts)):
        for act in acts:
            for canon, candidates in must_empty_fields.items():
                actual_value = None
                for k in candidates:
                    if k in act:
                        actual_value = act[k]
                        break
                if not _is_empty(actual_value):
                    result.err(
                        p,
                        f"{label}节点 {canon} 应为空（按规范），实际 '{actual_value}'",
                    )
    # 浏览节点：除 handleurl/mobilehandleurl 外其余应为空
    for act in browse_acts:
        for canon, candidates in must_empty_fields.items():
            if canon in ("handleurl", "mobilehandleurl"):
                continue
            actual_value = None
            for k in candidates:
                if k in act:
                    actual_value = act[k]
                    break
            if not _is_empty(actual_value):
                result.warn(
                    p,
                    f"浏览节点 {canon} 建议为空（按规范），实际 '{actual_value}'",
                )

    # ============================================================
    # handleurl 风格 warn：activitytype=30 用 add，activitytype=100 用 detail，
    # 其他 activitytype 必须为空。
    # ============================================================
    for act, owner in parsed_activities:
        if not isinstance(act, dict):
            continue
        atype = _to_int_or_none(act.get("activitytype", act.get("activityType")))
        expected_mode = HANDLE_URL_ACTIVITY_TYPES.get(atype)
        for field in ("handleurl", "mobilehandleurl"):
            url = act.get(field)
            if expected_mode is None:
                if not _is_empty(url):
                    result.warn(
                        p,
                        f"{owner} activitytype={atype} 的 {field} 应为空，实际 {url!r}",
                    )
                continue
            expected_prefix = f"{WORKFLOW_RENDERER_PREFIX}/{expected_mode}?pagetag="
            if _is_empty(url):
                result.warn(
                    p,
                    f"{owner} activitytype={atype} 的 {field} 为空，建议使用 '{expected_prefix}<pagetag>'",
                )
            elif url == "[#=FirstMaterialUrl#]":
                result.warn(
                    p,
                    f"{owner} 的 {field}='[#=FirstMaterialUrl#]' 已废弃，"
                    f"activitytype={atype} 应使用 '{expected_prefix}<pagetag>'",
                )
            elif not isinstance(url, str) or not url.startswith(expected_prefix):
                result.warn(
                    p,
                    f"{owner} activitytype={atype} 的 {field} 应使用 "
                    f"'{expected_prefix}<pagetag>'，实际 {url!r}",
                )

    # ============================================================
    # 红线 2：开始 != 申请（同一节点不能既是 10 又是 30）
    # 通过 type_count 已隐含；这里再校验"开始节点不应绑定表单/handleurl"
    # ============================================================
    for act in start_acts:
        ops = act.get("workflowActivityOperation") or act.get("WorkflowActivityOperation") or []
        # 开始节点的按钮也允许，但不应有 operationtype=30 退回按钮
        for op in ops:
            if not isinstance(op, dict):
                continue
            if op.get("operationtype") == 30 or op.get("operationType") == 30:
                result.err(p, "开始节点不应有退回按钮（operationtype=30）")

    # ============================================================
    # 红线 5：processversionguid 一致性
    # ============================================================
    pversion_obj = (
        version.get("workflowProcessVersion")
        or version.get("WorkflowProcessVersion")
        or {}
    )
    process_version_guid = (
        pversion_obj.get("processversionguid")
        if isinstance(pversion_obj, dict)
        else None
    ) or (
        pversion_obj.get("processversionguid")
        if isinstance(pversion_obj, dict)
        else None
    )

    if process_version_guid:
        process_version_guids.add(process_version_guid)
    if len(process_version_guids) > 1:
        result.err(
            p,
            f"processversionguid 在不同节点上不一致，发现 {len(process_version_guids)} 个: "
            f"{sorted(process_version_guids)}",
        )

    # workflowProcessVersion.processguid 与 workflowProcess.processguid 一致
    pv_process_guid = (
        pversion_obj.get("processguid")
        if isinstance(pversion_obj, dict)
        else None
    ) or (
        pversion_obj.get("processguid")
        if isinstance(pversion_obj, dict)
        else None
    )
    if process_guid and pv_process_guid and pv_process_guid != process_guid:
        result.err(
            p,
            f"workflowProcessVersion.processguid '{pv_process_guid}' 与 "
            f"workflowProcess.processguid '{process_guid}' 不一致",
        )

    # ============================================================
    # 红线 6：退回按钮 ↔ workflowConfig 闭环
    # ============================================================
    reject_op_guids: set[str] = set()
    for act, owner in parsed_activities:
        ops = act.get("workflowActivityOperation") or act.get("WorkflowActivityOperation") or []
        for j, op in enumerate(ops):
            if not isinstance(op, dict):
                continue
            otype = op.get("operationtype", op.get("operationType"))
            oguid = op.get("operationguid") or op.get("operationguid")
            if otype == 30 and oguid:
                reject_op_guids.add(oguid)
                # 退回按钮的关键字段
                if not (op.get("targetactivity") or op.get("targetActivity")):
                    result.warn(
                        p,
                        f"{owner}.operations[{j}] 退回按钮缺少 targetactivity，"
                        f"建议设为 [#=AllBeforeActivity#]",
                    )
                # multitransctormode 枚举校验：仅允许 OR / AND / OrAndRead
                mtm = op.get("multitransctormode")
                if mtm is not None and mtm not in ("OR", "AND", "OrAndRead"):
                    result.err(
                        p,
                        f"{owner}.operations[{j}] 退回按钮 multitransctormode='{mtm}' "
                        f"不在允许的集合 {{OR, AND, OrAndRead}} 中",
                    )

    config_source_guids: set[str] = set()
    if isinstance(workflow_config, list):
        for k, conf in enumerate(workflow_config):
            if not isinstance(conf, dict):
                continue
            sguid = conf.get("sourceguid") or conf.get("sourceguid")
            cname = conf.get("configname") or conf.get("configName")
            if cname == "backTargetScope" and sguid:
                config_source_guids.add(sguid)

    missing_config = reject_op_guids - config_source_guids
    if missing_config:
        result.err(
            p,
            f"以下退回按钮缺少对应 workflowConfig (belongto=22, configname=backTargetScope): "
            f"{sorted(missing_config)}",
        )
    extra_config = config_source_guids - reject_op_guids
    if extra_config:
        result.warn(
            p,
            f"以下 workflowConfig.sourceguid 找不到对应的退回按钮: {sorted(extra_config)}",
        )

    process_mode_value = process.get("isnewversion")
    if process_mode_value in (20, "20"):
        if reject_op_guids:
            result.err(p, "自由流程（isnewversion=20）不允许配置退回按钮；如需反向处理请配置反向通过按钮")
        for act, owner in parsed_activities:
            if not isinstance(act, dict):
                continue
            if act.get("multitransactormode") == 25:
                pass_when_empty = (
                    act.get("is_passwhennotransactor")
                    if "is_passwhennotransactor" in act
                    else act.get("isPassWhenNoTransactor")
                )
                if pass_when_empty != 10:
                    result.warn(p, f"{owner} 是自由流转节点（multitransactormode=25），建议设置 is_passwhennotransactor=10")

    if process_mode_value in (10, "10") and custom_design_operation_count == 0:
        result.warn(p, "自定义流程（isnewversion=10）建议至少配置 1 个 operationtype=80 的自定义流程设计按钮")

    # ============================================================
    # 红线 7：transition 引用闭合 + vmlid 唯一
    # ============================================================
    transition_vmlids: dict[int, int] = {}
    transition_entries: list[dict] = []
    for i, t in enumerate(transitions):
        if not isinstance(t, dict):
            continue
        # 兼容旧结构 WorkflowTransition 包装
        if "WorkflowTransition" in t and "transitionguid" not in t and "transitionguid" not in t:
            result.warn(p, f"transition[{i}] 仍带 WorkflowTransition 包装层，请按规范平铺")
            wt = t.get("WorkflowTransition") or {}
        else:
            wt = t

        from_g = wt.get("fromactivityguid") or wt.get("fromActivityGuid")
        to_g = wt.get("toactivityguid") or wt.get("toActivityGuid")
        tname = wt.get("transitionname") or wt.get("transitionname")
        tvml = wt.get("vmlid", wt.get("vmlId"))
        conds = wt.get("workflowTransitionCondition") or []
        if not isinstance(conds, list):
            conds = []

        transition_entries.append({
            "index": i,
            "transition": wt,
            "from": from_g,
            "to": to_g,
            "name": tname,
            "conditions": conds,
        })

        if not from_g:
            result.err(p, f"transition[{i}] 缺少 fromactivityguid")
        elif from_g not in activity_guids:
            result.err(
                p, f"transition[{i}] fromactivityguid '{from_g}' 不在活动列表",
            )
        if not to_g:
            result.err(p, f"transition[{i}] 缺少 toactivityguid")
        elif to_g not in activity_guids:
            result.err(
                p, f"transition[{i}] toactivityguid '{to_g}' 不在活动列表",
            )
        if not tname:
            result.warn(p, f"transition[{i}] 缺少 transitionname")
        if tvml is None:
            result.warn(p, f"transition[{i}] 缺少 vmlid（规范要求 ≥2）")
        else:
            try:
                tvml_int = int(tvml)
                if tvml_int < 2:
                    result.warn(p, f"transition[{i}] vmlid={tvml_int} 应 ≥2")
                if tvml_int in transition_vmlids:
                    result.err(p, f"transition[{i}] vmlid={tvml_int} 重复")
                else:
                    transition_vmlids[tvml_int] = i
            except (TypeError, ValueError):
                result.err(p, f"transition[{i}] vmlid '{tvml}' 不是整数")

        if conds and wt.get("is_default") == 10:
            result.warn_strict_error(
                p,
                f"transition[{i}] '{tname}' 已配置 workflowTransitionCondition，"
                "is_default 不应为 10；条件分支请使用显式互斥条件，is_default=20",
            )

        # 字段命名规范化：旧驼峰 → 下划线（现行规范已统一）
        legacy_to_snake = {
            "isTargetTransactorEditable": "is_targettransactor_editable",
            "isShowAsOperationButton": "is_showasoperationbutton",
        }
        for legacy_key, snake_key in legacy_to_snake.items():
            if legacy_key in wt and snake_key not in wt:
                result.warn(
                    p,
                    f"transition[{i}] 字段 '{legacy_key}' 是旧驼峰命名，"
                    f"现行规范已统一为 '{snake_key}'，请改名",
                )

    # 流转必须从开始 → 申请 → ... → 结束（不能跳过申请节点）
    start_guids = {a.get("activityguid") or a.get("activityguid") for a in start_acts}
    apply_guids = {a.get("activityguid") or a.get("activityguid") for a in apply_acts}
    has_start_to_apply = False
    for t in transitions:
        if not isinstance(t, dict):
            continue
        wt = t.get("WorkflowTransition") if "WorkflowTransition" in t else t
        if not isinstance(wt, dict):
            continue
        from_g = wt.get("fromactivityguid") or wt.get("fromActivityGuid")
        to_g = wt.get("toactivityguid") or wt.get("toActivityGuid")
        if from_g in start_guids and to_g in apply_guids:
            has_start_to_apply = True
            break
    if start_guids and apply_guids and not has_start_to_apply:
        result.err(
            p,
            "流转必须为：开始(10) → 申请(30) → ... → 结束(20)，"
            "未发现从开始节点到申请节点的 transition",
        )

    # 主线横向布局：从开始节点沿 transition 追踪到结束节点，检查 x 坐标严格递增
    # 且相邻节点满足动态间距，避免设计器卡片重叠。
    def _activity_guid(act: dict) -> str | None:
        return act.get("activityguid") or act.get("activityGuid")

    def _activity_name(act: dict) -> str:
        return act.get("activityname") or act.get("activityName") or ""

    def _activity_type(act: dict) -> int | None:
        return _to_int_or_none(act.get("activitytype", act.get("activityType")))

    def _iconx_as_int(act: dict) -> int | None:
        raw = act.get("iconx", act.get("iconX"))
        try:
            return int(raw)
        except (TypeError, ValueError):
            try:
                value = float(raw)
            except (TypeError, ValueError):
                return None
            return int(value) if value.is_integer() else None

    def _icony_as_str(act: dict) -> str | None:
        raw = act.get("icony", act.get("iconY"))
        if raw is None:
            return None
        return str(raw)

    guid_to_act = {
        guid: act
        for act, _owner in parsed_activities
        if isinstance(act, dict) and (guid := _activity_guid(act))
    }
    outgoing: dict[str, list[str]] = {}
    outgoing_transition_entries: dict[str, list[dict]] = {}
    edge_set: set[tuple[str, str]] = set()
    for t in transitions:
        if not isinstance(t, dict):
            continue
        wt = t.get("WorkflowTransition") if "WorkflowTransition" in t else t
        if not isinstance(wt, dict):
            continue
        from_g = wt.get("fromactivityguid") or wt.get("fromActivityGuid")
        to_g = wt.get("toactivityguid") or wt.get("toActivityGuid")
        if from_g and to_g:
            outgoing.setdefault(from_g, []).append(to_g)
            edge_set.add((from_g, to_g))
    for entry in transition_entries:
        from_g = entry.get("from")
        if from_g:
            outgoing_transition_entries.setdefault(from_g, []).append(entry)

    for from_g, siblings in outgoing_transition_entries.items():
        if len(siblings) <= 1:
            continue
        has_any_condition = any(entry.get("conditions") for entry in siblings)
        if not has_any_condition:
            continue
        source_name = _activity_name(guid_to_act.get(from_g, {})) or from_g
        for entry in siblings:
            if entry.get("conditions"):
                continue
            target_name = _activity_name(guid_to_act.get(entry.get("to"), {})) or entry.get("to")
            result.warn_strict_error(
                p,
                f"源活动 '{source_name}' 存在条件分支，但 transition[{entry.get('index')}] "
                f"'{entry.get('name')}' → '{target_name}' 未配置 workflowTransitionCondition；"
                "“否则/不满足条件”请生成显式互补条件，不要只依赖默认变迁",
            )

    branch_detours: set[tuple[str, str, str]] = set()
    for source_guid, targets in outgoing.items():
        for branch_guid in targets:
            if branch_guid not in guid_to_act:
                continue
            if _activity_type(guid_to_act.get(branch_guid, {})) == 100:
                continue
            for merge_guid in outgoing.get(branch_guid, []):
                if merge_guid == branch_guid:
                    continue
                if (source_guid, merge_guid) in edge_set:
                    branch_detours.add((source_guid, branch_guid, merge_guid))

    for source_guid, branch_guid, merge_guid in sorted(branch_detours):
        source_act = guid_to_act.get(source_guid, {})
        branch_act = guid_to_act.get(branch_guid, {})
        merge_act = guid_to_act.get(merge_guid, {})
        source_name = _activity_name(source_act) or source_guid
        branch_name = _activity_name(branch_act) or branch_guid
        merge_name = _activity_name(merge_act) or merge_guid

        if _icony_as_str(branch_act) != FLOW_BRANCH_ICON_Y:
            result.warn_strict_error(
                p,
                f"可选分支节点 '{branch_name}' 位于 '{source_name}' → '{merge_name}' 分支中，"
                f"icony 建议为 '{FLOW_BRANCH_ICON_Y}'，实际 {branch_act.get('icony')!r}",
            )

        source_x = _iconx_as_int(source_act)
        branch_x = _iconx_as_int(branch_act)
        merge_x = _iconx_as_int(merge_act)
        if source_x is None or branch_x is None or merge_x is None:
            result.warn_strict_error(
                p,
                f"可选分支 '{source_name}' → '{branch_name}' → '{merge_name}' "
                "存在无法解析为整数的 iconx，无法校验分支布局",
            )
            continue
        if not (source_x < branch_x < merge_x):
            result.warn_strict_error(
                p,
                f"可选分支节点 '{branch_name}' 的 iconx={branch_x} 应位于源节点 "
                f"'{source_name}' iconx={source_x} 与汇合节点 '{merge_name}' iconx={merge_x} 之间",
            )
        min_direct_step = max(
            FLOW_MIN_STEP_X * 2,
            flow_step_after(_activity_type(source_act), _activity_name(source_act))
            + flow_step_after(_activity_type(branch_act), _activity_name(branch_act)),
        )
        actual_direct_step = merge_x - source_x
        if actual_direct_step < min_direct_step:
            result.warn_strict_error(
                p,
                f"可选分支 '{source_name}' → '{merge_name}' 横向距离为 {actual_direct_step}px，"
                f"小于分支布局建议 {min_direct_step}px，可能导致分支线和节点拥挤",
            )

    if start_acts and end_acts:
        main_flow_acts: list[dict] = []
        current_guid = _activity_guid(start_acts[0])
        seen_guids: set[str] = set()
        while current_guid and current_guid not in seen_guids:
            seen_guids.add(current_guid)
            next_guids = [
                guid for guid in outgoing.get(current_guid, [])
                if _activity_type(guid_to_act.get(guid, {})) != 100
            ]
            if not next_guids:
                break
            next_guid = next_guids[0]
            next_act = guid_to_act.get(next_guid)
            if not next_act:
                break
            main_flow_acts.append(next_act)
            if _activity_type(next_act) == 20:
                break
            current_guid = next_guid

        if main_flow_acts:
            first_x = _iconx_as_int(main_flow_acts[0])
            if first_x != FLOW_FIRST_ACTIVITY_ICON_X:
                result.warn(
                    p,
                    f"首个主线活动 '{_activity_name(main_flow_acts[0])}' 的 iconx 建议为 "
                    f"'{FLOW_FIRST_ACTIVITY_ICON_X}'，实际 {main_flow_acts[0].get('iconx')!r}",
                )
        for prev_act, curr_act in zip(main_flow_acts, main_flow_acts[1:]):
            prev_x = _iconx_as_int(prev_act)
            curr_x = _iconx_as_int(curr_act)
            if prev_x is None or curr_x is None:
                result.warn(
                    p,
                    f"主线节点 '{_activity_name(prev_act)}' 或 '{_activity_name(curr_act)}' 的 iconx "
                    "无法按整数坐标校验动态布局",
                )
                continue
            if curr_x <= prev_x:
                result.warn(
                    p,
                    f"主线节点 '{_activity_name(curr_act)}' 的 iconx={curr_x} 未大于前序节点 "
                    f"'{_activity_name(prev_act)}' 的 iconx={prev_x}",
                )
                continue
            expected_step = flow_step_after(_activity_type(prev_act), _activity_name(prev_act))
            actual_step = curr_x - prev_x
            if actual_step < expected_step:
                result.warn(
                    p,
                    f"主线节点 '{_activity_name(prev_act)}' → '{_activity_name(curr_act)}' "
                    f"横向间距为 {actual_step}px，小于动态布局建议 {expected_step}px，可能导致设计器卡片重叠",
                )

    # ============================================================
    # workflowPvMaterial / workflowPvMisTableSet 1:1 关系
    # ============================================================
    if not pv_material:
        result.warn(p, "缺少 workflowPvMaterial（流程版本材料），1 个流程通常需要 1 个表单")
    elif isinstance(pv_material, list):
        read_prefix = f"{WORKFLOW_RENDERER_PREFIX}/detail?pagetag="
        readwrite_prefix = f"{WORKFLOW_RENDERER_PREFIX}/add?pagetag="
        for i, material in enumerate(pv_material):
            if not isinstance(material, dict):
                continue
            page_read = material.get("pageurl_read")
            page_readwrite = material.get("pageurl_readandwrite")
            if not page_read:
                result.warn(p, f"workflowPvMaterial[{i}].pageurl_read 为空，建议使用 '{read_prefix}<pagetag>'")
            elif not isinstance(page_read, str) or not page_read.startswith(read_prefix):
                result.warn(
                    p,
                    f"workflowPvMaterial[{i}].pageurl_read 应使用详情页地址 '{read_prefix}<pagetag>'，"
                    f"实际 {page_read!r}",
                )
            if not page_readwrite:
                result.warn(
                    p,
                    f"workflowPvMaterial[{i}].pageurl_readandwrite 为空，建议使用 '{readwrite_prefix}<pagetag>'",
                )
            elif not isinstance(page_readwrite, str) or not page_readwrite.startswith(readwrite_prefix):
                result.warn(
                    p,
                    f"workflowPvMaterial[{i}].pageurl_readandwrite 应使用读写页地址 '{readwrite_prefix}<pagetag>'，"
                    f"实际 {page_readwrite!r}",
                )
        material_guids = {
            (m.get("materialguid") or m.get("materialguid"))
            for m in pv_material
            if isinstance(m, dict)
        }
        material_guids.discard(None)
        if pv_mistableset and isinstance(pv_mistableset, list):
            ts_material_guids = {
                (m.get("materialguid") or m.get("materialguid"))
                for m in pv_mistableset
                if isinstance(m, dict)
            }
            ts_material_guids.discard(None)
            for mg in material_guids:
                if mg not in ts_material_guids:
                    result.warn(
                        p,
                        f"workflowPvMaterial.materialguid={mg} 没有对应的 workflowPvMisTableSet",
                    )

    # ============================================================
    # 字段类型校验（防止数字/字符串混淆）
    # ============================================================

    # spec v2: workflowPvMisTableSet.tableid 已废弃（deprecation warn 在末尾统一处理）

    # --- activity 字段类型校验（字符串 vs 整数） ---
    for act, owner in parsed_activities:
        # iconx/icony 必须是字符串
        for coord_key in ("iconx", "icony"):
            val = act.get(coord_key)
            if val is not None and not isinstance(val, str):
                result.warn(
                    p,
                    f"{owner}.{coord_key} 应为字符串（如 '-159'），"
                    f"实际类型 {type(val).__name__}，可能导致设计器渲染异常",
                )
        # multitransactormode / isallowaddattachfile / timelimitenable / earlywarning_enable 非 null 时必须是整数
        for int_key in ("multitransactormode", "isallowaddattachfile", "timelimitenable",
                         "earlywarning_enable", "is_passwhennotransactor"):
            val = act.get(int_key)
            if val is not None and isinstance(val, str) and val not in ("", "null"):
                result.warn(
                    p,
                    f"{owner}.{int_key} 应为整数（如 10），"
                    f"实际是字符串 '{val}'，可能导致解析异常",
                )
        # operationvisiablecase / backtargetscope / nopasshandlevalue 必须是字符串
        for str_key in ("nopasshandlevalue",):
            val = act.get(str_key)
            if val is not None and isinstance(val, int):
                result.warn(
                    p,
                    f"{owner}.{str_key} 应为字符串（如 '10'），"
                    f"实际是整数 {val}",
                )
        # 按钮字段类型校验
        ops = act.get("workflowActivityOperation") or act.get("WorkflowActivityOperation") or []
        for j, op in enumerate(ops):
            if not isinstance(op, dict):
                continue
            for str_key_op in ("operationvisiablecase", "backtargetscope"):
                val = op.get(str_key_op)
                if val is not None and isinstance(val, int):
                    result.warn(
                        p,
                        f"{owner}.operations[{j}].{str_key_op} 应为字符串（如 '10'），"
                        f"实际是整数 {val}",
                    )

    # --- workflowProcess 字段类型校验 ---
    tag_val = process.get("tag")
    if tag_val is not None and isinstance(tag_val, int):
        result.warn(p, f"workflowProcess.tag 应为字符串（如 '20'），实际是整数 {tag_val}")

    # --- workflowProcessVersion 字段类型和值域校验 ---
    if isinstance(pversion_obj, dict):
        dir_val = pversion_obj.get("direction")
        if dir_val is not None and isinstance(dir_val, int):
            result.warn(p, f"workflowProcessVersion.direction 应为字符串（如 '90'），实际是整数 {dir_val}")

        # 工作流扩展字段值域校验
        revoke_opt = pversion_obj.get("revokeoption")
        if revoke_opt is not None and revoke_opt not in (10, 20, 30, 40):
            result.warn(p, f"workflowProcessVersion.revokeoption={revoke_opt} 不在合法值域 {{10,20,30,40}}")
        no_part = pversion_obj.get("noparticipatoroption")
        if no_part is not None and no_part not in (10, 20, 30):
            result.warn(p, f"workflowProcessVersion.noparticipatoroption={no_part} 不在合法值域 {{10,20,30}}")
        show_line = pversion_obj.get("isshowlinegraph")
        if show_line is not None and show_line not in ("Normal", "Orthogonal"):
            result.warn(p, f"workflowProcessVersion.isshowlinegraph='{show_line}' 不在合法值域 {{Normal, Orthogonal}}")
        show_node = pversion_obj.get("isshownodesimple")
        if show_node is not None and show_node not in ("details", "simple"):
            result.warn(p, f"workflowProcessVersion.isshownodesimple='{show_node}' 不在合法值域 {{details, simple}}")
        revoke_remind = pversion_obj.get("revokeremindoption")
        if revoke_remind is not None and revoke_remind not in (10, 20):
            result.warn(p, f"workflowProcessVersion.revokeremindoption={revoke_remind} 不在合法值域 {{10,20}}")

    # --- transition 字段类型校验 ---
    for i, t in enumerate(transitions):
        if not isinstance(t, dict):
            continue
        wt = t.get("WorkflowTransition") if "WorkflowTransition" in t else t
        if not isinstance(wt, dict):
            continue
        for int_key_t in ("is_sendtomessagecenter", "priority", "type",
                          "targetactivitytransactorsource", "is_targettransactor_editable",
                          "is_default", "is_showasoperationbutton"):
            val = wt.get(int_key_t)
            if val is not None and isinstance(val, str) and val not in ("", "null"):
                result.warn(
                    p,
                    f"transition[{i}].{int_key_t} 应为整数，实际是字符串 '{val}'",
                )

    # ============================================================
    # 工作流扩展节点校验：method / workflowEvent / workflowContext /
    #                  workflowTransitionCondition
    # ============================================================

    # --- method 引用闭合 ---
    methods = version.get("method") or []
    method_guids: set[str] = set()
    if isinstance(methods, list):
        for i, m in enumerate(methods):
            if not isinstance(m, dict):
                continue
            mg = m.get("methodguid") or m.get("methodguid")
            if mg:
                method_guids.add(mg)
            else:
                result.warn(p, f"method[{i}] 缺少 methodguid")
            mpvg = m.get("processversionguid") or m.get("processversionguid")
            if mpvg:
                process_version_guids.add(mpvg)

    # --- workflowEvent 引用闭合 ---
    events = version.get("workflowEvent") or []
    if isinstance(events, list):
        for i, evt in enumerate(events):
            if not isinstance(evt, dict):
                continue
            emg = evt.get("eventmethodguid") or evt.get("eventmethodguid")
            rule_guid = evt.get("ruleguid") or evt.get("ruleguid")
            if not emg and not rule_guid:
                result.warn(p, f"workflowEvent[{i}] 建议至少配置 eventmethodguid 或 ruleguid 之一")
            if emg and method_guids and emg not in method_guids:
                result.warn(
                    p,
                    f"workflowEvent[{i}].eventmethodguid '{emg}' "
                    f"不在已定义的 method 列表中",
                )
            sg = evt.get("sourceguid") or evt.get("sourceguid")
            bt = evt.get("belongto") or evt.get("belongto")
            if bt == 20 and sg and sg not in activity_guids:
                result.warn(
                    p,
                    f"workflowEvent[{i}].sourceguid '{sg}' "
                    f"(belongto=20 活动实例事件) 不在活动列表中",
                )
            epvg = evt.get("processversionguid") or evt.get("processversionguid")
            if epvg:
                process_version_guids.add(epvg)

    # --- workflowContext 引用闭合 ---
    contexts = version.get("workflowContext") or []
    if isinstance(contexts, list):
        material_guid_set = set()
        if isinstance(pv_material, list):
            for m in pv_material:
                if isinstance(m, dict):
                    mg_ = m.get("materialguid") or m.get("materialguid")
                    if mg_:
                        material_guid_set.add(mg_)
        sqltablenames_for_ctx = set()
        if isinstance(pv_mistableset, list):
            for ts in pv_mistableset:
                if isinstance(ts, dict):
                    stn = ts.get("sql_tablename")
                    if stn:
                        sqltablenames_for_ctx.add(stn)
        for i, ctx in enumerate(contexts):
            if not isinstance(ctx, dict):
                continue
            vs = ctx.get("valuesource") or ctx.get("valuesource")
            fmg = ctx.get("frommaterialguid") or ctx.get("frommaterialguid")
            # spec v2: valuesource=30 时必填 frommaterialguid / fromsqltablename / fromfieldname
            if vs == 30:
                missing = []
                if not fmg:
                    missing.append("frommaterialguid")
                if not ctx.get("fromsqltablename"):
                    missing.append("fromsqltablename")
                if not ctx.get("fromfieldname"):
                    missing.append("fromfieldname")
                if missing:
                    result.err(
                        p,
                        f"workflowContext[{i}] valuesource=30（表单字段）必须填 {', '.join(missing)}（spec v2 必填项）",
                    )
                # fromsqltablename 必须能在 workflowPvMisTableSet 中找到
                fst = ctx.get("fromsqltablename")
                if fst and sqltablenames_for_ctx and fst not in sqltablenames_for_ctx:
                    result.warn(
                        p,
                        f"workflowContext[{i}].fromsqltablename '{fst}' "
                        f"在 workflowPvMisTableSet.sql_tablename 中找不到匹配",
                    )
            if vs == 30 and fmg and material_guid_set and fmg not in material_guid_set:
                result.warn(
                    p,
                    f"workflowContext[{i}].frommaterialguid '{fmg}' "
                    f"不在 workflowPvMaterial 列表中",
                )
            cpvg = ctx.get("processversionguid") or ctx.get("processversionguid")
            if cpvg:
                process_version_guids.add(cpvg)

    # --- workflowTransitionCondition 引用闭合 ---
    transition_guid_set: set[str] = set()
    for t in transitions:
        if not isinstance(t, dict):
            continue
        wt = t.get("WorkflowTransition") if "WorkflowTransition" in t else t
        if not isinstance(wt, dict):
            continue
        tg = wt.get("transitionguid") or wt.get("transitionguid")
        if tg:
            transition_guid_set.add(tg)
        # 校验 transition 内嵌的条件
        conds = wt.get("workflowTransitionCondition") or []
        if isinstance(conds, dict):
            conds = [conds]  # 兼容单个对象而非数组
        if isinstance(conds, list):
            indexed_single_conditions = [
                (ci, condition)
                for ci, condition in enumerate(conds)
                if isinstance(condition, dict) and condition_expression_type(condition) == 10
            ]
            single_condition_count = len([
                condition
                for _, condition in sorted(indexed_single_conditions, key=condition_sort_key)
            ])
            for j, cond in enumerate(conds):
                if not isinstance(cond, dict):
                    continue
                ctg = cond.get("transitionguid") or cond.get("transitionguid")
                if ctg and tg and ctg != tg:
                    result.err(
                        p,
                        f"transition.workflowTransitionCondition[{j}].transitionguid "
                        f"'{ctg}' 与所属变迁 '{tg}' 不一致",
                    )
                cet = condition_expression_type(cond)
                if cet is None:
                    result.err(p, f"workflowTransitionCondition[{j}] conditionexpressiontype 必须是 10/20/30")
                    continue
                if cet == 10:
                    for required_key in ("leftvalue", "compareoperation", "rightvalue", "valuetype"):
                        if cond.get(required_key) in (None, ""):
                            result.err(
                                p,
                                f"workflowTransitionCondition[{j}] conditionexpressiontype=10 缺少 {required_key}",
                            )
                    lv = cond.get("leftvalue")
                    if isinstance(lv, str) and lv and BARE_FIELD_RE.match(lv) and "[#=" not in lv:
                        result.err(
                            p,
                            f"workflowTransitionCondition[{j}].leftvalue='{lv}' "
                            f"缺少工作流占位符格式 [#=...#]；正确写法应为 '[#={lv}#]'",
                        )
                elif cet == 20:
                    expression = cond.get("conditionexpression")
                    if not expression:
                        result.err(p, f"workflowTransitionCondition[{j}] conditionexpressiontype=20 缺少 conditionexpression")
                    else:
                        expression_error = validate_condition_expression_text(str(expression), single_condition_count)
                        if expression_error:
                            result.err(p, f"workflowTransitionCondition[{j}] {expression_error}")
                elif cet == 30:
                    cmg = cond.get("methodguid") or cond.get("methodguid")
                    crg = cond.get("ruleguid") or cond.get("ruleguid")
                    if not cmg and not crg:
                        result.err(
                            p,
                            f"workflowTransitionCondition[{j}] conditionexpressiontype=30 必须配置 methodguid 或 ruleguid",
                        )
                    if cmg and method_guids and cmg not in method_guids:
                        result.warn(
                            p,
                            f"workflowTransitionCondition.methodguid '{cmg}' "
                            f"不在已定义的 method 列表中",
                        )
                else:
                    result.err(
                        p,
                        f"workflowTransitionCondition[{j}] conditionexpressiontype={cet} 不支持（仅支持 10/20/30）",
                    )
                cpvg = cond.get("processversionguid") or cond.get("processversionguid")
                if cpvg:
                    process_version_guids.add(cpvg)

    # 重新校验 processversionguid 一致性（含工作流扩展节点）
    if len(process_version_guids) > 1:
        result.err(
            p,
            f"processversionguid 在不同节点上不一致（含工作流扩展节点），"
            f"发现 {len(process_version_guids)} 个: {sorted(process_version_guids)}",
        )

    # ============================================================
    # 字段白名单 schema 强校验（防字段名幻觉，如 contextguid/contextname/contexttext）
    # 数据源：field_schema.WORKFLOW_NODE_SCHEMAS（与 references/workflow/工作流/基础骨架/ 字段表对齐）
    # 命中别名/缺必填 → error；未知字段 → warn（--strict 升 error）
    # ============================================================
    if isinstance(process, dict) and process:
        apply_node_schema(result, p, "workflowProcess", process, "workflowProcess")

    for act, owner in parsed_activities:
        apply_node_schema(result, p, owner, act, "activity")
        for j, op in enumerate(act.get("workflowActivityOperation") or []):
            if isinstance(op, dict):
                apply_node_schema(
                    result, p, f"{owner}.workflowActivityOperation[{j}]", op,
                    "workflowActivityOperation",
                )
        for j, am in enumerate(act.get("workflowActivityMaterial") or []):
            if isinstance(am, dict):
                apply_node_schema(
                    result, p, f"{owner}.workflowActivityMaterial[{j}]", am,
                    "workflowActivityMaterial",
                )
                for k, fa in enumerate(am.get("workflowActivityFieldAccess") or []):
                    if isinstance(fa, dict):
                        apply_node_schema(
                            result, p,
                            f"{owner}.workflowActivityMaterial[{j}].workflowActivityFieldAccess[{k}]",
                            fa, "workflowActivityFieldAccess",
                        )

    for i, cfg in enumerate(workflow_config if isinstance(workflow_config, list) else []):
        if isinstance(cfg, dict):
            apply_node_schema(result, p, f"workflowConfig[{i}]", cfg, "workflowConfig")
    for i, mat in enumerate(pv_material if isinstance(pv_material, list) else []):
        if isinstance(mat, dict):
            apply_node_schema(result, p, f"workflowPvMaterial[{i}]", mat, "workflowPvMaterial")
    for i, ts in enumerate(pv_mistableset if isinstance(pv_mistableset, list) else []):
        if isinstance(ts, dict):
            apply_node_schema(result, p, f"workflowPvMisTableSet[{i}]", ts, "workflowPvMisTableSet")
    for i, m in enumerate(methods if isinstance(methods, list) else []):
        if isinstance(m, dict):
            apply_node_schema(result, p, f"method[{i}]", m, "method")
    for i, evt in enumerate(events if isinstance(events, list) else []):
        if isinstance(evt, dict):
            apply_node_schema(result, p, f"workflowEvent[{i}]", evt, "workflowEvent")
    for i, ctx in enumerate(contexts if isinstance(contexts, list) else []):
        if isinstance(ctx, dict):
            apply_node_schema(result, p, f"workflowContext[{i}]", ctx, "workflowContext")

    wpv = version.get("workflowProcessVersion") or version.get("WorkflowProcessVersion") or {}
    if isinstance(wpv, dict) and wpv:
        apply_node_schema(result, p, "workflowProcessVersion", wpv, "workflowProcessVersion")

    # transition + 内嵌流转条件 字段校验，并收集 [#=xxx#] 引用
    referenced_tokens: list[tuple[str, str]] = []  # (token, where)
    for i, t in enumerate(transitions):
        if not isinstance(t, dict):
            continue
        wt = t.get("WorkflowTransition") if isinstance(t.get("WorkflowTransition"), dict) else t
        apply_node_schema(result, p, f"transition[{i}]", wt, "transition")
        conds = wt.get("workflowTransitionCondition") or []
        if isinstance(conds, dict):
            conds = [conds]
        for j, cond in enumerate(conds if isinstance(conds, list) else []):
            if not isinstance(cond, dict):
                continue
            apply_node_schema(
                result, p, f"transition[{i}].workflowTransitionCondition[{j}]", cond,
                "workflowTransitionCondition",
            )
            for fld in ("leftvalue", "rightvalue", "conditionexpression"):
                for token in extract_placeholders(cond.get(fld)):
                    referenced_tokens.append(
                        (token, f"transition[{i}].workflowTransitionCondition[{j}].{fld}")
                    )
    # ============================================================
    # [#=xxx#] 引用闭合：流转条件引用的相关数据参数名
    # 必须在 workflowContext.fieldname 中定义（同时抓住「键名幻觉」和「fieldname 值写错」）
    # ============================================================
    context_fieldnames: set[str] = {
        ctx.get("fieldname")
        for ctx in (contexts if isinstance(contexts, list) else [])
        if isinstance(ctx, dict) and ctx.get("fieldname")
    }
    for token, where in referenced_tokens:
        if is_context_reference(token) and token not in context_fieldnames:
            result.err(
                p,
                f"{where} 引用的相关数据 [#={token}#] 未在 workflowContext.fieldname 中定义"
                f"（请在 workflowContext 新增 fieldname={token} 的参数，或核对字段名是否写错）",
            )

    # ============================================================
    # 驼峰字段 deprecation 检测（spec v2 要求统一小写下划线）
    # 默认 warn；--strict 模式下升级为 error（用 warn_strict_error 登记）。
    # ============================================================
    DEPRECATED_CAMEL = {
        # transition / 通用
        "isDefault": "is_default",
        "isPassWhenNoTransactor": "is_passwhennotransactor",
        "isLockWhenMultiTransactor": "is_lockwhenmultitransactor",
        "mobileHandleType": "mobilehandletype",
        "isAllowAddAttachFile": "isallowaddattachfile",
        "timeLimitEnable": "timelimitenable",
        "earlyWarningEnable": "earlywarning_enable",
        "earlyWarning_enable": "earlywarning_enable",
        "earlyWarningTime": "earlywarning_time",
        "earlyWarning_time": "earlywarning_time",
        "earlyWarningTimeUnit": "earlywarning_timeunit",
        "earlyWarning_timeUnit": "earlywarning_timeunit",
        "multiTransactorMode": "multitransactormode",
        "multiTransctorMode": "multitransctormode",
        "targetActivityTransactorSource": "targetactivitytransactorsource",
        "isTargetTransactorEditable": "is_targettransactor_editable",
        "isShowAsOperationButton": "is_showasoperationbutton",
        "isSendToMessageCenter": "is_sendtomessagecenter",
        "isShowNextActivity": "is_shownextactivity",
        "isRequireOpinion": "is_requireopinion",
        "isCheckMaterialSubmit": "is_checkmaterialsubmit",
        "isShowOperationPage": "is_showoperationpage",
        "operationVisiableCase": "operationvisiablecase",
        "backTargetScope": "backtargetscope",
        "targetActivity": "targetactivity",
        "noPassHandleValue": "nopasshandlevalue",
        # 子流程
        "subProcessSyncType": "subprocesssynctype",
        "subProMultiTransctorMode": "subpromultitransctormode",
        "callSubProcessGuid": "callsubprocessguid",
        # 按钮
        "stateLevel": "statelevel",
        "controlVisiableMethodGuid": "controlvisiablemethodguid",
        "defaultOpinion": "defaultopinion",
        "is_ShowOpinionTemplete": "is_showopiniontemplete",
        "isShowOpinionTemplete": "is_showopiniontemplete",
        "operationPageUrl": "operationpageurl",
        "orderNumber": "ordernumber",
        # 流程版本
        "isShowLineGraph": "isshowlinegraph",
        "isShowNodeSimple": "isshownodesimple",
        "revokeOption": "revokeoption",
        "revokeAllowDay": "revokeallowday",
        "revokeRemindOption": "revokeremindoption",
        "noParticipatorOption": "noparticipatoroption",
        "defaultUserGuid": "defaultuserguid",
        # workflowContext
        "fromMisTableId": "fromsqltablename（值改为 sql_tablename）",
        "fromFieldId": "（已废弃，引擎根据 fromfieldname + fromsqltablename 自动绑定）",
        "fromMaterialGuid": "frommaterialguid",
        "fromSqlTableName": "fromsqltablename",
        "fromFieldName": "fromfieldname",
        "fieldGuid": "fieldguid",
        "fieldName": "fieldname",
        "fieldType": "fieldtype",
        "fieldValue": "fieldvalue",
        "valueSource": "valuesource",
        # workflowProcess / workflowProcessVersion
        "isNewVersion": "isnewversion",
        "customType": "customtype",
        "canSimpleDisplay": "cansimpledisplay",
        "stateMachineTag": "statemachinetag",
        "appGuid": "appguid",
        "baseOuGuid": "baseouguid",
        "tenantGuid": "tenantguid",
        "processGuid": "processguid",
        "processName": "processname",
        "processVersionGuid": "processversionguid",
        "processVersionName": "processversionname",
        # method / event
        "dllPath": "dllpath",
        "typeName": "typename",
        "methodName": "methodname",
        "returnValueType": "returnvaluetype",
        "ruleGuid": "ruleguid",
        "eventGuid": "eventguid",
        "eventName": "eventname",
        "eventType": "eventtype",
        "eventMethodGuid": "eventmethodguid",
        "syncType": "synctype",
        "sourceGuid": "sourceguid",
        "belongTo": "belongto",
    }

    def _check_deprecated_recursive(node, parent_path: str = ""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in DEPRECATED_CAMEL:
                    result.warn_strict_error(
                        p,
                        f"{parent_path}.{k} 已废弃（spec v2），请改为 '{DEPRECATED_CAMEL[k]}'。"
                        f"--strict 模式下此问题会升级为 error。",
                    )
                _check_deprecated_recursive(v, f"{parent_path}.{k}" if parent_path else k)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                _check_deprecated_recursive(item, f"{parent_path}[{i}]")

    _check_deprecated_recursive(wf, "workFlow")

    # ============================================================
    # spec v2 可选节点：workflowActivityMaterial / workflowActivityFieldAccess 引用闭合
    # ============================================================
    activity_guids_set = {act.get("activityguid") for act, _ in parsed_activities if isinstance(act, dict)}
    material_guids_set = set()
    if isinstance(pv_material, list):
        material_guids_set = {m.get("materialguid") for m in pv_material if isinstance(m, dict)}
    sqltablenames_set = set()
    if isinstance(pv_mistableset, list):
        sqltablenames_set = {ts.get("sql_tablename") for ts in pv_mistableset if isinstance(ts, dict)}

    for act, owner in parsed_activities:
        # spec v2 扩展字段值域校验
        ltime = act.get("locktimewhenmultitransactor")
        if ltime not in (None, ""):
            try:
                tval = int(ltime)
                if tval < 1:
                    result.warn(p, f"{owner}.locktimewhenmultitransactor={ltime} 应为 >1 的分钟数")
            except (ValueError, TypeError):
                result.warn(p, f"{owner}.locktimewhenmultitransactor='{ltime}' 应为字符串/整数表示的分钟数")
        # passrate 0-100
        prate = act.get("passrate")
        if prate not in (None, ""):
            try:
                pv = int(prate)
                if not (0 <= pv <= 100):
                    result.warn(p, f"{owner}.passrate={prate} 应在 0-100 范围内")
            except (ValueError, TypeError):
                result.warn(p, f"{owner}.passrate='{prate}' 应为 0-100 的数值")
        # passratecalculatemode 10 或 20
        pmode = act.get("passratecalculatemode")
        if pmode is not None and pmode not in (10, 20):
            result.warn(p, f"{owner}.passratecalculatemode={pmode} 应为 10 或 20")

        materials = act.get("workflowActivityMaterial") or []
        for mi, mat in enumerate(materials):
            if not isinstance(mat, dict):
                continue
            mat_act_guid = mat.get("activityguid")
            if mat_act_guid and mat_act_guid not in activity_guids_set:
                result.err(p, f"{owner}.workflowActivityMaterial[{mi}].activityguid '{mat_act_guid}' 找不到对应活动")
            mat_mat_guid = mat.get("materialguid")
            if mat_mat_guid and material_guids_set and mat_mat_guid not in material_guids_set:
                result.err(p, f"{owner}.workflowActivityMaterial[{mi}].materialguid '{mat_mat_guid}' 找不到对应材料")
            field_accesses = mat.get("workflowActivityFieldAccess") or []
            for fi, fa in enumerate(field_accesses):
                if not isinstance(fa, dict):
                    continue
                fa_amg = fa.get("activitymaterialguid")
                if fa_amg and fa_amg != mat.get("activitymaterialguid"):
                    result.err(
                        p,
                        f"{owner}.workflowActivityMaterial[{mi}].workflowActivityFieldAccess[{fi}].activitymaterialguid 不一致",
                    )
                fa_table = fa.get("sqltablename")
                if fa_table and sqltablenames_set and fa_table not in sqltablenames_set:
                    result.warn(
                        p,
                        f"{owner}.workflowActivityMaterial[{mi}].workflowActivityFieldAccess[{fi}].sqltablename '{fa_table}' "
                        f"在 workflowPvMisTableSet 中找不到",
                    )

    # 检测到 workflowPvMisTableSet.tableid（已废弃）：strict 模式升级为 error
    if isinstance(pv_mistableset, list):
        for i, ts in enumerate(pv_mistableset):
            if isinstance(ts, dict) and "tableid" in ts:
                result.warn_strict_error(
                    p,
                    f"workflowPvMisTableSet[{i}].tableid 已废弃（spec v2），"
                    f"现由引擎根据 sql_tablename 自动绑定 mis 表 ID，请删除此字段。"
                    f"--strict 模式下此问题会升级为 error。",
                )

    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def _action_ids_from_event(value) -> list[str] | None:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return value
    return None


def _validate_page_events(
    *,
    path: str,
    owner: str,
    events,
    actions: dict,
    result: ValidationResult,
) -> None:
    if events in (None, {}):
        return
    if not isinstance(events, dict):
        result.err(path, f"{owner}.events 必须是对象")
        return
    for ev_name, ev_val in events.items():
        action_ids = _action_ids_from_event(ev_val)
        if action_ids is None:
            result.err(path, f"{owner}.events.{ev_name} 必须是 action id 字符串或字符串数组")
            continue
        for aid in action_ids:
            if aid not in actions:
                result.err(path, f"{owner}.events.{ev_name} 引用未注册的 action: {aid}")


def _model_parts(ref) -> list[str] | None:
    if not isinstance(ref, str) or not ref.strip():
        return None
    ref = ref.strip()
    if ref.startswith("model."):
        ref = ref[6:]
    parts = ref.split(".")
    if not all(parts):
        return None
    return parts


def _normalize_page_models(models) -> dict:
    """Return page models indexed by alias.

    Core page schema uses models as an array. Older generated pages used an
    object keyed by alias, so the validator accepts both while checking refs
    through the same alias map.
    """
    if isinstance(models, dict):
        return models
    if not isinstance(models, list):
        return {}
    normalized = {}
    for item in models:
        if not isinstance(item, dict):
            continue
        alias = item.get("alias") or item.get("name") or item.get("id")
        if alias:
            normalized[str(alias)] = item
    return normalized


def _model_ref_exists(ref, models: dict, *, allow_root: bool = True) -> bool:
    parts = _model_parts(ref)
    if not parts:
        return False
    root = parts[0]
    if root not in models:
        return False
    if len(parts) == 1:
        return allow_root
    fields = (models.get(root) or {}).get("fields") or {}
    return parts[1] in fields


def _iter_page_nodes(children, parent: str = "children"):
    for idx, item in enumerate(children or []):
        owner = f"{parent}[{idx}]"
        if isinstance(item, dict):
            yield owner, item
            nested = item.get("children")
            if isinstance(nested, list):
                yield from _iter_page_nodes(nested, f"{owner}.children")


def _validate_action_cycles(path: str, graph: dict[str, set[str]], result: ValidationResult) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(action_id: str, stack: list[str]) -> None:
        if action_id in visiting:
            result.err(path, f"actions.run 存在循环调用: {' -> '.join(stack + [action_id])}")
            return
        if action_id in visited:
            return
        visiting.add(action_id)
        for next_id in graph.get(action_id, set()):
            dfs(next_id, stack + [action_id])
        visiting.remove(action_id)
        visited.add(action_id)

    for action_id in graph:
        dfs(action_id, [])


def validate_pagedesigne(path: Path, data: dict, result: ValidationResult):
    p = str(path)
    if not isinstance(data, dict):
        result.err(p, f"顶层必须是对象，实际 {type(data).__name__}")
        return
    if data.get("kind") != "page":
        result.err(p, f"kind 应为 'page'，实际 '{data.get('kind')}'")
    if data.get("schemaVersion") != "core-1.0":
        result.warn(p, f"schemaVersion 应为 'core-1.0'，实际 '{data.get('schemaVersion')}'")

    # pagetag 必填 + 格式校验（应用内唯一性在跨文件 check 里做，见 validate_pagedesigne_pagetag_refs）
    pagetag = data.get("pagetag")
    if not pagetag:
        result.err(p, "缺少 pagetag 字段（页面运行时标识，应用内唯一，被 workflow handleurl 引用）")
    elif not isinstance(pagetag, str):
        result.err(p, f"pagetag 必须是字符串，实际 {type(pagetag).__name__}")
    elif not re.match(r"^[a-z][a-z0-9_]*$", pagetag):
        result.err(p, f"pagetag 不合法: '{pagetag}'（要求小写字母开头，仅含小写英文/数字/下划线）")

    raw_models = data.get("models") or []
    models = _normalize_page_models(raw_models)
    resources = data.get("resources") or {}
    actions = data.get("actions") or {}
    children = data.get("children")
    if not isinstance(raw_models, (list, dict)):
        result.err(p, "models 必须是数组或对象")
    elif isinstance(raw_models, list):
        for i, model in enumerate(raw_models):
            if not isinstance(model, dict):
                result.err(p, f"models[{i}] 必须是对象")
                continue
            if not model.get("alias"):
                result.err(p, f"models[{i}].alias 必填")
        aliases = [m.get("alias") for m in raw_models if isinstance(m, dict) and m.get("alias")]
        duplicate_aliases = sorted({x for x in aliases if aliases.count(x) > 1})
        if duplicate_aliases:
            result.err(p, f"models alias 重复: {duplicate_aliases}")
    if not isinstance(resources, dict):
        result.err(p, "resources 必须是对象")
        resources = {}
    if not isinstance(actions, dict):
        result.err(p, "actions 必须是对象")
        actions = {}

    if children is None:
        result.err(p, "缺少 children 字段")
        children = []
    elif not isinstance(children, list):
        result.err(p, "children 必须是数组")
        children = []

    _validate_page_events(path=p, owner="page", events=data.get("events") or {}, actions=actions, result=result)

    node_ids = []
    for owner, item in _iter_page_nodes(children):
        node_id = item.get("id")
        if node_id:
            node_ids.append(node_id)
        else:
            result.warn(p, f"{owner} 缺少 id，建议补稳定标识")

        node_type = item.get("type")
        if not isinstance(node_type, str) or not node_type:
            result.err(p, f"{owner}.type 必须是非空字符串")

        if "children" in item and not isinstance(item.get("children"), list):
            result.err(p, f"{owner}.children 必须是数组")

        _validate_page_events(path=p, owner=owner, events=item.get("events") or {}, actions=actions, result=result)

        source = item.get("source")
        if source:
            if not isinstance(source, str):
                result.err(p, f"{owner}.source 必须是 resource id 字符串")
            elif source not in resources:
                result.err(p, f"{owner}.source 引用不存在的 resource: {source}")

        for ref_key in ("model", "textModel"):
            model_ref = item.get(ref_key)
            if model_ref and not _model_ref_exists(model_ref, models):
                result.err(p, f"{owner}.{ref_key} 引用不存在的模型字段: {model_ref}")

        visible = item.get("visible")
        if visible is not None and not isinstance(visible, (bool, str)):
            result.err(p, f"{owner}.visible 必须是布尔值或表达式字符串")

        if item.get("type") == "table":
            table_model = item.get("model")
            if table_model and not _model_ref_exists(table_model, models, allow_root=True):
                result.err(p, f"{owner}.model 引用不存在的集合模型: {table_model}")
            columns = item.get("columns") or []
            if not isinstance(columns, list):
                result.err(p, f"{owner}.columns 必须是数组")
            else:
                root = (_model_parts(table_model) or [None])[0]
                fields = (models.get(root) or {}).get("fields") or {}
                for i, col in enumerate(columns):
                    if not isinstance(col, dict):
                        result.err(p, f"{owner}.columns[{i}] 必须是对象")
                        continue
                    field = col.get("field")
                    if field and not isinstance(field, str):
                        result.err(p, f"{owner}.columns[{i}].field 必须是字段名字符串")
                    elif field and root and field not in fields:
                        result.err(p, f"{owner}.columns[{i}].field 引用不存在的字段: {field}")

    duplicate_node_ids = sorted({x for x in node_ids if node_ids.count(x) > 1})
    if duplicate_node_ids:
        result.err(p, f"同一页面 node id 重复: {duplicate_node_ids}")

    action_run_graph: dict[str, set[str]] = {aid: set() for aid in actions}
    for action_id, action in actions.items():
        if not isinstance(action, dict):
            result.err(p, f"actions.{action_id} 必须是对象")
            continue
        steps = action.get("steps")
        if not isinstance(steps, list):
            result.err(p, f"actions.{action_id}.steps 必须是数组")
            continue
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                result.err(p, f"actions.{action_id}.steps[{i}] 必须是对象")
                continue
            use = step.get("use")
            if use:
                if not isinstance(use, str) or "." not in use:
                    result.err(p, f"actions.{action_id}.steps[{i}].use 必须是 resource.operation")
                else:
                    resource_id, operation_id = use.split(".", 1)
                    resource = resources.get(resource_id)
                    operations = (resource or {}).get("operations") or {}
                    if resource_id not in resources:
                        result.err(p, f"actions.{action_id}.steps[{i}].use 引用不存在的 resource: {resource_id}")
                    elif operation_id not in operations:
                        result.err(
                            p,
                            f"actions.{action_id}.steps[{i}].use 引用不存在的 operation: {use}",
                        )
            run = step.get("run")
            if run:
                run_ids = [run] if isinstance(run, str) else run if isinstance(run, list) else []
                if not run_ids:
                    result.err(p, f"actions.{action_id}.steps[{i}].run 必须是 action id 或 action id 数组")
                for run_id in run_ids:
                    if not isinstance(run_id, str):
                        result.err(p, f"actions.{action_id}.steps[{i}].run 项必须是 action id 字符串")
                        continue
                    if run_id not in actions:
                        result.err(p, f"actions.{action_id}.steps[{i}].run 引用未注册的 action: {run_id}")
                    else:
                        action_run_graph.setdefault(action_id, set()).add(run_id)
            assign = step.get("assign")
            if assign:
                if not isinstance(assign, dict):
                    result.err(p, f"actions.{action_id}.steps[{i}].assign 必须是对象")
                else:
                    for target_ref in assign:
                        if not _model_ref_exists(target_ref, models, allow_root=True):
                            result.err(
                                p,
                                f"actions.{action_id}.steps[{i}].assign 左侧不是可写模型引用: {target_ref}",
                            )
            validate_ref = step.get("validate")
            if validate_ref and isinstance(validate_ref, str) and validate_ref.startswith("model."):
                if not _model_ref_exists(validate_ref, models, allow_root=True):
                    result.err(p, f"actions.{action_id}.steps[{i}].validate 引用不存在的模型: {validate_ref}")

    _validate_action_cycles(p, action_run_graph, result)

    if not any(p == path_ for path_, _ in result.errors):
        result.ok(p)


def validate_one(path: Path, result: ValidationResult):
    p = str(path)
    suffix = path.suffix.lower()
    is_json = suffix == ".json"

    # 空文件直接跳过
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    if size == 0:
        result.warn(p, "文件为空，跳过校验")
        return

    try:
        if is_json:
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = yaml_load(path)
    except Exception as e:
        # 兼容低代码扩展语法（如 codeitem 嵌套子项），降级为 warn
        result.warn(
            p,
            f"解析失败（可能使用了低代码扩展语法/嵌套子项写法）: {str(e).splitlines()[0]}",
        )
        return

    yml_type = detect_yml_type(path, data)

    if is_json or yml_type == "pagedesigne":
        validate_pagedesigne(path, data or {}, result)
        return

    if yml_type == "appinfo":
        validate_appinfo(path, data or {}, result)
    elif yml_type == "appref":
        validate_appref(path, data, result)
    elif yml_type == "codeitem":
        validate_codeitem(path, data or {}, result)
    elif yml_type == "mis":
        validate_mis(path, data or {}, result)
    elif yml_type == "module":
        validate_module(path, data or {}, result)
    elif yml_type == "event":
        validate_event(path, data or {}, result)
    elif yml_type == "workflow":
        validate_workflow(path, data or {}, result)
    else:
        result.warn(p, f"未识别的文件类型，跳过校验")


def find_target_files(path: Path) -> list[Path]:
    """从指定路径收集所有需要校验的文件（yml/yaml + 页面设计器 json）."""
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    targets = []
    targets.extend(path.rglob("*.yml"))
    targets.extend(path.rglob("*.yaml"))
    # 页面设计器文件使用 page/*.json。
    targets.extend(path.rglob("page/*.json"))
    return sorted(set(targets))


def validate_metadata_dir_structure(metadata_dir: Path, result: ValidationResult):
    """校验应用根目录整体结构（appinfo 必备等）。

    spec v2：应用资产直接挂在 <apptag>/ 下，**不再有 metadata/ 这一层**。
    检测到老结构时输出 strict-error（默认 warn，--strict 时升级为 error）。
    """
    p = str(metadata_dir)
    appinfo = metadata_dir / "appinfo.lowcode.yml"

    # spec v2 路径红线：检测老结构 metadata/ 层
    is_metadata_dir = metadata_dir.name == "metadata"
    has_metadata_subdir = (metadata_dir / "metadata").is_dir()
    if is_metadata_dir:
        result.warn_strict_error(
            p,
            "检测到老结构应用根（路径以 /metadata 结尾，spec v2 已废弃）。"
            "请将资产从 <apptag>/metadata/<asset>/ 迁移到 <apptag>/<asset>/，例如：\n"
            f"  mv {metadata_dir}/* {metadata_dir.parent}/ && rmdir {metadata_dir}\n"
            "--strict 模式下此问题会升级为 error。",
        )
    elif has_metadata_subdir:
        result.warn_strict_error(
            p,
            f"检测到老结构残留：{metadata_dir}/metadata/ 子目录。spec v2 已废弃 metadata/ 层，"
            "请把里面的资产平移到 <apptag>/ 根下，删除 metadata/ 目录。"
            "--strict 模式下此问题会升级为 error。",
        )

    if not appinfo.is_file():
        # 老结构兼容：metadata/ 内可能藏着 appinfo
        legacy_appinfo = metadata_dir / "metadata" / "appinfo.lowcode.yml"
        if legacy_appinfo.is_file():
            result.warn(
                p,
                f"appinfo.lowcode.yml 位于老结构 metadata/ 下：{legacy_appinfo}。"
                "spec v2 应位于 <apptag>/ 根下，请按上面的迁移命令处理。",
            )
        elif is_metadata_dir:
            result.err(p, "应用根目录（metadata/）缺少 appinfo.lowcode.yml")
        else:
            result.err(p, "应用根目录缺少 appinfo.lowcode.yml")


def load_any(path: Path):
    """读取 yml/json，失败返回 None."""
    try:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        return yaml_load(path)
    except Exception:
        return None


def read_apptag(app_root: Path) -> str:
    """读取 apptag。新结构下 app_root 自身就是 <apptag>/，老结构下是 <apptag>/metadata/."""
    appinfo = app_root / "appinfo.lowcode.yml"
    data = load_any(appinfo) if appinfo.is_file() else {}
    if isinstance(data, dict) and data.get("apptag"):
        return str(data["apptag"])
    # 老结构 fallback：父目录名（即 <apptag>）；新结构：目录自身名字
    if app_root.name == "metadata":
        return app_root.parent.name
    return app_root.name


def inventory_assets(metadata_dir: Path) -> dict[str, set[str]]:
    """收集 metadata 内可被 appref 引用的资产名."""
    inventory = {name: set() for name in VALID_ENGINEGUIDS}
    for path in find_target_files(metadata_dir):
        data = load_any(path)
        yml_type = detect_yml_type(path, data)
        stem = re.sub(r"\.(codeitem|mis|module|event|workflow|pagedesigne|api)$", "", path.stem)
        parent = path.parent.name

        if yml_type == "codeitem":
            inventory["codeitem"].update(x for x in [stem, (data or {}).get("name")] if x)
        elif yml_type == "mis":
            inventory["mis"].update(x for x in [stem, (data or {}).get("name"), (data or {}).get("tableName")] if x)
        elif yml_type == "module":
            inventory["module"].update(x for x in [stem, (data or {}).get("name"), (data or {}).get("code")] if x)
        elif yml_type == "event":
            app = (data or {}).get("app") or {}
            inventory["event"].update(
                x for x in [stem, app.get("name"), app.get("sign"), app.get("code"), app.get("id"), app.get("rowguid")] if x
            )
        elif yml_type == "workflow":
            wf = (data or {}).get("workFlow") or (data or {}).get("WorkFlow") or {}
            process = wf.get("workflowProcess") or wf.get("WorkflowProcess") or {}
            process_name = process.get("processname") or process.get("processname")
            inventory["workflow"].update(x for x in [stem, process_name] if x)
        elif yml_type == "pagedesigne" or (path.suffix.lower() == ".json" and parent == "page"):
            inventory["pagedesigne"].update(x for x in [stem, (data or {}).get("title"), (data or {}).get("id")] if x)
        elif parent == "api":
            inventory["api"].add(stem)
    return inventory


def find_resources_root(metadata_dir: Path) -> Path:
    """找到 META-INF/resources 根目录；找不到则用 metadata 父目录兜底."""
    for parent in metadata_dir.parents:
        if parent.name == "resources" and parent.parent.name == "META-INF":
            return parent
    return metadata_dir.parent


def find_metadata_by_apptag(metadata_dir: Path, apptag: str) -> Optional[Path]:
    """按 apptag 查找应用根目录。优先新结构，老结构兜底。"""
    resources_root = find_resources_root(metadata_dir)
    KNOWN_ASSETS = {"codeitem", "mis", "module", "event", "workflow", "page", "api"}
    # 新结构：<apptag>/ 下直接放 appinfo 或资产子目录
    for candidate in resources_root.rglob(apptag):
        if not candidate.is_dir() or candidate.name != apptag:
            continue
        if (candidate / "appinfo.lowcode.yml").is_file():
            return candidate
        if any((candidate / a).is_dir() for a in KNOWN_ASSETS):
            return candidate
    # 老结构兼容：<apptag>/metadata/
    for candidate in resources_root.rglob(f"{apptag}/metadata"):
        if candidate.is_dir():
            return candidate
    return None


def validate_appref_refs(metadata_dir: Path, current_inventory: dict[str, set[str]], result: ValidationResult) -> None:
    appref = metadata_dir / "appref.lowcode.yml"
    if not appref.is_file():
        return
    data = load_any(appref)
    if not isinstance(data, list):
        return
    current_apptag = read_apptag(metadata_dir)
    inventory_cache: dict[str, dict[str, set[str]]] = {current_apptag: current_inventory}

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        engineguid = item.get("engineguid")
        names = item.get("name") or []
        if engineguid not in VALID_ENGINEGUIDS or not isinstance(names, list):
            continue

        source_app = item.get("sourceAppTag")
        if not source_app:
            # 未声明 sourceAppTag 表示平台公共引用，当前离线工程无法可靠校验存在性。
            continue
        source_metadata = metadata_dir
        if source_app != current_apptag:
            source_metadata = find_metadata_by_apptag(metadata_dir, source_app)
            if not source_metadata:
                result.err(str(appref), f"第 {i + 1} 项 sourceAppTag='{source_app}' 找不到对应 metadata")
                continue
        if source_app not in inventory_cache:
            inventory_cache[source_app] = inventory_assets(source_metadata)
        available = inventory_cache[source_app].get(engineguid, set())
        for name in names:
            if str(name) not in available:
                result.err(
                    str(appref),
                    f"第 {i + 1} 项引用不存在: engineguid={engineguid}, name={name}, sourceAppTag={source_app}",
                )


def validate_mis_codeitem_refs(metadata_dir: Path, current_inventory: dict[str, set[str]], result: ValidationResult) -> None:
    codeitems = current_inventory.get("codeitem", set())
    for path in sorted((metadata_dir / "mis").glob("*.yml")):
        data = load_any(path)
        if not isinstance(data, dict):
            continue
        for field in data.get("fields") or []:
            if not isinstance(field, dict):
                continue
            codename = field.get("datasourceCodename")
            if codename and str(codename) not in codeitems:
                result.err(str(path), f"字段 {field.get('name')} 引用不存在的代码项: {codename}")


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _mis_table_names(metadata_dir: Path) -> set[str]:
    names: set[str] = set()
    mis_dir = metadata_dir / "mis"
    if not mis_dir.is_dir():
        return names
    for path in sorted(set(mis_dir.glob("*.yml")) | set(mis_dir.glob("*.yaml"))):
        data = load_any(path)
        if isinstance(data, dict) and data.get("tableName"):
            names.add(str(data["tableName"]))
    return names


def validate_workflow_mis_refs(metadata_dir: Path, result: ValidationResult) -> None:
    """校验 workflowPvMisTableSet.sql_tablename 是否匹配同应用 mis.tableName."""
    table_names = _mis_table_names(metadata_dir)
    workflow_dir = metadata_dir / "workflow"
    if not workflow_dir.is_dir():
        return
    workflow_files = sorted(set(workflow_dir.glob("*.yml")) | set(workflow_dir.glob("*.yaml")))
    for path in workflow_files:
        data = load_any(path)
        if not isinstance(data, dict):
            continue
        wf = data.get("workFlow") or data.get("WorkFlow") or {}
        version = wf.get("workflowVersion") or wf.get("WorkFlowVersion") or {}
        if not isinstance(version, dict):
            continue
        for i, table_set in enumerate(_as_list(version.get("workflowPvMisTableSet"))):
            if not isinstance(table_set, dict):
                continue
            sql_table = table_set.get("sql_tablename")
            if not sql_table:
                result.err(str(path), f"workflowPvMisTableSet[{i}].sql_tablename 不能为空，必须对应同应用 mis.tableName")
            elif str(sql_table) not in table_names:
                result.err(str(path), f"workflowPvMisTableSet[{i}].sql_tablename='{sql_table}' 找不到同应用 mis.tableName")


def validate_workflow_ruleguid_refs(metadata_dir: Path, current_inventory: dict[str, set[str]], result: ValidationResult) -> None:
    """校验 workflow 中指向动作流的 ruleguid 是否能在 event 资产中找到."""
    event_refs = {str(x) for x in current_inventory.get("event", set()) if x}
    workflow_dir = metadata_dir / "workflow"
    if not workflow_dir.is_dir():
        return
    workflow_files = sorted(set(workflow_dir.glob("*.yml")) | set(workflow_dir.glob("*.yaml")))
    for path in workflow_files:
        data = load_any(path)
        if not isinstance(data, dict):
            continue
        wf = data.get("workFlow") or data.get("WorkFlow") or {}
        version = wf.get("workflowVersion") or wf.get("WorkFlowVersion") or {}
        if not isinstance(version, dict):
            continue

        for i, method in enumerate(_as_list(version.get("method"))):
            if not isinstance(method, dict):
                continue
            rule_guid = method.get("ruleguid") or method.get("ruleguid")
            if rule_guid and str(rule_guid) not in event_refs:
                result.err(str(path), f"method[{i}].ruleguid 引用不存在的动作流: {rule_guid}")

        for i, event in enumerate(_as_list(version.get("workflowEvent"))):
            if not isinstance(event, dict):
                continue
            rule_guid = event.get("ruleguid") or event.get("ruleguid")
            if rule_guid and str(rule_guid) not in event_refs:
                result.err(str(path), f"workflowEvent[{i}].ruleguid 引用不存在的动作流: {rule_guid}")

        for ti, transition in enumerate(_as_list(version.get("transition"))):
            if not isinstance(transition, dict):
                continue
            wt = transition.get("WorkflowTransition") if "WorkflowTransition" in transition else transition
            if not isinstance(wt, dict):
                continue
            for ci, condition in enumerate(_as_list(wt.get("workflowTransitionCondition"))):
                if not isinstance(condition, dict):
                    continue
                rule_guid = condition.get("ruleguid") or condition.get("ruleguid")
                if rule_guid and str(rule_guid) not in event_refs:
                    result.err(
                        str(path),
                        f"transition[{ti}].workflowTransitionCondition[{ci}].ruleguid 引用不存在的动作流: {rule_guid}",
                    )


def validate_pagedesigne_pagetag_uniqueness(metadata_dir: Path, result: ValidationResult) -> None:
    """校验同应用下所有页面设计器文件的 pagetag 唯一."""
    seen: dict[str, Path] = {}
    page_dir = metadata_dir / "page"
    if not page_dir.is_dir():
        return
    candidates = list(page_dir.glob("*.json"))
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.search(r'"pagetag"\s*:\s*"([^"]+)"', content)
        if not match:
            continue
        tag = match.group(1)
        if tag in seen:
            result.err(
                str(path),
                f"pagetag '{tag}' 与 {seen[tag].name} 重复（应用内必须唯一）",
            )
        else:
            seen[tag] = path


def validate_cross_refs(metadata_dir: Path, result: ValidationResult) -> None:
    """跨文件引用校验：appref、mis 字典引用等。

    支持新结构（应用根目录直接含 appinfo.lowcode.yml + 子目录）和老结构（metadata/）。
    """
    p = str(metadata_dir)
    if not metadata_dir.is_dir():
        result.err(p, "--check-refs 需要传入应用根目录或老结构 metadata/ 目录")
        return
    # 简单识别：含 appinfo.lowcode.yml 或任意一个资产子目录就视为合法
    KNOWN_ASSETS = {"codeitem", "mis", "module", "event", "workflow", "page", "api"}
    has_appinfo = (metadata_dir / "appinfo.lowcode.yml").is_file()
    has_assets = any((metadata_dir / a).is_dir() for a in KNOWN_ASSETS)
    if not (has_appinfo or has_assets or metadata_dir.name == "metadata"):
        result.err(p, "--check-refs 目标既不含 appinfo.lowcode.yml 也无任何资产子目录，疑似传错路径")
        return
    if metadata_dir.name == "metadata":
        result.warn(
            p,
            "检测到老结构 metadata/。新结构已去掉 metadata 层，建议把内部资产迁到 <apptag>/ 下。",
        )
    current_inventory = inventory_assets(metadata_dir)
    validate_appref_refs(metadata_dir, current_inventory, result)
    validate_mis_codeitem_refs(metadata_dir, current_inventory, result)
    validate_workflow_mis_refs(metadata_dir, result)
    validate_workflow_ruleguid_refs(metadata_dir, current_inventory, result)
    validate_pagedesigne_pagetag_uniqueness(metadata_dir, result)


def _find_asset_file(app_root: Path, asset_type: str, expected_names: list[str]) -> Path | None:
    suffix_map = {
        "codeitem": ".codeitem.yml",
        "mis": ".mis.yml",
        "module": ".module.yml",
        "pagedesigne": ".json",
        "workflow": ".workflow.yml",
        "event": ".event.yml",
    }
    folder = app_root / ("page" if asset_type == "pagedesigne" else asset_type)
    if not folder.is_dir():
        return None
    if asset_type == "pagedesigne":
        files = list(folder.glob("*.json"))
    else:
        files = list(folder.glob(f"*{suffix_map.get(asset_type, '.yml')}")) + list(folder.glob("*.yml"))
    normalized = {str(x).strip() for x in expected_names if x}
    for path in files:
        data = load_any(path) or {}
        stem = re.sub(r"\.(codeitem|mis|module|event|workflow|pagedesigne)$", "", path.stem)
        candidates = {stem}
        if isinstance(data, dict):
            candidates.update(str(data.get(k, "")).strip() for k in ("name", "tableName", "title") if data.get(k))
            if asset_type == "event":
                app = data.get("app") or {}
                candidates.update(str(app.get(k, "")).strip() for k in ("name", "sign", "id", "rowguid") if app.get(k))
            if asset_type == "workflow":
                wf = data.get("workFlow") or data.get("WorkFlow") or {}
                process = wf.get("workflowProcess") or wf.get("WorkflowProcess") or {}
                candidates.update(
                    str(process.get(k, "")).strip()
                    for k in ("processname", "processName")
                    if process.get(k)
                )
            if asset_type == "pagedesigne":
                candidates.update(str(data.get(k, "")).strip() for k in ("pagetag", "id") if data.get(k))
        if normalized & candidates:
            return path
    return None


def _workflow_activity_names(path: Path) -> set[str]:
    data = load_any(path) or {}
    wf = data.get("workFlow") or data.get("WorkFlow") or {}
    version = wf.get("workflowVersion") or wf.get("WorkflowVersion") or {}
    activities = version.get("activity") or version.get("workflowActivity") or []
    names = set()
    if isinstance(activities, list):
        for act in activities:
            if isinstance(act, dict) and act.get("activityname"):
                names.add(str(act["activityname"]))
    return names


def validate_ir_consistency(app_root: Path, ir_path: Path, result: ValidationResult) -> None:
    """轻量回检：IR 声明的资产是否在应用根下落盘，关键名称是否一致."""
    p = str(app_root)
    try:
        ir = yaml_load(ir_path)
    except Exception as e:
        result.err(str(ir_path), f"IR 读取失败: {e}")
        return
    if not isinstance(ir, dict):
        result.err(str(ir_path), "IR 顶层必须是对象")
        return
    assets = ir.get("assets") or []
    if not isinstance(assets, list):
        result.err(str(ir_path), "IR assets 必须是数组")
        return
    app = ir.get("application") or {}
    apptag = app.get("apptag")
    if apptag and app_root.name != apptag:
        appinfo = load_any(app_root / "appinfo.lowcode.yml") or {}
        if appinfo.get("apptag") != apptag:
            result.err(p, f"IR apptag={apptag} 与应用根/appinfo 不一致")

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_id = asset.get("id", "<unknown>")
        asset_type = asset.get("type")
        spec = asset.get("spec") or {}
        if asset_type == "app-shell":
            if not (app_root / "appinfo.lowcode.yml").is_file():
                result.err(p, f"{asset_id}: IR 声明 app-shell，但缺少 appinfo.lowcode.yml")
            continue
        if asset_type == "codeitem":
            expected = [spec.get("name")]
        elif asset_type == "mis":
            expected = [spec.get("tableName"), spec.get("tableChineseName")]
        elif asset_type == "module":
            expected = [spec.get("name"), spec.get("code")]
        elif asset_type == "pagedesigne":
            expected = [spec.get("title"), spec.get("pagetag")]
        elif asset_type == "workflow":
            expected = [spec.get("processName")]
        elif asset_type == "event":
            expected = [spec.get("name"), spec.get("sign")]
        else:
            continue
        found = _find_asset_file(app_root, asset_type, expected)
        if not found:
            result.err(p, f"{asset_id}: IR 声明 {asset_type} 资产 {expected}，但应用根下未找到对应文件")
            continue
        if asset_type == "workflow":
            actual_names = _workflow_activity_names(found)
            expected_activity_names = {
                str(a.get("name"))
                for a in spec.get("activities", [])
                if isinstance(a, dict) and a.get("type") in {"apply", "approve", "route", "subprocess"} and a.get("name")
            }
            missing = expected_activity_names - actual_names
            if missing:
                result.err(str(found), f"{asset_id}: workflow 缺少 IR 活动: {sorted(missing)}")


def cli():
    parser = argparse.ArgumentParser(description="低代码 yml 静态校验")
    parser.add_argument("target", help="要校验的文件或目录")
    parser.add_argument(
        "--strict", action="store_true",
        help="严格模式：警告也作为错误返回非零退出码",
    )
    parser.add_argument(
        "--check-refs", action="store_true",
        help="跨文件引用校验（mis 字段引用 codeitem、appref 引用资产是否存在等）",
    )
    parser.add_argument(
        "--check-ir-consistency",
        help="回检应用根产物是否与 lowcode-dsl-gen IR 声明一致",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print_err(f"目标不存在: {target}")
        return 1

    result = ValidationResult()

    # 目录级整体结构校验：
    # - 老结构：target.name == "metadata"
    # - 新结构（spec v2 推荐）：target 是 <apptag>/，根下含 appinfo.lowcode.yml
    if target.is_dir():
        is_legacy_metadata = target.name == "metadata"
        is_new_app_root = (target / "appinfo.lowcode.yml").is_file()
        has_metadata_subdir = (target / "metadata").is_dir()
        if is_legacy_metadata or is_new_app_root or has_metadata_subdir:
            validate_metadata_dir_structure(target, result)

    files = find_target_files(target)
    if not files:
        print_warn(f"未找到任何 yml/json 文件: {target}")
        return 0

    print_info(f"扫描到 {len(files)} 个文件")
    for f in files:
        validate_one(f, result)
    if args.check_refs:
        validate_cross_refs(target, result)
    if args.check_ir_consistency:
        if not target.is_dir():
            result.err(str(target), "--check-ir-consistency 需要 target 为应用根目录")
        else:
            validate_ir_consistency(target, Path(args.check_ir_consistency).resolve(), result)

    return result.report(strict=args.strict)


if __name__ == "__main__":
    sys.exit(cli())
