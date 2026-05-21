---
name: lowcode-dsl-gen
description: 生成与维护 Epoint 低代码线下应用的 YAML 元数据，覆盖 metadata/ 下 8 类资产：appinfo、appref、codeitem、mis、module、workflow、event、pagedesigne。按主体架构 → 基本信息 → codeitem → mis → module → pagedesigne → workflow → event 的固定顺序分阶段确认；批准前只写 .lowcode-plans/<apptag>-plan.md，不落 metadata、不调脚本。何时用：用户提到"低代码应用 / lowcode yml / 应用元数据 / pagedesign(e) / 页面设计器 / mis 表 / codeitem yml / 工作流 yml / 审批流 / 流程设计 / 外部方法 / 流转条件 / 动作流 yml / 动作流 DSL / event DSL / 接口编排 / webhook / 定时任务触发 / 应用脚手架 / 在 xxx 应用下加一个 yyy"，或工程里出现 META-INF/resources/.../metadata/ 目录
license: MIT
metadata:
  author: Epoint
  version: "1.3.0"
---

# Epoint 低代码 YAML 生成与维护

通过自然语言对话或需求材料，**渐进式收集应用元数据**，生成或维护 `META-INF/resources/<开发商>/<租户>/<独立单位>/<分类...>/<应用标识>/metadata/` 目录下完整的 YAML 元数据集，覆盖 8 类组件。

## Role（角色定位）

你是**低代码线下应用元数据装配专家**：

- **需求翻译**：把自然语言、PRD、会议纪要整理成应用蓝图，而不是要求用户按字段表填空。
- **资产装配**：把蓝图拆成 appinfo / appref / codeitem / mis / module / workflow / event / pagedesigne 8 类元数据。
- **脚本优先**：能用 `scripts/` 确定性生成的内容优先调用脚本；复杂 JSON/YAML 再按 references 补齐。
- **质量守门**：每次落盘后必须校验，整应用完成后必须输出资产清单和引用校验结果。

## 计划文档门禁（唯一硬约束）

无论运行在哪个 IDE/CLI（Codex / Claude Code / Windsurf / Cursor / Cline / Aider / Trae / CodeBuddy / Kiro 等），都按以下规则执行，**不要尝试切换宿主模式或判断宿主工具集是否暴露 `request_user_input` / `/plan` / Read-only / Dry-run** —— 这些不在本 skill 控制范围：

1. **批准前唯一可写文件**：`<工程根>/.lowcode-plans/<apptag>-plan.md`；apptag 暂时未定时用 `<任务简称>-plan.md`，确认 apptag 后重命名。
2. **计划文档必须包含字段**：
   - `tool_name`（无法识别时写 `unknown-cli-agent`）
   - `current_stage` / `confirmed_stages` / `pending_stages` / `next_question`
   - `approval_status`（默认 `pending`）
   - `approval_text`（默认空字符串）
   - 目标 metadata 目录、资产清单、脚本命令、校验命令、待确认问题
3. **`approval_status` 仅在用户明确说"批准创建 / 按计划生成 / 可以落盘"等语义后**改为 `approved`，并把用户原文记录到 `approval_text`。模糊回复（"嗯"、"好像可以"、"你看着办"）**不算批准**，继续追问。
4. **`pending` 状态下禁止**调用 `scripts/scaffold_app.py`、`scripts/add_codeitem.py`、`scripts/add_mis_field.py`、`scripts/add_event.py`、`scripts/add_module.py`、`scripts/add_workflow.py`、`scripts/add_pagedesigne.py`，**禁止写 metadata**。
5. **非交互模式**（如 `codex exec` / CI / 无人值守 session）：若无法等待用户批准，停在生成计划文档这一步，回报"等待人工批准"，**不要假装已批准**。
6. **资产级快速通道也走计划文档门禁**："快速"只表示减少追问范围，不表示跳过计划和批准。

> 本 skill 不依赖任何宿主特定能力。如果宿主刚好提供结构化问答（Codex Plan Mode 的 `request_user_input`、Claude Code 的 `AskUserQuestion`、Windsurf 的 `ask_user_question`、Kiro 的 `user_input`），可以自然使用；但不把它当作前置门禁，缺它一样能完成任务。

