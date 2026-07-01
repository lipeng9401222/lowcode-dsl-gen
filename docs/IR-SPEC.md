# Lowcode DSL IR 规范 (Lowcode DSL IR Specification)

> Version: 1.0 | 供 `lowcode-dsl-gen` 调度器与原子 skill 使用。
>
> 说明：本文为 IR（中间表示）规范，正文以英文为主，关键标题与要点已补中文。术语字段名（如 `apptag`、`operationMode`）保留英文。

## 1. 目的 Purpose

> 关键点：IR 是「可读计划」与「确定性 DSL 生成」之间的机器合同；它只描述「要什么」（意图），不描述 YAML 内部骨架。脚本和校验器负责把 IR 展开成具体的 Epoint 低代码元数据。IR 不是第一轮规划的必备产物，但在 dry-run / 校验 / 批准 / 落盘前必须存在于规范路径 `.lowcode-plans/<apptag>/ir.yml` 并通过 `validate_ir.py`。

IR is the machine contract between readable planning and deterministic DSL generation. The dispatcher writes a readable plan first, grills unresolved generation facts, then syncs IR as cache/audit/script input before dry-run or landing. Atomic skills consume one asset fragment at a time.

IR must describe intent, not handwritten YAML internals. Scripts and validators expand IR into concrete Epoint lowcode metadata.

Users review the readable plan by default. Show full IR only for debugging, audit, or when the user explicitly asks for it.

IR is not a mandatory first-round planning artifact. In `plan-only` or early `approval_status=pending` planning, the plan package may contain only the readable plan and open-question summary. Before dry-run, validation, approval, or landing, `.lowcode-plans/<apptag>/ir.yml` must exist, use the canonical path, and pass `validate_ir.py`.

Keep IR minimal: include fields needed by generators, validators, source evidence, asset dependencies, and unresolved/resolved `open_questions`. Do not duplicate long markdown plan prose, full reference excerpts, or generated YAML internals.

## 2. 顶层结构 Top-Level Shape

> 关键点：IR 顶层包含 `version` / `task`（任务模式与来源）/ `application`（应用基础信息与来源）/ `assets`（资产列表）/ `open_questions`（待确认问题）/ `validation`（校验状态）。

```yaml
version: "1.0"
task:
  mode: "whole-app"
  requestedAssetTypes: ["app-shell", "codeitem", "mis", "module", "pagedesigne", "workflow"]
  sources:
    mode: "user_confirmed"
  sourceDetails:
    mode:
      questionId: "q-mode"
      answer: "根据 PRD 完整生成采购立项低代码应用"
application:
  apptag: "purchaseproject"
  applicationname: "采购立项"
  developerstag: "epoint"
  kitid: "businessprocess"
  tenantguid: ""
  baseouguid: ""
  categories: []
  sources:
    developerstag: "user_confirmed"
    kitid: "user_confirmed"
    tenantguid: "safe_default"
    baseouguid: "safe_default"
    categories: "user_confirmed"
  sourceDetails:
    developerstag: { questionId: "q-basic" }
    kitid: { questionId: "q-basic" }
    tenantguid: { reason: "用户未要求多租户，空值作为安全默认" }
    baseouguid: { reason: "用户未要求独立单位，空值作为安全默认" }
    categories: { questionId: "q-basic" }
assets: []
open_questions: []
validation:
  status: "pending"
  reports: []
```

### `task`

| Field | Required | Notes |
|---|---:|---|
| `mode` | yes | One of `whole-app`, `greenfield-app`, `existing-app`, `asset-fast`, `plan-only`. |
| `requestedAssetTypes` | when `asset-fast` | Asset types explicitly requested by the user. |
| `sources.mode` | yes | Must be `user_confirmed` or `repo_inferred`; `model_inferred` blocks generation. |
| `sourceDetails.mode` | yes | `user_confirmed` requires `questionId` or `interactionId`; `repo_inferred` requires `repoEvidence`. |

Mode rules:

- Workflow-only prompts such as “生成请假工作流/审批流” are `asset-fast` unless the user explicitly asks for a complete/new application.
- In `asset-fast`, `assets[].type` must be a subset of `requestedAssetTypes`; do not add app-shell/codeitem/mis/module/pagedesigne unless the user confirms a complete/new app.
- `whole-app` requires explicit whole-app/PRD/需求文档 wording in the user confirmation evidence. Do not upgrade to `whole-app` only because the user supplied `apptag` or accepted a recommended option ambiguously.

### `application`

