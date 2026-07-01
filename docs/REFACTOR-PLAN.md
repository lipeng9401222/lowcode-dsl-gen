# lowcode-dsl-gen 原子化重构整合计划

> 版本: v2.0 | 日期: 2026-06-08 | 状态: implementation-ready

## 1. Summary

将当前单体 `lowcode-dsl-gen` 改造成：

```text
dispatcher skill -> IR 中间语言 -> atomic skills -> deterministic scripts -> validation pipeline
```

主 skill 只做自然语言需求识别、IR 输出、依赖编排、计划追溯和校验聚合；各原子 skill 只负责单类 DSL 生成。`lowcode-gen-scaffold` 不再作为原子 skill 名称，改为 `lowcode-gen-app-shell`，负责应用根、标准目录、`appinfo.lowcode.yml` 和可选 `appref.lowcode.yml`。

RAG 不做完整向量化方案。只增加轻量 `scripts/retrieve_refs.py`，在不确定应读哪个 reference 时按资产类型和关键词检索 3-5 篇最相关文档。

## 2. Target Architecture

```text
Layer 0  lowcode-dsl-gen dispatcher
         自然语言/PRD -> 应用蓝图 IR -> 资产任务队列 -> 计划追溯 -> 原子调度

Layer 1  IR contract
         docs/IR-SPEC.md + schemas/app-blueprint.schema.yml + schemas/examples/*.ir.yml

Layer 2  atomic skills
         lowcode-gen-app-shell / codeitem / mis / module / pagedesigne / workflow / event

Layer 3  deterministic scripts
         add_*.py + ir_to_*_args.py + retrieve_refs.py

Layer 4  validation
         validate_ir.py -> validate_plan.py -> add_*.py --dry-run -> validate_yml.py -> check_dsl.py
```

原子 skill 采用“仓内统一维护，可软链注册为独立 skill”的形式：本仓 `skills/lowcode-gen-*` 下维护 `SKILL.md`，共享根目录 `references/`、`scripts/` 和 `assets/templates/`。

## 3. Dispatcher Scope

`lowcode-dsl-gen` 只保留以下职责：

- 识别任务模式：整应用、从零创建、修改补充、资产级快速通道。
- 从自然语言、PRD、会议纪要抽取 `application`、`assets[]`、`open_questions[]`。
- 先生成 IR，再调用 `scripts/validate_ir.py`。
- 用疑点策略把业务不确定项写入 `open_questions[]`；未确认时停止在计划阶段。
- 根据 `assets[].dependencies` 做拓扑排序。
- 维护 `.lowcode-plans/` 计划包和批准门禁。
- 按资产类型调度原子 skill，并聚合产物校验结果。

dispatcher 不再承载各资产字段白名单、复杂 workflow 节点字段、event 节点细节。字段细节下沉到原子 skill 和对应 references。

## 4. IR Contract

IR 顶层结构：

```yaml
version: "1.0"
application:
  apptag: ""
  applicationname: ""
  developerstag: "epoint"
  kitid: "businessprocess"
  tenantguid: ""
  baseouguid: ""
  categories: []
assets:
  - id: "asset-001"
    type: "mis"
    status: "pending"
    dependencies: []
    spec: {}
    errors: []
open_questions: []
validation:
  status: "pending"
  reports: []
```

核心原则：

- IR 描述“要什么”，不描述 YAML 内部骨架。
- 每个资产是一个任务，必须有唯一 `id` 和明确 `type`。
- `workflow.spec.activities` 必填，先识别活动数量、名称、顺序，再由 `lowcode-gen-workflow` 转成 `add_workflow.py` 参数。
- `event.spec` 与 `workflow.spec` 分离。标准 CRUD 不进入 event。
- `open_questions` 未解决时，不能进入生成。
- `open_questions` 统一记录 `id/target/field/severity/question/options/recommended/status/answer/resolvedValue`；业务事实不明确时必须提问，安全默认值只可写入 assumptions。

完整字段定义见 `docs/IR-SPEC.md` 和 `schemas/app-blueprint.schema.yml`。

## 5. Atomic Skills

| Skill | 职责 | 输入 | 输出 |
|---|---|---|---|
| `lowcode-gen-app-shell` | 应用壳、目录、appinfo、appref | `application` + app-shell asset | 应用根目录、`appinfo.lowcode.yml`、可选 `appref.lowcode.yml` |
| `lowcode-gen-codeitem` | 代码项 | `assets[type=codeitem].spec` | `codeitem/*.codeitem.yml` |
| `lowcode-gen-mis` | 数据模型 | `assets[type=mis].spec` | `mis/*.mis.yml` |
| `lowcode-gen-module` | 模块菜单 | `assets[type=module].spec` | `module/*.module.yml` |
| `lowcode-gen-page` | 页面设计器 | `assets[type=pagedesigne].spec` | `page/*.page.yml` |
| `lowcode-gen-workflow` | 审批流 | `assets[type=workflow].spec` | `workflow/*.workflow.yml` |
| `lowcode-gen-event` | 动作流 | `assets[type=event].spec` | `event/*.event.yml` |

每个原子 skill 的 `SKILL.md` 只保留：

- 输入协议。
- 必读 references。
- 脚本调用规则。
- dry-run 与落盘校验。
- 幻觉红线。

## 6. Workflow / Event Plan Partition

计划包结构：