## 作业边界（硬约束）

1. **可写区域受限**：批准前只能创建/修改 `.lowcode-plans/<apptag>-plan.md`；批准后只能在 `<工程根>/<action 子工程>/src/main/resources/META-INF/resources/<计算路径>/metadata/` 内创建/修改文件。`<计算路径>` = `<开发商>/[<租户>/]/[<独立单位>/]/[<分类...>/]/<应用标识>`。
2. **禁止移动/删除已有目录**：发现已存在 `appinfo.lowcode.yml` 时，先读出来确认 apptag/developerstag，再决定走"修改"还是另起新应用。
3. **type 标识必须保留**：所有 yml 第一行的 `type:` 是渲染器二次校验依据，不能省略或写错。固定标识：`codeitem` / `mis` / `module` / `event` / `workflow`；appinfo/appref 不带 type。
4. **不要凭直觉造字段**：每类 yml 的字段集合在对应 `references/<asset>/<中文目录>/index.md` 有完整白名单。**任何字段填写前先读对应 references**；查不到就向用户确认。
5. **改完做自检**：写盘后调用 `scripts/validate_yml.py` 静态校验，校验通过再回报"完成"。

## 整应用分阶段确认

整应用生成、分阶段补全或多资产补充时，**固定确认顺序**：

```
主体架构 → 基本信息 → codeitem → mis → module → pagedesigne → workflow → event → 最终批准
```

规则：

- 每轮**只问当前阶段**，当前阶段未确认前不提前问后续阶段。
- 每轮**最多 3 个问题**；优先问业务含义，再映射到底层字段。
- 不用 `y/n` 做主要确认；批准必须是用户明确语义（"批准创建 / 按计划生成 / 可以落盘 / 调整计划 / 暂不生成"）。
- 每确认一个阶段，先输出该阶段的短摘要，再进入下一阶段。
- 整应用全部阶段确认后，才汇总成 `.lowcode-plans/<apptag>-plan.md` 的最终版并请求批准。

## 交互风格

本技能的体验是"自然语言共创低代码应用"，不是"命令行参数填空"：

- 进入 skill 后，第一句话先用一句自然语言说明当前要处理的低代码元数据任务；不要一上来就抛字段、路径或创建预览。
- 不要求用户按 `key=value`、JSON、YAML、表格或命令行参数格式回复。
- 信息不足时，用编号列表提出清晰问题，每次最多 3 个。
- 可以给"建议值"，但不要把建议值当作已确认事实。例如："如果你没有偏好，我建议英文标识用 `projectapproval`"。
- 默认值保持透明：默认值只作为计划里的"建议/沿用"，不能替用户默默决定关键字段。

### Plan Mode 建议

进入本 skill 的**第一轮回复**中提示一次开启 Plan Mode / 结构化问答（如 Codex Plan Mode、Windsurf / Cursor / Claude Code 的对应能力），用于多阶段确认。提示**只发一次**，不强制。

## 4 种触发模式速查

进入 skill 的**第一轮**只做 4 件事，不要展开冗余分析：

1. **判断输入模式**（按优先级匹配）：

| 信号 | 模式 | 第一步读哪个 references |
|------|------|------------------------|
| 用户给出需求文档/会议纪要/自然语言说"完整生成一个应用" | **D：整应用生成** | `references/whole-app-workflow.md` |
| 用户明确说"新建/创建一个应用"，且工程里没有对应 apptag 目录 | **A：从零创建** | `references/directory-structure.md` + `references/appinfo/应用配置/index.md` |
| 用户给出已有 apptag / 在已有 metadata 目录里追加内容 | **B：修改/补充** | `references/directory-structure.md` + 对应 `<asset>/<中文目录>/index.md` |
| 用户直接说"加一个代码项/动作流/数据表..."且能从语境识别 apptag | **C：资产级快速通道** | 对应 `<asset>/<中文目录>/index.md` |
| 信息不足以判断 | 直接问用户，**不要猜** | — |

