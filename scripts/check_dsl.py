import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml


class CheckResult:
    def __init__(self) -> None:
        self.ok: List[str] = []
        self.warn: List[str] = []
        self.err: List[str] = []

    def add_ok(self, msg: str) -> None:
        self.ok.append(msg)

    def add_warn(self, msg: str) -> None:
        self.warn.append(msg)

    def add_err(self, msg: str) -> None:
        self.err.append(msg)

    @property
    def has_error(self) -> bool:
        return len(self.err) > 0

    def print(self, file_path: Path) -> None:
        print(f"\n=== 检查文件: {file_path} ===")
        for msg in self.ok:
            print(f"[OK]   {msg}")
        for msg in self.warn:
            print(f"[WARN] {msg}")
        for msg in self.err:
            print(f"[ERR]  {msg}")


def load_yaml(path: Path, res: CheckResult) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        res.add_err(f"读取文件失败: {e}")
        return {}

    # 结构检查: 是否以 '---' 开头
    first_non_empty = None
    for line in text.splitlines():
        if line.strip():
            first_non_empty = line.strip()
            break
    if first_non_empty != "---":
        res.add_warn("文件未以 '---' 开头 (建议以 YAML 文档分隔符开头)")

    try:
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            res.add_err("YAML 顶层不是对象(dict)")
            return {}
        return data
    except Exception as e:
        res.add_err(f"YAML 解析失败: {e}")
        return {}


def check_structure(data: Dict[str, Any], res: CheckResult) -> None:
    # 必需顶层字段
    required_top = ["app", "workflow", "kind", "version", "dependencies"]
    missing = [k for k in required_top if k not in data]
    if missing:
        res.add_err(f"缺少顶层字段: {', '.join(missing)}")
    else:
        res.add_ok("顶层字段 app/workflow/kind/version/dependencies 存在")

    # app 节点完整性检查
    app = data.get("app")
    if not isinstance(app, dict):
        res.add_err("app 必须为对象(dict)")
        return
    
    # app 必需字段检查
    app_required_fields = ["mode", "name", "id", "created_at", "sign"]
    app_missing = [k for k in app_required_fields if k not in app]
    if app_missing:
        res.add_err(f"app 节点缺少必需字段: {', '.join(app_missing)}")
    else:
        res.add_ok("app 节点包含所有必需字段")
    
    # app 可选字段检查（给出建议）
    app_optional_fields = ["use_icon_as_answer_icon", "icon", "description", "icon_background"]
    app_present_optional = [k for k in app_optional_fields if k in app]
    if app_present_optional:
        res.add_ok(f"app 节点包含可选字段: {', '.join(app_present_optional)}")
    else:
        res.add_warn(f"app 节点缺少可选字段: {', '.join(app_optional_fields)} (建议添加以完善配置)")

    # 检查 app 字段值的合理性
    if "mode" in app and app["mode"] != "actflow":
        res.add_warn(f"app.mode 建议为 'actflow'，当前值: {app['mode']!r}")
    elif "mode" in app:
        res.add_ok("app.mode 为 'actflow'")
        
    if "created_at" in app:
        created_at = app["created_at"]
        if not isinstance(created_at, int) or len(str(created_at)) != 10:
            res.add_warn(f"app.created_at 应为10位秒级时间戳，当前值: {created_at}")
        else:
            res.add_ok("app.created_at 为有效的10位时间戳")
            
    if "id" in app:
        app_id = app["id"]
        if not isinstance(app_id, str) or len(app_id) != 36:
            res.add_warn(f"app.id 应为36位UUID格式，当前值: {app_id!r}")
        else:
            res.add_ok("app.id 为有效的UUID格式（动作流唯一标识）")
            
    if "sign" in app:
        sign = app["sign"]
        if not isinstance(sign, str) or not sign:
            res.add_warn(f"app.sign 应为非空字符串（动作流标识），当前值: {sign!r}")
        else:
            res.add_ok("app.sign 格式正确")

    if "code" in app:
        res.add_warn("app.code 字段已废弃，建议移除（动作流标识应使用 app.sign）")

    # workflow 下字段
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        res.add_err("workflow 必须为对象(dict)")
        return

    if "conversation_variables" not in workflow:
        res.add_err("workflow 缺少 conversation_variables 字段")
    if "environment_variables" not in workflow:
        res.add_err("workflow 缺少 environment_variables 字段")

    # workflow.sign 检查
    if "sign" not in workflow:
        res.add_err("workflow 缺少 sign 字段（动作流标识）")
    else:
        wf_sign = workflow["sign"]
        if not isinstance(wf_sign, str) or not wf_sign:
            res.add_warn(f"workflow.sign 应为非空字符串（动作流标识），当前值: {wf_sign!r}")
        else:
            res.add_ok("workflow.sign 格式正确")

    # workflow.name 检查
    if "name" not in workflow:
        res.add_warn("workflow 缺少 name 字段（建议与 app.name 一致）")
    else:
        res.add_ok("workflow.name 存在")

    # workflow 字段顺序检查: sign 应在 name 之后
    wf_keys = list(workflow.keys())
    if "name" in wf_keys and "sign" in wf_keys:
        if wf_keys.index("sign") < wf_keys.index("name"):
            res.add_warn("workflow.sign 应在 workflow.name 之后")

    # app.sign 与 workflow.sign 一致性检查
    app_sign = app.get("sign")
    wf_sign = workflow.get("sign")
    if app_sign and wf_sign and app_sign != wf_sign:
        res.add_err(f"app.sign({app_sign!r}) 与 workflow.sign({wf_sign!r}) 不一致")
    elif app_sign and wf_sign and app_sign == wf_sign:
        res.add_ok("app.sign 与 workflow.sign 一致")
    if (
        "conversation_variables" in workflow
        and workflow.get("conversation_variables") == []
    ):
        res.add_ok("workflow.conversation_variables 为 []")
    if (
        "environment_variables" in workflow
        and workflow.get("environment_variables") == []
    ):
        res.add_ok("workflow.environment_variables 为 []")

    # kind/version/dependencies 检查
    kind = data.get("kind")
    version = data.get("version")
    deps = data.get("dependencies")

    if kind != "app":
        res.add_warn(f"kind 建议为 'app'，当前值: {kind!r}")
    else:
        res.add_ok("kind 为 'app'")

    if version != "3.0":
        res.add_warn(f"version 建议为 '3.0'，当前值: {version!r}")
    else:
        res.add_ok("version 为 '3.0'")

    if not isinstance(deps, list):
        res.add_warn("dependencies 建议为列表([])")
    elif deps == []:
        res.add_ok("dependencies 为 []")


