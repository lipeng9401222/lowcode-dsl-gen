---
name: lowcode-gen-workflow
description: Epoint 低代码工作流原子生成器。根据 lowcode-dsl-gen 计划或可选 IR 生成/修改 workflow/*.workflow.yml；先验证 activities 活动列表和 Mermaid 预览，再通过 add_workflow.py 或 update_workflow.py 确定性处理，禁止手写 workflowVersion、activity、transition、workflowConfig 等骨架。
---

# lowcode-gen-workflow

只处理 `assets[type=workflow]`。工作流计划写入 `.lowcode-plans/<apptag>/workflow/<asset-id>-plan.md`。

先判定 `spec.operationMode`：

- `create`：新建工作流；使用 `add_workflow.py`，允许新 `processguid/processversionguid/version`。
- `revise-plan`：计划/流程图确认阶段纠错；只更新同一个计划和流程图预览，不落应用资产。
- `update-existing`：修改已有 `.workflow.yml`；使用 `update_workflow.py`，必须保留 `processguid/processversionguid/version`。

若同名 workflow 已存在且用户语义模糊，先确认“新增独立流程”还是“修改原流程”，推荐“修改原流程”。

## Input 输入

默认输入是可读计划中的 workflow spec。`ir.yml` 只作为复杂整应用、审计追溯或兼容旧流程时的可选输入。

```yaml
spec:
  operationMode: "create"
  processName: "请假审批流程"
  processMode: "normal"
  material: "请假申请表"
  sqlTableName: "leaveinfo"
  pageTagForm: "leave_form"
  pageTagDetail: "leave_detail"
  activities:
    - { name: "申请", type: "apply" }
    - { name: "部门经理审批", type: "approve" }
  contexts: []
  conditions: []
  methods: []
  events: []
  activityMaterials: []
  activityExtra: []
  approvePassRate: []
  confirmations:
    processGoal: { status: "confirmed", source: "user_confirmed" }
    activityChain: { status: "confirmed", source: "user_confirmed" }
    transactors: { status: "confirmed", source: "user_confirmed" }
    conditions: { status: "not_required", source: "user_confirmed" }
    pageTags: { status: "confirmed", source: "repo_inferred" }
    sqlTableName: { status: "confirmed", source: "repo_inferred" }
    fieldPermissions: { status: "not_required", source: "user_confirmed" }
    approvePassRate: { status: "not_required", source: "user_confirmed" }
    timeout: { status: "not_required", source: "user_confirmed" }
    eventLinkage: { status: "not_required", source: "user_confirmed" }
```

## References 参考文档

- `../../references/workflow/工作流/index.md`
- `../../references/workflow/工作流/生成与校验/06-脚本使用指南.md`
- `../../references/workflow/工作流/生成与校验/07-字段类型约束表.md`
- 仅当匹配复杂特性时才读场景文档。

## Steps 执行步骤

1. 读取 activities 之前先校验 `spec.operationMode`，合法值只有 `create/revise-plan/update-existing`。
2. 先校验活动列表，必须包含一个 `apply`（申请）和至少一个 `approve`（审批）。
3. 用 `workflow_preview.py` 生成/更新 Mermaid 预览。预览只展示业务节点/分支，隐藏 `开始`、`结束`、`浏览`。
4. 任何 dry-run 之前先校验 `spec.confirmations`。核心确认项（`processGoal`、`activityChain`、`transactors`、`pageTags`、`sqlTableName`）必须为 `confirmed`；可选确认项只有在对应的 spec 数组为空时才允许 `not_required/skipped`。
5. 校验确认证据：`user_confirmed` 需有 `questionId/interactionId`，`repo_inferred` 需有 `repoEvidence`。光写 `source: user_confirmed` 不够。
6. 写入/更新 `.lowcode-plans/<apptag>/workflow/<asset-id>-plan.md`，包含：
   - `status: <资产状态>`
   - 输入 spec 摘要
   - 目标 workflow 文件，以及修改已有流程时保留的 GUID
   - `operationMode` 判定依据
   - Mermaid 流程图预览
   - 用户纠偏记录（无则写“无”）
   - 活动转换表（activity conversion table）
   - 确认矩阵（confirmation matrix）
   - conditions/contexts/methods/events 摘要
   - dry-run 与校验的命令和结果
7. 普通活动中不要包含引擎节点 `开始`、`结束`、`浏览`；这些由脚本生成。
8. 请求批准前，先用当前活动列表生成 Mermaid 预览：
   ```bash
   python3 ../../scripts/workflow_preview.py --activities-json '[{"name":"申请","type":"apply"},{"name":"部门经理审批","type":"approve"}]'
   ```
9. `create`（新建）落盘前，先用直接 CLI 参数 dry-run：
   ```bash
   python3 ../../scripts/add_workflow.py --app-root <app-root> --name "请假审批流程" --approvers "部门经理审批" --material "请假申请表" --dry-run
   ```
10. `update-existing`（改已有）执行：
   ```bash
   python3 ../../scripts/update_workflow.py --workflow-file <workflow-file> --activities-json '[{"name":"申请","type":"apply"},{"name":"科室负责人审批","type":"approve","oldName":"部门经理审批"}]' --dry-run
   ```
   批准后去掉 `--dry-run` 再跑同一条命令。
11. `revise-plan`（计划纠错）不跑落盘脚本。更新 workflow 子计划和 Mermaid 预览，然后再次请求确认。
12. 落盘后校验：
   ```bash
   python3 ../../scripts/validate_yml.py <workflow-file>
   ```
13. `--from-ir` 仍保留以兼容，但不要把它作为单个 workflow 新建或节点链路纠错的默认路径。

## Red Lines 红线

- 绝不手写 `workflowVersion` 子结构。
- 绝不用 `add_workflow.py --force` 去“修改”已有 workflow。
- `revise-plan` 或 `update-existing` 时，绝不改 `workflowProcess.processguid`、`workflowProcessVersion.processversionguid`、`workflowProcessVersion.version`。
- 含“否则/不满足”的条件必须使用显式的互补条件（complementary conditions）。
- `workflowContext.fieldname` 必须与条件占位符（如 `[#=leave_days#]`）一致。
- 字段权限、通过率、超时、workflow event 等关键词必须映射到对应的 JSON 输入，不得忽略。
