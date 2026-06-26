# lowcode-dsl-gen 工作流纠偏与 IR 降级改造

## 背景

本次改造解决两个问题：

1. 用户看完 LLM 生成的流程图后，只想修正节点链路，但 skill 容易误走新建流程，导致生成新的 workflow。
2. 单资产 workflow 生成前强制同步 `ir.yml` 会拖慢流程；对节点链路纠偏来说，IR 不是必要产物。

## 本次策略

采用二阶段策略，先把 IR 从默认必经路径降级为可选审计/兼容路径，不删除历史脚本和 fixture。

- 第一阶段（本次）：workflow 默认走计划、Mermaid 预览、直接 CLI 参数、dry-run、落盘校验。
- 第二阶段（后续评估）：如果评测证明直接 CLI 路径稳定，再考虑删除 IR schema、`validate_ir.py`、`validate_plan.py` 和 `ir_to_*` 转换脚本。

## 已实施改造点

### 1. workflow 纠偏默认不新建

- 用户表达“修改、调整、修正、刚才流程图不对、两个节点有问题”时，优先判定为 `revise-plan` 或 `update-existing`。
- 命中已有同名 `.workflow.yml`、目标文件或 `processguid` 时，默认推荐“修改原流程”。
- 只有 `create` 允许生成新的 `processguid/processversionguid/version`。
- `revise-plan` 只更新计划与 Mermaid 预览，不落应用资产。
- `update-existing` 必须使用 `update_workflow.py`，禁止用 `add_workflow.py --force` 覆盖旧流程。

### 2. workflow 预览脱离 IR

`scripts/workflow_preview.py` 新增 `--activities-json`：

```bash
python3 scripts/workflow_preview.py \
  --activities-json '[{"name":"申请","type":"apply"},{"name":"科室负责人审批","type":"approve"}]'
```

仍保留：

- `--workflow-file`：从已有 workflow 生成基线预览。
- `--from-ir`：兼容旧 IR 流程。

### 3. workflow 默认使用直接 CLI

新建：

```bash
python3 scripts/add_workflow.py \
  --app-root <app-root> \
  --name "请假审批流程" \
  --approvers "部门经理审批" \
  --material "请假申请表" \
  --dry-run
```

修改已有：

```bash
python3 scripts/update_workflow.py \
  --workflow-file <workflow-file> \
  --activities-json '[{"name":"申请","type":"apply"},{"name":"科室负责人审批","type":"approve","oldName":"部门经理审批"}]' \
  --dry-run
```

`--from-ir` 继续保留，但文案标注为兼容路径，不再作为默认示例。

## 暂不做的范围

本次只做节点链路层面的纠偏：节点改名、增删节点、主链路调整。

暂不实现以下深层配置的原地修改：

- 处理人
- 字段权限
- 条件分支
- 事件联动
- 超时提醒
- 通过率

## 验证命令

```bash
python3 scripts/workflow_preview.py --activities-json '[{"name":"申请","type":"apply"},{"name":"科室负责人审批","type":"approve"}]'
python3 scripts/update_workflow.py --workflow-file <workflow-file> --activities-json '[...]' --dry-run
python3 scripts/add_workflow.py --app-root <app-root> --name "请假审批流程" --approvers "部门经理审批" --dry-run
python3 scripts/validate_yml.py <workflow-file>
```