def get_graph(data: Dict[str, Any], res: CheckResult) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    workflow = data.get("workflow", {})
    graph = workflow.get("graph")
    if not isinstance(graph, dict):
        res.add_err("workflow.graph 缺失或不是对象(dict)")
        return [], []
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list):
        res.add_err("workflow.graph.nodes 缺失或不是数组")
        nodes = []
    if edges is None:
        # edges 允许为空，但要是数组
        edges = []
    if not isinstance(edges, list):
        res.add_err("workflow.graph.edges 不是数组")
        edges = []
    return nodes, edges


def check_nodes(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], res: CheckResult) -> None:
    ids: List[str] = []
    for n in nodes:
        nid = n.get("id")
        if isinstance(nid, str):
            ids.append(nid)
        else:
            res.add_err(f"存在节点未设置 id 或 id 非字符串: {n}")

    # id 唯一性
    seen: Set[str] = set()
    dup: Set[str] = set()
    for nid in ids:
        if nid in seen:
            dup.add(nid)
        else:
            seen.add(nid)
    if dup:
        res.add_err(f"节点 id 存在重复: {', '.join(sorted(dup))}")
    else:
        res.add_ok("所有节点 id 唯一")

    # 入/出度统计
    incoming: Dict[str, int] = {nid: 0 for nid in ids}
    outgoing: Dict[str, int] = {nid: 0 for nid in ids}
    for e in edges:
        s = e.get("source")
        t = e.get("target")
        if isinstance(s, str) and s in outgoing:
            outgoing[s] += 1
        if isinstance(t, str) and t in incoming:
            incoming[t] += 1

    start_nodes: List[str] = []
    end_nodes: List[str] = []

    for n in nodes:
        nid = n.get("id")
        data = n.get("data") or {}
        n_type = data.get("type") or n.get("type")

        if n_type == "start":
            start_nodes.append(nid)
            if incoming.get(nid, 0) != 0:
                res.add_err(f"开始节点 {nid} 存在入站连线 (期望无入站连线)")
        if n_type == "end":
            end_nodes.append(nid)
            if outgoing.get(nid, 0) != 0:
                res.add_err(f"结束节点 {nid} 存在出站连线 (期望无出站连线)")

    if start_nodes:
        res.add_ok(f"检测到开始节点: {', '.join(start_nodes)}")
    else:
        res.add_warn("未检测到 data.type='start' 的开始节点")

    if end_nodes:
        res.add_ok(f"检测到结束节点: {', '.join(end_nodes)}")
    else:
        res.add_warn("未检测到 data.type='end' 的结束节点")

    # 迭代节点相关检查
    for n in nodes:
        nid = n.get("id")
        data = n.get("data") or {}
        n_type = n.get("type")
        # 粗略认为 type == 'iteration' 为迭代节点
        if n_type == "iteration":
            for key in ("iteration_id", "resultType", "zIndex"):
                if key not in data:
                    res.add_err(f"迭代节点 {nid} 缺少 data.{key}")
            if "start_node_id" not in n:
                res.add_err(f"迭代节点 {nid} 缺少 start_node_id 字段")

        # custom-iteration-start
        if n_type == "custom-iteration-start":
            if data.get("isInIteration") is not True:
                res.add_err(f"迭代开始节点 {nid} data.isInIteration 必须为 true")
            if "parentId" not in n:
                res.add_err(f"迭代开始节点 {nid} 缺少 parentId")
            for key in ("selectable", "draggable", "width", "height", "zIndex"):
                if key not in n:
                    res.add_warn(f"迭代开始节点 {nid} 未设置 {key} (建议补全)")

        # 迭代内部节点
        if data.get("isInIteration") is True and n_type not in ("iteration", "custom-iteration-start"):
            if "iteration_id" not in data:
                res.add_err(f"迭代内部节点 {nid} 缺少 data.iteration_id")
            if "parentId" not in n:
                res.add_err(f"迭代内部节点 {nid} 缺少 parentId")