| Field | Required | Notes |
|---|---:|---|
| `apptag` | yes | Lowercase app identifier. |
| `applicationname` | yes | Chinese application name. |
| `developerstag` | yes | `epoint` may be recommended, but must be user-confirmed or repo-inferred. |
| `kitid` | yes | `businessprocess` may be recommended, but must be user-confirmed or repo-inferred. |
| `tenantguid` | no | Empty is a safe default only when recorded in sources/plan assumptions. |
| `baseouguid` | no | Empty is a safe default only when recorded in sources/plan assumptions. |
| `categories` | yes | Empty array means “not categorized” and still needs user confirmation or repo inference. |

### `sources`

Any field that affects generation must have a source marker. Source values:

| Source | Meaning | Generation |
|---|---|---|
| `user_confirmed` | User explicitly confirmed it. | Allowed. |
| `repo_inferred` | Existing appinfo/directory/assets prove it. | Allowed. |
| `safe_default` | Safe technical default documented in plan assumptions. | Allowed for explicitly safe fields only. |
| `model_inferred` | Model guessed it. | Blocks generation/approval. |

For app creation or app-shell assets, source tracking is mandatory for `developerstag`, `kitid`, `categories`, `baseouguid`, `tenantguid`, and `appref`.

### Source Evidence

Every source that affects generation needs evidence:

```yaml
application:
  sources:
    developerstag: "user_confirmed"
    kitid: "repo_inferred"
    tenantguid: "safe_default"
  sourceDetails:
    developerstag:
      questionId: "q-basic"
    kitid:
      repoEvidence:
        path: "src/main/resources/META-INF/resources/epoint/purchaseproject/appinfo.lowcode.yml"
    tenantguid:
      reason: "未启用多租户，空值作为安全默认"
```

Rules:

- `user_confirmed` must reference an `open_questions[].id` or a dialogue `interactionId`.
- `repo_inferred` must include `repoEvidence.path` or `repoEvidence.paths`.
- `safe_default` must include `reason`.
- A bare `source: user_confirmed` or `source: repo_inferred` without evidence must fail validation.

### `assets[]`

Every asset item:

```yaml
- id: "asset-001"
  type: "mis"
  status: "pending"
  dependencies: []
  spec: {}
  errors: []
```

Allowed `type` values:

- `app-shell`
- `codeitem`
- `mis`
- `module`
- `pagedesigne`
- `workflow`
- `event`

Allowed `status` values:

- `pending`
- `generating`
- `validating`
- `done`
- `failed`
- `skipped`

## 3. 资产规格 Asset Specs

> 关键点：以下分别给出 app-shell / codeitem / mis / module / pagedesigne / workflow / event 的 `spec` 结构示例与约束。

### app-shell

```yaml
spec:
  # createDirs 默认只含核心目录；event / api 默认不建，仅在用户明确需要时加入
  createDirs: ["codeitem", "mis", "module", "pagedesigne", "workflow"]
  appref:
    enabled: false
    refs: []
  sources:
    appref: "user_confirmed"
  sourceDetails:
    appref: { questionId: "q-basic" }
  confirmations:
    developerstag: { status: "confirmed", source: "user_confirmed", questionId: "q-basic" }
    kitid: { status: "confirmed", source: "user_confirmed", questionId: "q-basic" }
    categories: { status: "confirmed", source: "user_confirmed", questionId: "q-basic" }
    appref: { status: "not_required", source: "user_confirmed", questionId: "q-basic" }
```

### codeitem

```yaml
spec:
  name: "审核状态"
  description: "业务审核状态"
  items:
    - codetext: "待提交"
      codevalue: "0"
      ordernum: 1
```

`items` must not be empty before generation.

### mis

```yaml
spec:
  tableName: "purchaseproject"
  tableChineseName: "采购立项"
  primaryKey: "rowguid"
  fields:
    - fieldName: "audit_status"
      fieldType: "nvarchar"
      length: 50
      chineseName: "审核状态"
      mustfill: false
      datasourceCodename: "审核状态"
```

`tableName` uses the existing MIS naming constraints: lowercase letters/digits and no underscore.

### module

```yaml
spec:
  name: "采购管理"
  code: "9544"
  url: ""
  subModules: []
```

### pagedesigne

```yaml
spec:
  title: "采购立项列表"
  pagetag: "purchaseproject_list"
  device: "desktop"
  pageType: "list"
  endpoint: "/api/purchaseproject"
  model: "items"
  fields: []
  query: []
```