```text
.lowcode-plans/
  <apptag>-plan.md
  <apptag>/
    workflow/
      <asset-id>-plan.md
    event/
      <asset-id>-plan.md
```

主计划文件记录：

- 总 IR。
- 资产任务队列。
- 依赖关系。
- 批准状态。
- 全局校验结果。

workflow 分区只记录：

- 活动识别结果。
- `activities` 逐项转换。
- 条件分支、相关数据、字段权限、通过率、外部方法、workflowEvent。
- `add_workflow.py --dry-run` 和 `validate_yml.py` 结果。

event 分区只记录：

- 触发方式。
- 标准三段式或高级节点编排。
- 业务动作、context class、Webhook、数据映射。
- `check_dsl.py` 六项检查结果。

边界：

- 列表、详情、新增、修改、删除等标准 CRUD 不主动生成 event。
- 只有明确“动作流/接口编排/状态变更联动/定时/推送/回调”诉求才进入 event。
- workflow 引用 event ruleguid 时，IR 中预分配 event asset，并建立 `workflow.dependencies -> event` 或按实际生成顺序建立反向引用计划。

## 7. Engineering Validation

流水线：

```text
natural language -> IR
  -> validate_ir.py
  -> validate_plan.py
  -> atomic skill --dry-run / ir_to_*_args.py
  -> add_*.py --from-ir
  -> validate_yml.py
  -> validate_yml.py --check-ir-consistency <ir>
  -> validate_yml.py --strict --check-refs <app-root>
  -> check_dsl.py <event-file> for event
```

新增脚本：

- `scripts/validate_ir.py`：schema 轻量校验、依赖 DAG、asset id 唯一、open_questions 状态。
- `scripts/validate_plan.py`：审计 `.lowcode-plans` 主计划、对话确认闭环、批准语义、IR/主计划/资产子计划状态一致性。
- `scripts/ir_to_workflow_args.py`：workflow IR 到 `add_workflow.py` CLI 参数 JSON。
- `scripts/ir_to_event_args.py`：event IR 到 `add_event.py` CLI 参数 JSON。
- `scripts/retrieve_refs.py`：轻量 references 检索。

增强脚本：

- `scripts/add_workflow.py --from-ir <ir.yml> --asset-id <id> --dry-run`
- `scripts/add_event.py --from-ir <ir.yml> --asset-id <id> --dry-run`
- `scripts/validate_yml.py --check-ir-consistency <ir.yml>`

## 8. Implementation Phases

### Phase 1: 基础层

- 更新本计划文档。
- 新增 `docs/IR-SPEC.md`。
- 新增 `schemas/app-blueprint.schema.yml` 和 IR 示例。
- 实现 `scripts/validate_ir.py`。
- 调整计划文档结构，明确 workflow/event 分区。

### Phase 2: workflow/event 试点

- 新增 `skills/lowcode-gen-workflow/SKILL.md`。
- 新增 `skills/lowcode-gen-event/SKILL.md`。
- 实现 `ir_to_workflow_args.py`、`ir_to_event_args.py`。
- 给 `add_workflow.py`、`add_event.py` 增加 `--from-ir` 和 `--dry-run`。
- 增加 workflow/event 独立 evals。

### Phase 3: 其余原子 skill

- 新增 `lowcode-gen-app-shell`、`lowcode-gen-codeitem`、`lowcode-gen-mis`、`lowcode-gen-module`、`lowcode-gen-page`。
- 迁移主 `SKILL.md` 中资产细节到原子 skill。
- 每个原子 skill 保留脚本调用和校验规则。

### Phase 4: Dispatcher 收敛

- 精简主 `SKILL.md`。
- 固定“自然语言 -> IR -> 校验 -> 原子调度 -> 产物校验 -> 汇总报告”流程。
- 增加 `retrieve_refs.py` 作为可选辅助检索。

### Phase 5: 回归验证

- 保持原有 evals 通过。
- 新增 IR、dispatcher、atomic evals。
- 运行 `python3 scripts/lint_skill.py --strict`。

## 9. Test Plan

Dispatcher evals：

- 整应用需求能输出合法 IR。
- workflow/event 计划分区正确。
- 标准 CRUD 不误生成 event。
- 未解决 `open_questions` 时不允许进入生成。
- 依赖图有环或 asset id 重复时 `validate_ir.py` 失败。

Workflow evals：

- 简单审批流。
- 条件分支。
- 字段权限。
- 通过率。
- workflowEvent / method 关联 event ruleguid。

Event evals：

- 状态变更联动。
- Webhook 标准三段式。
- 定时/推送等高级场景仅在用户明确要求时生成。
- CRUD 反例不生成 event。

Final checks：

```bash
python3 scripts/lint_skill.py --strict
python3 scripts/validate_ir.py schemas/examples/simple-app.ir.yml
python3 scripts/validate_ir.py schemas/examples/workflow-condition.ir.yml
python3 scripts/validate_ir.py schemas/examples/workflow-event-link.ir.yml
python3 scripts/validate_yml.py --strict --check-refs <app-root>
python3 scripts/check_dsl.py <event-file>
```

## 10. Assumptions

- 原子 skill 采用仓内统一维护，可软链注册为独立 skill。
- 不做完整向量 RAG，先用轻量 reference 检索降低上下文选择成本。
- `add_workflow.py`、`validate_yml.py` 继续作为核心确定性能力，只增强不重写。
- `lowcode-gen-app-shell` 取代 `lowcode-gen-scaffold`，避免命名误导。
