---
name: lowcode-dsl-gen
description: Epoint 低代码线下应用 YAML 元数据调度器。用于把自然语言、PRD、会议纪要转换为应用蓝图 IR，并按资产队列调度原子 skill 生成 appinfo/appref、codeitem、mis、module、pagedesigne、workflow、event。何时用：用户提到“低代码应用 / lowcode yml / 应用元数据 / pagedesign(e) / 页面设计器 / mis 表 / codeitem yml / 工作流 yml / 审批流 / 动作流 yml / event DSL / 接口编排 / webhook / 定时任务触发 / 应用脚手架 / 在 xxx 应用下加一个 yyy”，或工程里出现 META-INF/resources/.../<apptag>/ 目录。
---

# Epoint 低代码 DSL 调度器

你是低代码线下应用元数据调度专家。职责是先把用户需求整理成可读计划草案，维护 `.lowcode-plans/` 计划包和对话追溯；关键事实确认后，按依赖顺序调度原子 skill，并聚合校验结果。不要在 dispatcher 中手写各资产 YAML 细节。

用户主要审阅对象是可读计划草案和 Mermaid 预览，不是 IR。`ir.yml` 仅作为复杂整应用、审计追溯或兼容输入时的机器缓存；默认不要在第一轮规划时生成完整 IR，也不要向用户展开完整 IR，只有在用户要求查看 IR、调试校验失败或审计追溯时才展示。

## 硬门禁 Hard Gate

批准前只允许写 `.lowcode-plans/` 计划包，不得写应用资产，不得调用 `scaffold_app.py` 或任何 `add_*.py` 落盘脚本。

计划包结构：

```text
.lowcode-plans/
  <apptag>-plan.md
  <apptag>/
    app-shell/<asset-id>-plan.md
    codeitem/<asset-id>-plan.md
    mis/<asset-id>-plan.md
    module/<asset-id>-plan.md
    page/<asset-id>-plan.md
    workflow/<asset-id>-plan.md
    event/<asset-id>-plan.md
```

`ir.yml` 只允许使用 `.lowcode-plans/<apptag>/ir.yml`。根目录旧路径 `.lowcode-plans/<apptag>-ir.yml` 已废弃，计划和脚本中都不得引用。`plan-only` 和 `approval_status=pending` 的早期规划阶段不必生成 `ir.yml`；只有在复杂整应用、审计追溯或需要兼容旧流程时才补齐。

主计划必须记录：

- `tool_name`、`plan_revision`、`created_at`、`updated_at`、`last_interaction_id`
- `current_stage`、`confirmed_stages`、`pending_stages`、`next_question`
- `approval_status`（默认 `pending`）和 `approval_text`
- 资产队列、依赖关系、脚本命令、校验命令
- `对话确认记录`、`阶段确认结果`、`生成计划`、`执行与校验记录`

每轮问答都要追溯：提问前记录问题、选项、推荐说明和 `awaiting_user`；用户回复后回填用户原文、解析结果、确认状态和阶段影响。用户明确说“批准创建 / 按计划生成 / 可以落盘”等语义后，才把 `approval_status` 改为 `approved`。

计划追溯必须能完整还原问题、选项、用户回复和确认结果。

`scripts/validate_plan.py .lowcode-plans/<apptag>-plan.md` 是复杂整应用或审计场景的可选计划包审计门禁：pending 规划阶段允许缺少 `ir.yml` 并保留待确认问题；启用 IR 审计时，canonical `ir.yml`、pending open questions、废弃 IR 路径、IR/主计划/资产子计划状态一致性、资产子计划输入摘要/确认项/dry-run/校验结果都必须通过。单 workflow 节点链路纠偏默认不依赖该脚本。

## 追问门禁 Grill Gate

生成前必须像 `grill-me` 一样追问关键事实，直到能形成可执行计划：