`device` defaults to `desktop`; use `mobile` only when the user explicitly asks for mobile/H5/small-screen.

### workflow

```yaml
spec:
  operationMode: "create"
  targetWorkflow:
    file: ""
    processguid: ""
  renameActivities: {}
  processName: "采购立项审批"
  processMode: "normal"
  material: "采购立项申请表"
  sqlTableName: "purchaseproject"
  pageTagForm: "purchaseproject_form"
  pageTagDetail: "purchaseproject_detail"
  activities:
    - name: "申请"
      type: "apply"
    - name: "部门经理审批"
      type: "approve"
      transactorSource: "assignee"
    - name: "分管领导审批"
      type: "approve"
      transactorSource: "assignee"
  contexts: []
  conditions: []
  methods: []
  events: []
  activityMaterials: []
  activityExtra: []
  approvePassRate: []
  confirmations:
    processGoal: { status: "confirmed", source: "user_confirmed", questionId: "q-workflow-effect" }
    activityChain: { status: "confirmed", source: "user_confirmed", questionId: "q-workflow-effect" }
    transactors: { status: "confirmed", source: "user_confirmed", questionId: "q-workflow-effect" }
    conditions: { status: "confirmed", source: "user_confirmed", questionId: "q-workflow-effect" }
    pageTags:
      status: "confirmed"
      source: "repo_inferred"
      repoEvidence:
        paths:
          - "page/purchaseproject_form.page.yml"
          - "page/purchaseproject_detail.page.yml"
    sqlTableName:
      status: "confirmed"
      source: "repo_inferred"
      repoEvidence:
        path: "mis/purchaseproject.mis.yml"
    fieldPermissions: { status: "not_required", source: "user_confirmed", questionId: "q-workflow-effect" }
    approvePassRate: { status: "not_required", source: "user_confirmed", questionId: "q-workflow-effect" }
    timeout: { status: "not_required", source: "user_confirmed", questionId: "q-workflow-effect" }
    eventLinkage: { status: "not_required", source: "user_confirmed", questionId: "q-workflow-effect" }
```

Rules:

- `operationMode` defaults to `create`; legal values are `create`, `revise-plan`, and `update-existing`.
- `create` is the only mode that may create a new `processguid/processversionguid/version`.
- `revise-plan` means the user is correcting the current plan or Mermaid preview before landing; update the same IR asset and preview, and do not run landing scripts.
- `update-existing` means an existing `.workflow.yml` is being modified in place. It must include `targetWorkflow.file` or `targetWorkflow.processguid`.
- In `update-existing`, preserve `workflowProcess.processguid`, `workflowProcessVersion.processversionguid`, and `workflowProcessVersion.version`. Use `renameActivities` or activity-level `oldName` to preserve activity GUIDs when renaming nodes.
- `activities` is required and must include at least one `apply` and one `approve` activity.
- Do not include `开始`、`结束`、`浏览` in IR unless the user explicitly discusses them; `add_workflow.py` creates those engine nodes.
- Conditions must use explicit complementary rules for “otherwise / 不满足”.
- `contexts[].fieldname` must match placeholders used in `conditions[].leftvalue`, for example `[#=leave_days#]`.
- `conditions[].conditionexpressiontype` defaults to `10` when omitted. Type `10` requires `leftvalue` + `compareoperation` + `rightvalue` + `valuetype`; type `20` requires `conditionexpression`; type `30` requires `methodguid` or `ruleguid`.
- Type `20` combines type `10` conditions on the same transition. References like `[1]` and `[2]` are 1-based indexes of type `10` conditions sorted by `ordernum`, then by list order. Do not reference conditions from another transition.
- `confirmations` is required. Core fields `processGoal`, `activityChain`, `transactors`, `pageTags`, and `sqlTableName` must be `confirmed`; optional capability fields may be `confirmed`, `skipped`, or `not_required` unless corresponding spec arrays are present.
- Every confirmation must include evidence: `user_confirmed` uses `questionId`/`interactionId`, and `repo_inferred` uses `repoEvidence`.

Complex condition example:

