# 整应用生成工作流

当用户给出自然语言需求、会议纪要、需求文档或“帮我完整生成一个应用”时，先走本工作流，再落到各资产文档。

若用户只说“生成工作流 / 审批流 / 请假工作流 / 加一个流程”，且没有“完整应用/新建应用”语义，不进入整应用生成；按资产级快速通道处理，并先确认目标应用或是否改为新建完整应用。

## 固定确认顺序

整应用生成或分阶段补全时，确认顺序必须固定为：

1. 主体架构
2. 基本信息
3. codeitem
4. mis
5. module
6. pagedesigne
7. workflow
8. event
9. 最终批准

规则：

- 每次只确认当前阶段，当前阶段未确认前不提前问后续阶段。
- 每轮最多 3 个问题，只问当前阶段。
- 每确认一个阶段，就先输出该阶段的短摘要，再进入下一阶段。

## 执行原则

- 进入工作流即按 `SKILL.md` 的「计划文档与对话追溯门禁（唯一硬约束）」执行：批准前唯一可写文件是 `.lowcode-plans/<apptag>-plan.md`；不要尝试切换宿主模式或判断宿主工具集是否暴露 `request_user_input` / `/plan`。
- 第一轮就创建/更新计划文档，并把每轮问题、选项、用户回复、解析结果和确认状态写入 `对话确认记录`。Plan Mode / 结构化问答只是提问方式不同，不改变追溯要求。
- **路径红线（spec v2）**：进入主体架构阶段，**第一步**就要用 `python3 scripts/path_resolver.py --apptag <tag>` 算出应用根目录绝对路径，并把结果原样写进计划文档的"目标目录 / 应用根 / app-root"字段。**严禁**手动拼出 `<apptag>/metadata/<asset>/...` 这样的路径——脚本会 fail-fast 拦下，应用根永远不应该带 `metadata/` 这一层。计划文档里也禁止使用"metadata 目录"这种措辞，统一写"应用根目录"。
- 先把业务需求整理成"应用蓝图"，但要按固定确认顺序逐段补齐，不要直接写 yml/json。
- IR 统一写 `.lowcode-plans/<apptag>/ir.yml`；不得再创建或引用 `.lowcode-plans/<apptag>-ir.yml`。
- 每一步只读取当前需要的参考文档，避免一次性加载所有 references。
- 计划文档必须持续更新，覆盖将新增/修改的应用、资产类型、目标文件、脚本命令和校验方式，并清楚列出当前阶段、已确认阶段、待确认阶段和下一步只问什么。全部阶段确认后，只整理 `生成计划` 章节为最终版，不重新另建计划。
- 用户明确说"批准创建 / 按计划生成 / 可以落盘"后，才调用脚本或写文件。
- 每个资产生成后立即校验；整批完成后再对应用根目录执行 `validate_yml.py --strict --check-refs <app-root>`（spec v2 严格模式，已废弃字段 / metadata 残留 / 旧驼峰键 一律升级为 error）。

> **event 阶段的边界（重要）**：用户提到列表 / 详情 / 新增 / 修改 / 删除时**不要主动建议生成动作流**——这些标准 CRUD 走 MIS 接口或 REST 接口直接提供。
>
> 当前阶段 skill **只把"状态变更联动"作为主动建议进入 event 阶段的场景**：
>
> - **状态变更联动**（dispatch / approve / reject / archive / cancel / submit / revoke，需同时改状态位、写日志、发消息）
>
> 以下场景属于"高级场景"，**仅当用户明确表达诉求时**才进入 event 阶段，不要主动建议：
>
> - 跨系统推送拉取（push / pull / notify / sync 外部接口）
> - 定时同步（Cron 触发、批量处理）
> - 工作流回调（method.ruleguid / workflowEvent.ruleGuid / workflowTransitionCondition.ruleGuid）
> - 多节点编排（条件、迭代、代码节点等）
>
> 反例：**不要**给用车申请这类业务主动建议 `getDataGridModel / getDetail / saveOrUpdate / delete`；这些都是标准接口。详见 `references/event/动作流/index.md` § 1。

## 5 阶段 12 步

| 阶段 | 步骤 | 动作 | 输出 |
|------|------|------|------|
| 阶段一：输入识别 | 1 | 判断输入是新建应用、补充已有应用还是单资产生成，并创建/更新计划文档 | 任务类型 + 计划初版 |
| 阶段一：输入识别 | 2 | 确认工程根、action 子工程、应用根目录或待创建目录，并记录问答追溯 | 目标边界 + 对话确认记录 |
| 阶段二：应用蓝图 | 3 | 抽取应用基础信息、套件、分类、标识建议 | application |
| 阶段二：应用蓝图 | 4 | 抽取业务对象、字段、字典、页面、菜单、接口、流程 | assets 草案 |
| 阶段三：资产拆分 | 5 | 把蓝图映射到 8 类应用资产 | 资产拆分表 |
| 阶段三：资产拆分 | 6 | 梳理依赖关系，如 mis 字段引用 codeitem、页面 action 调用 resource | 依赖表 |
| 阶段三：资产拆分 | 7 | 为每个资产选择脚本、模板或手工补充策略 | 生成方式 |
| 阶段四：计划落盘 | 8 | 整理目标文件、覆盖策略、脚本命令、校验方式 | `.lowcode-plans/<apptag>-plan.md` 的生成计划章节 |
| 阶段四：计划落盘 | 9 | 等待用户明确批准 | 批准记录 |
| 阶段四：计划落盘 | 10 | 调用脚本或按模板写盘 | 新增/修改文件 |
| 阶段五：验证归档 | 11 | 运行单文件校验、资产清单、跨引用校验 | 校验结果 |
| 阶段五：验证归档 | 12 | 汇报完成情况、关键文件、风险和下一步 | 校验报告 |