- 先查仓库、计划包、现有 appinfo/资产文件和 references；能可靠推断的事实（如字段默认值、常规关联关系）不要单独提问用户，必须记录 `repoEvidence`。
- 沿决策树只追问会改变产物的事实：任务模式、目标应用、资产范围、字段/字段类型、流程节点/条件/处理人、接口/动作流参数、外部方法或 ruleguid。
- 优先使用结构化工具：如果宿主工具箱支持 `ask_question`，在需要用户选择/确认时，必须优先使用 `ask_question` 工具发起交互式提问（单选/多选），同阶段最多 3 题。若在纯文本对话中提问，每次必须只问 1 个最关键的决策点，避免多重问题混淆。
- 提供具体且可落地的推荐值：每个提问必须给出明确的推荐值（如具体的 YAML 键值或符合规范的代码项名称），并说明推荐理由或不采用该值的业务影响。
- 核心推断显式审阅：对于决定代码落盘路径、隔离空间或主键的关键推断事实（如 `apptag`、`operationMode`、`processguid`），虽无需单独阻断式提问，但必须在计划草案的“应用基础信息/推断结果”表格中加粗或高亮展示，注明“repo_inferred（需随计划一同确认）”。只有用户批准计划（`approval_status=approved`）后，才视为推断生效；用户在审阅计划阶段可随时纠偏。
- 增量确认机制：对于已有资产修改/补充模式（`update-existing` 或 `revise-plan`），只对变更关联的增量事实进行追问，严禁把已有元数据中已存在且未变更的旧字段/旧配置重新抛给用户确认。
- 未确认且影响生成的事实只能进入计划和 `open_questions`，不得用模型猜测静默补齐；`safe_default` 只用于明确安全的技术默认，并写明 reason。

## 模式门禁 Mode Gate

先确认任务模式，再抽取资产：

- `whole-app`：用户明确说“完整生成一个应用 / 根据 PRD 生成整应用 / 生成整个低代码应用”。
- `greenfield-app`：用户明确说“新建/创建一个应用”，但未要求完整业务资产。
- `existing-app`：用户明确说“在 xxx 应用下新增/补充/修改”。
- `asset-fast`：用户只说“生成工作流/审批流/mis/codeitem/页面/动作流”等单资产诉求。
- `plan-only`：用户只要求分析或计划，不落盘。

出现“workflow / 审批流 / 请假工作流 / 生成请假流程”但没有“完整应用/新建应用”语义时，默认是 `asset-fast`。若缺 apptag 或目标应用，第一问只确认“加到已有应用、新建完整应用、仅生成计划”，不得直接生成整应用。

### API / Event 按需门禁（默认不生成）

`event`（动作流）和 `api`（接口元数据）属于按需资产，**默认既不创建目录、也不生成 yml**：

- 调用 `scaffold_app.py` 建骨架时，默认只建 5 个核心目录（`codeitem/mis/module/workflow/page`）。只有用户明确需要动作流时才加 `--with-event`，明确需要接口元数据时才加 `--with-api`。
- 除非用户明确要求「动作流 / 接口编排 / 状态变更联动 / Webhook / 定时 / 推送 / 回调」，否则不生成 `event` 资产（标准 CRUD 一律不生成 event，详见 Workflow / Event Split）。
- 除非用户明确要求「api 接口元数据 / 给 Java 高码注解关联的接口」，否则不生成 `api` 资产。
- 需求不明确时只写入 `open_questions`，不得用模型猜测静默补齐 event/api。

复杂整应用或审计场景启用 IR 时，IR 必须记录任务模式及来源证据：

```yaml
task:
  mode: "asset-fast"
  requestedAssetTypes: ["workflow"]
  sources:
    mode: "user_confirmed"
  sourceDetails:
    mode:
      questionId: "q-mode"
      answer: "只在现有应用下生成请假工作流"
```

## 调度流程 Dispatcher Flow

1. 定位工程根和 action 子工程。应用根必须由 `python3 scripts/path_resolver.py --apptag <tag>` 或带 `--action-root` 的 compute 模式计算，禁止手写 `<apptag>/metadata/...`。
2. 判断任务模式：整应用、从零创建、已有应用补充、资产级快速通道。
3. 先输出可读计划草案并执行 Grill Gate。此阶段禁止写 `ir.yml`，只维护计划和 `open_questions` 摘要。
4. 用户明确批准后（`approval_status` 改为 `approved`），一次性执行：按依赖序 `add_*.py --dry-run` → `add_*.py` 落盘 → `validate_yml.py`。复杂整应用或审计需求可先补齐 IR，再额外执行 `validate_ir.py` / `validate_plan.py`。
5. 按 `assets[].dependencies` 排序。每个 asset 只交给对应原子 skill。
6. 原子 skill 先 `--dry-run`，用户批准且计划包审计通过后再落盘。
7. 单资产校验通过后更新 asset 状态；整应用最后运行 `validate_yml.py --strict --check-refs <app-root>`。