def check_edges(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], res: CheckResult) -> None:
    node_by_id: Dict[str, Dict[str, Any]] = {n.get("id"): n for n in nodes if isinstance(n.get("id"), str)}

    # source/target 存在性
    for e in edges:
        s = e.get("source")
        t = e.get("target")
        if s not in node_by_id:
            res.add_err(f"连线 source={s!r} 未匹配到任何节点")
        if t not in node_by_id:
            res.add_err(f"连线 target={t!r} 未匹配到任何节点")

    # 条件节点 sourceHandle true/false
    for e in edges:
        s = e.get("source")
        source_node = node_by_id.get(s)
        if not source_node:
            continue
        data = source_node.get("data") or {}
        n_type = data.get("type") or source_node.get("type")
        if n_type == "condition":
            sh = e.get("sourceHandle")
            if sh not in ("true", "false"):
                res.add_err(f"条件节点 {s} 的连线 sourceHandle 必须为 'true' 或 'false'，当前: {sh!r}")

    # 迭代连线 isInIteration/isInLoop 对应 id 字段
    for e in edges:
        data = e.get("data") or {}
        if data.get("isInIteration") is True and "iteration_id" not in data:
            res.add_err(f"连线 {e.get('id')} 标记 isInIteration=true 但缺少 data.iteration_id")
        if data.get("isInLoop") is True and "loop_id" not in data:
            res.add_err(f"连线 {e.get('id')} 标记 isInLoop=true 但缺少 data.loop_id")


def find_webhook_request_body(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """粗略扫描所有节点, 找到 webhook 节点中的 requestBody 定义并返回列表结构。"""
    workflow = data.get("workflow", {})
    graph = workflow.get("graph", {})
    nodes = graph.get("nodes") or []
    result: List[Dict[str, Any]] = []
    for n in nodes:
        n_data = n.get("data") or {}
        action_data = n_data.get("actionData") or {}
        form_data = action_data.get("formData") or []
        for item in form_data:
            if item.get("name") == "request":
                value = item.get("value") or {}
                body = value.get("requestBody")
                if isinstance(body, List):
                    result.append({"node_id": n.get("id"), "body": body})
    return result


def check_webhook_structure(data: Dict[str, Any], res: CheckResult) -> None:
    webhook_bodies = find_webhook_request_body(data)
    if not webhook_bodies:
        # 有些 DSL 可能不是 webhook 触发, 只做提示不报错
        res.add_warn("未检测到 webhook 请求体(requestBody) 配置 (如未使用 webhook 触发可忽略)")
        return

    for item in webhook_bodies:
        node_id = item["node_id"]
        body = item["body"]
        if not body:
            res.add_err(f"节点 {node_id} 的 requestBody 为空")
            continue
        root = body[0]
        if root.get("UID") != "root":
            res.add_err(f"节点 {node_id} 的 requestBody 第一个元素 UID 建议为 'root'，当前: {root.get('UID')!r}")
        if "children" not in root or not isinstance(root.get("children"), list):
            res.add_err(f"节点 {node_id} 的 root 需包含 children 数组")
        else:
            res.add_ok(f"节点 {node_id} 的 webhook 根节点 children 结构存在 (建议进一步人工核查嵌套结构)")


def check_file(path: Path) -> bool:
    res = CheckResult()
    data = load_yaml(path, res)
    if not data:
        res.print(path)
        return not res.has_error

    check_structure(data, res)
    nodes, edges = get_graph(data, res)
    if nodes:
        check_nodes(nodes, edges, res)
        check_edges(nodes, edges, res)
    check_webhook_structure(data, res)

    res.print(path)
    return not res.has_error


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("用法: python check_dsl.py <dsl文件1> [dsl文件2 ...]")
        return 1

    any_error = False
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"[ERR] 文件不存在: {path}")
            any_error = True
            continue
        ok = check_file(path)
        if not ok:
            any_error = True

    if any_error:
        print("\n检查完成: 存在错误，请根据 [ERR] 信息修复后重试。")
        return 2
    else:
        print("\n检查完成: 所有文件通过必需检查 (部分 [WARN] 为建议项，可按需优化)。")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