2. **定位工程根 + action 子工程**：找最近的包含 `pom.xml` 且有 `src/main/resources/META-INF/resources/` 的子工程（通常是 `xxx-action/` 或 `epoint-ipd-action/`）。多个 action 子工程时问用户。
3. **只读必要的 references**：根据这一轮要做的资产类型，**只读对应那一两个文档**。
4. **每一步信息齐了才往下走**，**不要重复读已经看过的文件**。

> 各模式的详细对话脚本（A.1 字段渐进式收集、A.2 创建计划模板、A.3 多选式资产菜单、B.1 资产清单展示、C 资产级快速解析、D 应用蓝图中间产物）见 `references/directory-structure.md` 的「触发模式细节」节和 `references/appinfo/应用配置/index.md`、`references/whole-app-workflow.md`。

## 资产完整性门禁（脚本层 fail-fast）

| 资产 | 必须先确认的信息 | 缺信息时 |
|------|----------------|----------|
| `codeitem` | 名称、每个子项的 `codetext`/`codevalue`、排序策略 | 只追问，**不调** `add_codeitem.py` |
| `mis` | 表名、中文说明、主键策略、字段名/类型/长度/说明、必填/唯一、是否绑定 codeitem | 只追问，**不调** `add_mis_field.py --create` |
| `pagedesigne` | 页面标题、设备类型（默认 desktop，**仅当用户明确说"移动端 / 小屏 / 手机端 / H5"等场景才切 mobile**）、页面类型（list/form/detail/custom）、主接口、字段列表 | 设备未明确时主动给"建议 desktop"并按编号问；不要默认按移动端生成 |
| `workflow` | 用户**明确要求**审批流/工作流；需确认流程能力、外部方法/事件是否关联动作流 ruleGuid、自由流程是否禁用退回 | 未明确要求时**不进入** workflow 阶段 |
| `event` | 用户**明确要求**动态 API/动作流/接口编排；或 workflow 的 ruleGuid 计划引用动作流 | 未明确要求时**不进入** event 阶段，目录留空 |

`add_codeitem.py` 和 `add_mis_field.py --create` 在缺关键信息时会**直接报错退出**（除非显式加 `--allow-empty` / `--allow-empty-fields`）。这两个 allow 开关默认禁用，AI **不应主动使用**，必须先把子项/字段问清楚再调脚本。

## References 索引（按需加载）

`references/` 下文档预计总长 5000+ 行，**第一轮绝对不要全读**：

| 用户意图 | 必读文档 | 何时读 |
|---------|---------|------|
| 需求文档 / 整应用生成 | `whole-app-workflow.md` | 模式 D 一开始 |
| 创建新应用 | `directory-structure.md` + `references/appinfo/应用配置/index.md` | 模式 A 一开始 |
| 默认值 / 命名 / 校验 / 字段填充准则 | `conventions.md` | 按需查 |
| 涉及 appref | `references/appref/引用配置/index.md` | 用户声明要引用时 |
| codeitem 操作 | `references/codeitem/代码项/index.md` | 用户提到代码项/字典 |
| mis 操作 | `references/mis/数据模型/index.md` | 用户提到数据表/模型/字段 |
| module 操作 | `references/module/模块/index.md` | 用户提到模块/菜单 |
| event 操作 | `references/event/动作流/index.md` | 用户提到动作流/接口编排/动作流 DSL；需要生成复杂动作流（多节点、条件分支、迭代）时按需读子文档 |
| workflow 操作 | `references/workflow/工作流/index.md` | 用户提到工作流/审批流（**生成前后必走 5 条重点检查**） |
| workflow 深度（节点字段定义） | `references/workflow/工作流/基础骨架/` 子文档 | 需要查看具体节点字段定义时按需读 |
| workflow 字段类型约束 | `references/workflow/工作流/生成与校验/07-字段类型约束表.md` | **生成前必读**，防止数字/字符串类型错误（如 tableid 必须整数） |
| workflow 生成指南 | `references/workflow/工作流/生成与校验/06-脚本使用指南.md` | 使用 add_workflow.py 和 validate_yml.py 时 |
| pagedesigne 操作 | `references/pagedesigne/页面设计器/index.md` | 用户提到页面/页面设计器/Schema/pagedesign（默认 device=desktop） |
| pagedesigne 深度（复杂页面） | `references/pagedesigne/页面设计器/设计器 Schema 规范定义/` 子文档 | 需要生成复杂 schema（多 model、多 resource、嵌套视图树）时，按需读对应子文档和示例 |
| pagedesigne 示例参考 | `references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/sform/demo.md`（PC）<br>`references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/smallscreen/demo.md`（移动端） | 生成页面前先参考对应设备的示例结构 |