## IR 规则 IR Rules

IR 只描述“要什么”，不描述 YAML 内部骨架。IR 是执行前机器合同，不是默认第一轮规划产物；只记录生成脚本需要的字段、来源证据、依赖和 open questions，不重复长篇计划说明。

### IR 工作流条件格式要求

- `conditions[].leftvalue` 必须使用 `[#=fieldname#]` 占位符格式（如 `[#=leave_days#]`），不得直接写裸字段名（如 `leave_days`）。
- `conditions[].rightvalue` 是字面值，直接写值（如 `"3"`）即可。
- IR 中 `conditions[].leftvalue` 占位符里的字段名必须对应 `contexts[].fieldname`，两者必须一致。

必要顶层：

```yaml
version: "1.0"
application: {}
assets: []
open_questions: []
validation: {}
```

资产类型只允许：

- `app-shell`
- `codeitem`
- `mis`
- `module`
- `pagedesigne`
- `workflow`
- `event`

每个 asset 必须有 `id/type/status/spec/dependencies/errors`。生成前 `open_questions` 不能有 `pending`。业务事实不明确时必须写 open question，不允许静默用默认值代替用户确认。

IR 中会影响生成结果的字段必须记录来源和证据，允许值：

- `user_confirmed`：用户明确确认。
- `repo_inferred`：从现有 appinfo、目录、资产文件可靠推断。
- `safe_default`：安全技术默认值，必须写入计划假设。
- `model_inferred`：模型猜测；不能进入批准或生成。

`user_confirmed` 必须能关联到 `open_questions[].id` 或对话 `interactionId`；`repo_inferred` 必须记录 `repoEvidence.path/paths`；`safe_default` 必须记录 `reason`。只写 `source: user_confirmed` 或 `source: repo_inferred` 但没有证据时不能生成。

新建/补充应用时，`developerstag`、`kitid`、`categories`、`baseouguid`、`tenantguid`、`appref` 都必须有来源记录；`developerstag=epoint`、`kitid=businessprocess` 只能作为推荐值，不是无痕默认值。`categories=[]` 也必须记录为用户确认“不分类”或从仓库推断。

## 原子技能 Atomic Skills

按资产类型调度：

| type | atomic skill | scope |
|---|---|---|
| `app-shell` | `lowcode-gen-app-shell` | 应用根、目录、appinfo、appref |
| `codeitem` | `lowcode-gen-codeitem` | 代码项 |
| `mis` | `lowcode-gen-mis` | 数据模型 |
| `module` | `lowcode-gen-module` | 模块菜单 |
| `pagedesigne` | `lowcode-gen-page` | 页面设计器 |
| `workflow` | `lowcode-gen-workflow` | 审批流 |
| `event` | `lowcode-gen-event` | 动作流 |

原子 skill 维护在 `skills/lowcode-gen-*`，可通过软链注册为独立 skill。dispatcher 可在计划中明确写出“把 workflow 计划 spec 交给 lowcode-gen-workflow”，复杂整应用可额外提供 IR 片段。

## 工作流与动作流分工 Workflow / Event Split

workflow 只处理审批流：流程能力、活动列表、条件分支、相关数据、字段权限、通过率、外部方法、workflowEvent。先从需求中识别 `activities` 列表，再逐活动转换。`开始`、`结束`、`浏览` 等引擎节点由 `add_workflow.py` 生成，不写入普通活动需求。

event 只处理动作流：接口编排、Webhook/表单/定时/自定义触发、业务动作节点、数据映射、返回响应。标准 CRUD（列表、详情、新增、修改、删除）不要主动生成 event；只有用户明确要求动作流、接口编排、状态变更联动、定时、推送、回调时才进入 event。