```yaml
conditions:
  - fromActivity: "申请"
    toActivity: "人工复核"
    transitionname: "人工复核"
    conditionname: "年龄大于20"
    conditionexpressiontype: 10
    leftvalue: "[#=age#]"
    lefttext: "年龄"
    compareoperation: ">"
    rightvalue: "20"
    righttext: "20"
    valuetype: 30
    ordernum: 0
  - fromActivity: "申请"
    toActivity: "人工复核"
    transitionname: "人工复核"
    conditionname: "性别是男"
    conditionexpressiontype: 10
    leftvalue: "[#=gender#]"
    lefttext: "性别"
    compareoperation: "="
    rightvalue: "male"
    righttext: "男"
    valuetype: 10
    ordernum: 1
  - fromActivity: "申请"
    toActivity: "人工复核"
    transitionname: "人工复核"
    conditionname: "年龄大于20且性别男"
    conditionexpressiontype: 20
    conditionexpression: "[1] AND [2]"
    ordernum: 2
```

### event

```yaml
spec:
  name: "提交后状态联动"
  sign: "submitStatus"
  triggerType: "webhook"
  apptag: "purchaseproject"
  bizAction: "PurchaseProjectRestService_submitStatus"
  bizTitle: "提交并更新状态"
  contextClass: "com.epoint.purchaseproject.context.PurchaseProjectContext"
  webhookUrl: ""
  nodes: []
```

Rules:

- Standard CRUD does not create event unless the user explicitly requires event.
- Standard three-stage event can omit `nodes`; `add_event.py` will generate the known skeleton.
- Advanced branch/loop/code event must keep `nodes` in IR and should be reviewed with event references before generation.

## 4. 待确认问题 open_questions

> 关键点：任何会影响生成结果的业务事实不明确时，必须写成 open question；只要还有 `status: pending` 的问题，就不允许生成。安全技术默认（如 `pagedesigne.device=desktop`）可不阻断但需写入计划假设；危险默认（如未知审批人角色 GUID、缺 MIS 字段类型）必须阻断生成。

```yaml
open_questions:
  - id: "q-001"
    target: "asset-002"
    field: "mis.fields[3].fieldType"
    severity: "blocking"
    question: "附件字段的字段类型和长度是否确认？"
    options: ["nvarchar(500)", "text"]
    recommended: "nvarchar(500)"
    status: "pending"
    answer: ""
    resolvedValue: ""
```

Allowed statuses: `pending`, `resolved`.
Allowed severity values: `blocking`, `confirm`, `info`.

No generation is allowed while any open question has `status: pending`.
When `status=resolved`, blocking/confirm questions must include the user's `answer` and parsed `resolvedValue`.
Question `target` may be an asset id, or one of `application`, `task`, `global`.

Uncertainty policy:

- Business facts that affect generated DSL must become open questions before generation: role/permission source, data fields, field types, workflow branch logic, webhook URLs, context classes, table operation mappings, and external method/rule references.
- Safe technical defaults may be filled without blocking only when documented in the plan assumptions, for example `pagedesigne.device=desktop` when the user did not mention mobile/H5/small-screen.
- `developerstag=epoint` and `kitid=businessprocess` are recommendations, not invisible defaults. They must be marked `user_confirmed` or `repo_inferred`.
- `categories=[]` is not “unknown”; it means the user/repo confirmed no classification.
- Dangerous defaults must block generation. Examples: unknown workflow approver role GUID, missing MIS field type, condition placeholders without `workflowContext`, event table operation without field mappings.

## 5. 校验合同 Validation Contract

> 关键点：按下列顺序执行校验。`add_workflow.py` 只用于 `operationMode=create`，`update_workflow.py` 只用于 `update-existing`，`revise-plan` 只更新计划/IR/预览不落盘。event 资产把 workflow 命令换成 `ir_to_event_args.py`、`add_event.py`、`check_dsl.py`。

Run in order:

```bash
python3 scripts/validate_ir.py .lowcode-plans/<apptag>/ir.yml
python3 scripts/validate_plan.py .lowcode-plans/<apptag>-plan.md
python3 scripts/workflow_preview.py --from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <workflow-asset-id>
python3 scripts/ir_to_workflow_args.py .lowcode-plans/<apptag>/ir.yml --asset-id <workflow-asset-id>
python3 scripts/add_workflow.py --from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <workflow-asset-id> --dry-run
python3 scripts/add_workflow.py --from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <workflow-asset-id>
python3 scripts/update_workflow.py --workflow-file <workflow-file> --from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <workflow-asset-id> --dry-run
python3 scripts/validate_yml.py --check-ir-consistency .lowcode-plans/<apptag>/ir.yml <app-root>
```

Use `add_workflow.py` only for `operationMode=create`. Use `update_workflow.py` for `operationMode=update-existing`. For `operationMode=revise-plan`, update plan/IR/preview only.

For event assets, replace workflow commands with `ir_to_event_args.py`, `add_event.py`, and `check_dsl.py`.