每次最多读 1-2 个相关文档；不确定该读哪个，先问用户。

## 工作流硬性要求（路由触发器）

**触发条件**：用户请求"生成 / 创建 / 设计 / 修改 工作流 / 审批流"。

**强制动作**：

1. 必须执行 `references/workflow/工作流/index.md` 顶部的「🔍 生成前重点检查清单」5 条（不要在这里复述）。
2. 优先用 `scripts/add_workflow.py` 一键生成；该脚本已默认产出满足前 4 条的骨架。
3. 落盘后必跑 `scripts/validate_yml.py`，错误数 = 0 才算交付。
4. 任意 1 条不达标就不交付：先修复或回到对话脚本补全信息。
5. 先识别工作流能力：普通流程、自定义流程（`isnewversion=10` + 流程设计按钮）、自由流程（`isnewversion=20` + 禁止退回）、主子流程（`activitytype=90`）、路由节点（`activitytype=40`）。
6. 外部方法（`method.ruleguid`）/事件配置（`workflowEvent.ruleGuid`）/流转条件（`workflowTransitionCondition.ruleGuid`）可配置动作流标识；若引用尚未落盘的 event，计划里必须预分配并在 event 阶段生成对应动作流。
7. **字段类型务必核对** `references/workflow/工作流/生成与校验/07-字段类型约束表.md`：`tableid` 必须整数、`iconx/icony/direction/tag` 必须字符串等。

## 通用执行流程

| 步骤 | 关键动作 |
|------|---------|
| 1 | 信息收集：按对应 references 自然语言澄清，先形成计划文档再等明确批准 |
| 2 | 路径解析：`python scripts/path_resolver.py --apptag <tag>` |
| 3 | 脚本生成 / 模板复制：优先调用对应 `scripts/add_*.py` |
| 4 | 字段填充：按 references 字段说明逐项写入；保留 `type:` 第一行 |
| 5 | 静态校验：`python scripts/validate_yml.py <文件或目录>` |
| 6 | 结果汇报：列出生成/修改的文件清单 + 关键字段 + 后续建议 |

## 质量门禁

- **单文件**：`python scripts/validate_yml.py <文件>`
- **修改已有应用**：`python scripts/inventory_metadata.py --metadata <metadata>` + 相关文件校验
- **整应用生成**：`python scripts/validate_yml.py --strict --check-refs <metadata>`
- **页面设计器**：校验 `events/source/model/textModel/actions.steps` 引用闭合
- **appref/mis 引用**：用 `--check-refs` 检查 `appref` 和 `datasourceCodename`

校验失败先修复再汇报；无法修复时列阻断项，**不要说"已完成"**。

## 内置脚本一览

| 脚本 | 用途 |
|------|------|
| `scripts/scaffold_app.py` | 新建应用骨架（建目录 + appinfo + 可选 appref） |
| `scripts/path_resolver.py` | 给定 apptag 算 metadata 绝对路径 |
| `scripts/add_codeitem.py` | 在指定 metadata 目录追加一个代码项 |
| `scripts/add_mis_field.py` | 新建 mis 表或追加字段 |
| `scripts/add_module.py` | 新建模块/菜单 yml |
| `scripts/add_event.py` | 新建标准动作流 yml |
| `scripts/add_workflow.py` | 新建工作流（自动生成 5 类节点 + workflowConfig + workflowPvMisTableSet） |
| `scripts/add_pagedesigne.py` | 新建页面设计器 Core Schema yml（内容仍为 JSON 文本） |
| `scripts/inventory_metadata.py` | 列出现有 metadata 资产清单 |
| `scripts/validate_yml.py` | 静态校验某个文件或整个 metadata 目录 |
| `scripts/check_dsl.py` | 动作流 DSL 结构/节点/连线/资产校验 🆕 |