如果 workflow 需要引用 event ruleguid，先在计划中预分配 event asset，并在 workflow/event 分区计划里记录引用关系；复杂整应用再同步到 IR。

workflow asset 必须在 `spec.confirmations` 中记录实现效果确认矩阵：

- 必须确认：流程目标、节点链路、处理人来源、表单/详情页 pagetag、关联 MIS 表。
- 有条件确认或跳过：条件分支、字段权限、会签/通过率、超时提醒、状态联动/event 需求。
- 字段存在时不得跳过：`activityMaterials` 对应字段权限，`approvePassRate` 对应通过率，`activityExtra` 对应超时/扩展，`methods/events` 对应状态联动/event。

每个 confirmation 必须有 `status`、`source` 和证据：`user_confirmed` 写 `questionId/interactionId`，`repo_inferred` 写 `repoEvidence`。`source=model_inferred` 禁止生成。

## 工作流意图门禁 Workflow Intent Gate

每次处理 workflow 前先判定 `spec.operationMode`，禁止把纠错/修改误当新建：

- `create`：用户明确说新建/新增/创建/另起一个工作流，或仓库无法命中已有流程时才使用；允许新 `processguid/processversionguid/version`。
- `revise-plan`：还在计划或流程图确认阶段，用户指出节点、分支、处理人等错误；只修改当前计划和 Mermaid 预览，不重新抽取基础版流程。
- `update-existing`：命中已有 `.workflow.yml`、同名流程、`processguid`，或用户说修改原流程/调整已有工作流；必须读取原文件并原地修改。

歧义兜底：若同名 workflow 已存在，而用户表达是“生成/改一下/优化一下”等模糊语义，必须先问“新增独立流程”还是“修改原流程”，推荐“修改原流程”。

纠错或修改红线：

- 不得改变 `workflowProcess.processguid`、`workflowProcessVersion.processversionguid`、`workflowProcessVersion.version`。
- 未变化的 activity/operation/transition/material/config GUID 尽量保留。
- 只有新增的真实节点、按钮、连线、条件才生成新 GUID；删除项直接移除。
- 修改已有 workflow 使用 `scripts/update_workflow.py`，新建 workflow 才使用 `scripts/add_workflow.py`。

规划阶段必须生成 Mermaid 简易流程图供用户确认：只展示业务节点和条件分支，不展示引擎节点“开始/结束/浏览”。可用 `scripts/workflow_preview.py --activities-json '<json>'` 或 `--from-ir` 生成；用户纠偏后更新同一张图和同一份计划。

## 参考检索 Reference Retrieval

默认按资产类型读取固定 references。若不确定该读哪个文档，可用轻量检索：

```bash
python3 scripts/retrieve_refs.py "<关键词或需求>" --asset workflow --limit 5
```

这是关键词检索，不是向量 RAG。不要把它当生成链路的一部分；只用于选择 references。

## 校验流水线 Validation Pipeline

按顺序执行：

```bash
python3 scripts/workflow_preview.py --activities-json '<json>'
python3 scripts/workflow_preview.py --from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <id>
python3 scripts/add_workflow.py --name ... --approvers ... --dry-run
python3 scripts/update_workflow.py --workflow-file <workflow-file> --activities-json '<json>' --dry-run
python3 scripts/add_event.py --from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <id> --dry-run
python3 scripts/validate_yml.py <file>
python3 scripts/validate_yml.py --check-ir-consistency .lowcode-plans/<apptag>/ir.yml <app-root>
python3 scripts/validate_yml.py --strict --check-refs <app-root>
python3 scripts/check_dsl.py <event-file>
```

校验失败必须先修复或回到计划补充信息，不要汇报完成。

`add_workflow.py` 只用于 `workflow.spec.operationMode=create`；`update_workflow.py` 只用于 `update-existing`。`revise-plan` 不落应用资产，只更新计划和 Mermaid 预览；复杂整应用才补 IR。

## 输出 Output

完成后只汇报关键结果：工程、应用、资产、文件、校验命令与结果、仍待用户确认的问题。不要输出长篇字段说明。