阶段四是硬门禁：没有明确批准，只能维护计划文档，不调用脚本、不写应用资产、不覆盖已有文件。

## 步骤文件

| 步骤 | 文件 | 作用 |
|------|------|------|
| 1 | `workflow/01-requirement-recognition.md` | 识别输入材料、应用边界和缺失信息 |
| 2 | `workflow/02-app-blueprint.md` | 形成应用蓝图 |
| 3 | `workflow/03-asset-breakdown.md` | 拆成 8 类应用资产 |
| 4 | `workflow/04-generation-plan.md` | 输出落盘计划并等待批准 |
| 5 | `workflow/05-validation-report.md` | 校验和回报 |

## 蓝图最小字段

```yaml
task:
  mode: <whole-app | greenfield-app | existing-app | asset-fast | plan-only>
  requestedAssetTypes: []
  sources:
    mode: user_confirmed
application:
  applicationname: ""
  apptag: ""
  developerstag: epoint
  kitid: businessprocess
  baseouguid: ""
  categories: []
  sources:
    developerstag: user_confirmed
    kitid: user_confirmed
    baseouguid: safe_default
    tenantguid: safe_default
    categories: user_confirmed
assets:
  codeitem: []
  mis: []
  module: []
  event: []
  workflow: []
  pagedesigne: []
open_questions: []
```

## 资产拆分表格式

```markdown
| 资产类型 | 资产名称 | 目标文件 | 生成方式 | 依赖 |
|----------|----------|----------|----------|------|
| codeitem | 审核状态 | codeitem/审核状态.codeitem.yml | add_codeitem.py | mis.audit_status |
| mis | purchaseproject | mis/purchaseproject.mis.yml | add_mis_field.py --create | codeitem.审核状态 |
| pagedesigne | 采购立项列表 | page/采购立项列表.json | add_page.py --type list | event.getDataGridModel |
```

## 生成计划必须包含

- 当前工具名称：`tool_name`（无法识别时写 `unknown-cli-agent`）。
- 追溯字段：`plan_revision` / `created_at` / `updated_at` / `last_interaction_id`。
- 计划文档路径：`.lowcode-plans/<apptag>-plan.md`。
- IR 路径：`.lowcode-plans/<apptag>/ir.yml`。
- 目标 应用根目录。
- `对话确认记录`：每轮问题、选项、推荐说明、用户原文、解析结果、确认状态。
- `阶段确认结果`：每个阶段的确认摘要、用户确认原文、是否还有待确认信息。
- 新增、修改、跳过、覆盖的文件清单；如需 `--force` 必须明说。
- 每个脚本的用途和关键参数，不要求用户自己理解 CLI。
- 校验命令：单文件校验 + `validate_yml.py --strict --check-refs <app-root>`。
- 仍未确认的信息，不能伪装成确定值。
- 来源追踪：`developerstag`、`kitid`、`categories`、`baseouguid`、`tenantguid`、`appref` 必须记录 `user_confirmed`、`repo_inferred` 或允许的 `safe_default`；`model_inferred` 不得进入批准。
- 每个资产必须有 `.lowcode-plans/<apptag>/<asset-type>/<asset-id>-plan.md` 子计划；主计划只做汇总，不承载资产细节。
- 未要求动作流时，`event` 必须标注“仅保留目录，不生成 `.event.yml`”。
- `codeitem` 未确认子项、`mis` 未确认字段清单时，只能放入待确认问题，不能列入可执行脚本。
- workflow 阶段必须有实现效果确认矩阵：流程目标、节点链路、处理人来源、条件分支、表单/详情页 pagetag、关联 MIS、字段权限、会签/通过率、超时提醒、状态联动/event 需求。

> 完整的计划文档字段（`plan_revision` / `last_interaction_id` / `current_stage` / `confirmed_stages` / `pending_stages` / `next_question` / `approval_status` / `approval_text`）和 `对话确认记录` 要求见 `SKILL.md` 的「计划文档与对话追溯门禁」节，本节不重复。

## 校验报告必须包含

- `inventory_metadata.py --app-root <app-root>` 的资产数量摘要。
- `validate_yml.py --strict --check-refs <app-root>` 的结果。
- 页面 schema 的引用闭合情况：events、source、model/textModel、actions.steps。
- appref 和 mis 字典引用风险。
- 最多列 5 个关键文件，避免把长路径刷屏。

## 跳转规则

- 缺应用核心信息：回到 `references/appinfo/应用配置/index.md` 的对话流程。
- 缺字段/表结构：读 `references/mis/数据模型/index.md`。
- 缺页面信息：读 `references/page/页面设计器/index.md`，优先使用 `scripts/add_page.py`。
- 缺流程节点：读 `references/workflow/工作流/index.md`。
- 缺接口编排：读 `references/event/动作流/index.md`。