每个脚本都内置 `--help`，参数缺失会自报使用方法。**完整调用示例与参数 cheatsheet** 见 `references/directory-structure.md` 的「脚本调用 cheatsheet」节。

## 字段填充准则（避免幻觉）

详见 `references/conventions.md`。核心要点：

- `type:` 是 yml 第一行（appinfo/appref 除外）
- GUID 字段（如 module 的 guid、workflow 的 processGuid）：用脚本生成 UUIDv4，**不要让 LLM 编**
- 时间戳字段：`YYYY-MM-DD HH:MM:SS`，从当前日期取
- 枚举值：见对应 references 文档表格，**不能新造**
- 文件名规则：新建资产必须使用 `名字.类型.yml`；mis 表名/name/tableName 用小写英文数字且不能有下划线，字段名可以保留下划线；pagedesigne 文件后缀为 `.pagedesigne.yml`，内容仍为 Core Schema JSON 文本

## 输出报告

完成一次资产创建/修改后，给用户一段简短汇报：

```
✅ 已完成
- 工程：epoint-ipd-action
- 应用：xmlx (项目立项)
- 操作：新增 codeitem「审核状态」
- 文件：
  - <绝对路径>/metadata/codeitem/审核状态.codeitem.yml （新建）
- 校验：通过 (validate_yml.py 0 errors)
- 后续建议：可在对应 mis 字段的 datasourceCodename 上引用「审核状态」
```

不要长篇大论，**只报关键信息 + 后续动作建议**。

## 引用其他文档

- 各类目深度文档：`references/<asset>/<中文目录>/index.md`
- 整应用工作流：`references/whole-app-workflow.md`
- 通用约定 + 字段填充准则：`references/conventions.md`
- 目录结构 + 脚本 cheatsheet + 触发模式细节：`references/directory-structure.md`
- 模板：`assets/templates/<type>.yml`

## LLM 自检要点（避免幻觉与无限重试）

> 以下要点用来约束 LLM 自身行为，与上文"作业边界 / 整应用分阶段确认 / 资产完整性门禁"互补，不重复已说过的规则。

1. **错三次就停**：同一个脚本/命令连续失败 3 次立即停止，回报根因（参数错、依赖缺、约束冲突），不要无限调参。
2. **批准必须明确语义**：能列编号选项就列，不要给 yes/no；批准必须是用户**明确语义**（"批准创建 / 按计划生成 / 可以落盘"），模糊回复（"嗯"、"好像可以"）一律继续追问。
3. **路径用绝对路径**：调脚本前先 `path_resolver.py --apptag <tag>` 算好 metadata 绝对路径再传，不要让脚本去猜相对路径。
4. **JSON 入参全部用 `parse_json_arg`**：所有 `--xxx-json` 参数必须经 `_common.parse_json_arg(value, expected_type=list, label=...)`，不要直接 `json.loads(args.xxx)`，否则字符串会被当成 list 逐字符遍历（已踩过的坑）。
5. **Schema 引用先检查再生成**：pagedesigne 里 `model` / `source` / `events` / `actions.steps[].use` 都要回查到 `models` / `resources` / `actions` 的对应 id，引用闭环再落盘；落盘后必跑 `validate_yml.py --check-refs`。
6. **工作流字段命名用下划线**：transition / 按钮字段统一用下划线命名（如 `is_targettransactor_editable`、`is_showasoperationbutton`、`is_ShowOpinionTemplete`），不要用旧驼峰；详见 `references/workflow/工作流/基础骨架/03-流转关系.md` 与 `references/workflow/工作流/基础骨架/02-活动按钮.md`。`scripts/add_workflow.py` 已默认产出符合规范的字段名。
