# 工作流：workflow yml

## 1. 资产定位与边界

`workflow` 描述完整的**业务审批流程**：流程基础信息、活动（节点）、变迁（线）、活动按钮、退回配置、流程材料、表单数据表映射、流程版本等。

- 与 应用根目录的对应关系：`<apptag>/workflow/<流程名>.workflow.yml`
- 不在本资产范围内的事：
  - 表单字段定义属于 `mis`（workflow 通过 `sql_tablename` 引用，引擎自动绑定 mis 表 ID），详见 `references/mis/数据模型/index.md`
  - 流程触发的复杂动作/外部数据流转属于 `event`（动作流），详见 `references/event/动作流/index.md`
  - 状态机型工作流、加办/抄送、Java 外部方法实现属于"不在本 skill 范围内的事"，详见下文「[不在本-skill-范围内的事](#不在本-skill-范围内的事)」

## 2. 文档导航

> 本资产的内容由本 index.md 承载主干（顶层结构 / 红线 / 校验 / 关系），同级子目录承载详细字段定义与场景示例。
> 章节速查：
> - § 文件位置与命名：见下文「[文件位置与命名](#文件位置与命名)」
> - § 设计红线（节点拆分 / 名称 / 流转闭环 / GUID 一致性 / 退回闭环）：见下文「[⛔-设计红线（强校验，违反会导致流程发布失败或运行异常）](#-设计红线强校验违反会导致流程发布失败或运行异常)」
> - § 顶层结构 + 数据关系：见下文「[顶层结构](#顶层结构)」「[数据关系（必遵守）](#数据关系必遵守)」
> - § 占位符 `[#=xxx#]`：见下文「[`[#=xxx#]` 占位符](#xxx-占位符)」
> - § 校验规则与修复指引：见下文「[校验规则与修复指引（validate_yml.py 实际执行）](#校验规则与修复指引validate_ymlpy-实际执行)」
> - § 子目录详细文档：见下文「[子目录导航表](#子目录导航表)」与开篇的「[文档导航](#文档导航)」表格（基础骨架 / 生成与校验 / 场景示例）

## 3. 生成与修改对话速查

> 详细对话脚本与脚本调用：见下文「[修改已有工作流](#修改已有工作流)」「[快速生成脚本](#快速生成脚本)」与子目录 `生成与校验/06-脚本使用指南.md`。生成前**必读**「[🔍 生成前重点检查清单（每次生成工作流都必须自检）](#-生成前重点检查清单每次生成工作流都必须自检)」5 条与「[⛔ 设计红线](#-设计红线强校验违反会导致流程发布失败或运行异常)」。

### 3.0 工作流意图判定门禁

处理 workflow 前必须先判定本次是 `create`、`revise-plan` 还是 `update-existing`：

| 模式 | 判定条件 | 脚本 | GUID 规则 |
|---|---|---|---|
| `create` | 用户明确说新建/新增/创建/另起一个工作流，或仓库无法命中已有流程 | `add_workflow.py` | 允许生成新 `processguid/processversionguid/version` |
| `revise-plan` | 还在计划/流程图确认阶段，用户指出节点或分支错误 | 不落应用资产，只更新计划/预览图 | 不涉及已落盘 GUID |
| `update-existing` | 命中已有 `.workflow.yml`、同名流程、`processguid`，或用户说修改原流程 | `update_workflow.py` | 必须保留 `processguid/processversionguid/version` |

歧义兜底：若同名 workflow 已存在，而用户只说“生成/改一下/优化一下”，必须先问“新增独立流程”还是“修改原流程”，推荐“修改原流程”。

规划阶段必须输出 Mermaid 简易流程图供用户确认；只展示业务节点和条件分支，不展示引擎节点“开始/结束/浏览”。用户纠偏后更新同一份计划和同一张预览图，不重新抽取基础版流程，也不得静默改成新建 workflow。

### 3.1 spec v2 主动追问触发词（重要）

用户需求中**只要出现下面任何一个关键词**，AI 必须在计划阶段先与用户确认细节，然后用对应入参重新生成 workflow，**不允许默认骨架就交付**：

| 触发词 | 对应入参 | 落到哪个字段 |
|--------|---------|-------------|
| 字段权限 / 只读字段 / 字段隐藏 / 字段必填 | `--activity-materials-json` | `workflowActivityMaterial` + `workflowActivityFieldAccess` |
| 通过率 / 多人会签 X% / 60% 通过 / 投票通过 | `--approve-pass-rate-json` | `passrate` / `passratecalculatemode` / `nopasshandlevalue` |
| 超时提醒 / 短信通知 / 多人锁定 N 分钟 / 移动端小程序规则 / 多路汇合 / 自定义会合 | `--activity-extra-json` | `overtimeremindcontent` / `smscontent` / `locktimewhenmultitransactor` / `mobileappletrules` / `addattachfilesource` / `joinmethodguid` |
| 金额 > X 走A 否则 走B / 条件分支 / 流转条件 / 不满足条件就走B | `--conditions-json` + `--contexts-json` | `workflowTransitionCondition` + `workflowContext`；“否则/不满足”必须生成显式互补条件 |
| 操作前后联动 / 节点完成后更新表 / 流程钩子 / 触发动作流 | `--methods-json` + `--events-json` | `method` + `workflowEvent`（可关联动作流 `ruleguid`） |
| 主子流程 / 调用子流程 | `--process-mode subprocess --subprocess-guid <子流程 processguid>` | `activitytype=90` 子流程节点 |
| 自定义流程 / 流程设计按钮 / 用户自定义流转 | `--process-mode custom` | `isnewversion=10` + `operationtype=80` 设计按钮 |
| 自由流程 / 自由流转 / 多角色任意流转 | `--process-mode free` | `isnewversion=20` + 禁退回 |

## 4. 与其他资产的引用关系

- 引用其他资产：
  - `workflowPvMisTableSet.sql_tablename` 必须匹配同应用 `mis.tableName`（表单数据落地表）
- 被其他资产引用：
  - `event`（动作流）的"工作流触发"模式可通过流程 `processguid` 触发流程
  - `workflowEvent` / `method` / `workflowTransitionCondition` 可通过 `ruleguid` 绑定到 event 的 `app.id` / `rowguid` / `sign`
  - 跨应用引用只有在用户明确要求暴露工作流资产时，才通过 `appref` 的 `engineguid: workflow` 配置
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs <app-root>` 会校验 `sql_tablename` → `mis.tableName` 和 `ruleguid` → event 引用闭合

---

`workflow` 描述完整的**业务审批流程**：流程基础信息、活动（节点）、变迁（线）、活动按钮、退回配置、流程材料、表单数据表映射、流程版本等。

## 文档导航

| 子文档 | 何时读 |
|---------|--------|
| **基础骨架/** | 查看具体节点字段定义时按需读 |
| ├─ `01-流程节点.md` | 5 类节点完整定义 + workflowProcess |
| ├─ `02-活动按钮.md` | 按钮字段、退回配置、工作流扩展字段 |
| ├─ `03-流转关系.md` | transition 完整定义 + 流转条件（workflowTransitionCondition） |
| ├─ `04-表单材料与数据表.md` | workflowPvMaterial + workflowPvMisTableSet + 相关数据（workflowContext） |
| ├─ `05-流程版本.md` | workflowProcessVersion + 工作流扩展字段 |
| └─ `06-外部方法与事件.md` | method + workflowEvent |
| **生成与校验/** | 生成和校验工作流前读 |
| ├─ `01~05-*.md` | AI 生成流程指南 |
| ├─ `06-脚本使用指南.md` | add_workflow.py + validate_yml.py 用法 |
| └─ `07-字段类型约束表.md` | **生成前必读**，数字/字符串类型核对 |
| **场景示例/** | 生成前参考对应复杂度的示例 |
| ├─ `01-简单审批流.md` | 最小骨架 3 节点示例 |
| ├─ `02-主子流程.md` | 主流程调用子流程节点 |
| ├─ `03-自定义流程.md` | 自定义流程设计按钮 |
| ├─ `04-自由流程.md` | 自由流转与退回禁用 |
| └─ `05-条件分支与外部方法.md` | 相关数据、流转条件、外部方法与动作流 ruleguid |
---

## 🔍 生成前重点检查清单（每次生成工作流都必须自检）

**任何工作流 yml 生成前后，必须按照以下 5 条逐项自检。任何 1 条不达标就不能交付，必须先修复或回到对话脚本补全信息。**

### 1. yaml 文件结构正确及完整性

识别**必要结构元素是否齐全**，缺一不可：

- 顶层：`type: workflow` + `workFlow:`
- `workFlow.workflowProcess`：流程基础信息（含 `processguid / processname`）
- `workFlow.workflowVersion`：版本结构，下含：
  - `activity`：活动数组
  - `transition`：变迁数组
  - `workflowConfig`：退回配置数组（无退回按钮时可为空数组）
  - `workflowPvMaterial`：流程版本材料（**至少 1 条**）
  - `workflowPvMisTableSet`：表单数据表映射（与材料 1:1）
  - `workflowProcessVersion`：流程版本详情

### 2. 各节点结构完整性（必填项不能缺）

每个 `activity` 节点都必填：

- `activityguid`、`activityname`、`activitydispname`、`processversionguid`
- `activitytype`（10/20/30/40/90/100 等）、`vmlid`
- `iconx`、`icony`（字符串，不是数字；横向布局默认开始 `(0,204)`、申请 `(235,180)`、浏览 `(24,-34)`）

**按 activitytype 分别校验必填项**：

| 类型 | 必填项 | 必空字段（写 `null`） |
|------|--------|------|
| 开始（10） | 上述通用项；`splittype=30` | `multitransactormode / handleurl / mobilehandleurl / isallowaddattachfile / timelimitenable / earlywarning_enable / is_passwhennotransactor / jointype` |
| 申请（30, name="申请"） | 上述通用项；`splittype=20 / jointype=30`；`handleurl='home/vuepagedesigner/renderer/add?pagetag=<page_tag_form>'`；`multitransactormode=10` | — |
| 审批（30, 自定义 name） | 同申请；含 `workflowActivityOperation`（至少 1 个通过按钮） | — |
| 结束（20） | 通用项；`jointype=30` | 同开始节点 + `splittype` |
| 浏览（100） | 通用项；`handleurl='home/vuepagedesigner/renderer/detail?pagetag=<page_tag_detail>'`；`mobilehandletype=view` | `multitransactormode / isallowaddattachfile / timelimitenable / earlywarning_enable / is_passwhennotransactor / jointype` |

坐标按动态横向布局生成：开始节点 `iconx='0' / icony='204'`；申请节点固定 `iconx='235' / icony='180'`；后续流程节点按上一节点卡片估算宽度递增，最小横向间距不低于 `320px`，主线 `icony='180'`；结束节点在最后一个流程节点后方，`icony='204'`；浏览节点固定 `iconx='24' / icony='-34'`，位于流程上方且不参与流转。条件可选分支按 `A → B → C` 且存在 `A → C` 识别，`B` 是分支节点，放在分支泳道 `icony='20'`，主线与汇合节点仍保持 `icony='180'`。

每个 `transition` 必填：`transitionguid / processversionguid / fromactivityguid / toactivityguid / transitionname / vmlid (≥2)`。

每个退回按钮必填：`operationtype=30 / targetactivity='[#=AllBeforeActivity#]' / backtargetscope='1' / multitransctormode='OR'`。

### 3. 各节点间的关联关系正确性

**父子层级与属性引用闭合**：

- **processversionguid 一致性**：`workflowProcessVersion.processversionguid` 必须与所有 activity / transition / workflowConfig / workflowPvMaterial / workflowPvMisTableSet 的 `processversionguid` 完全相等
- **processguid 一致性**：`workflowProcessVersion.processguid` == `workflowProcess.processguid`
- **transition 引用闭合**：`fromactivityguid` 与 `toactivityguid` 必须能在 `activity` 数组中找到对应 `activityguid`
- **退回按钮 ↔ workflowConfig 闭环**：每个 `operationtype=30` 的按钮必须有 1 条 `workflowConfig`，且 `sourceguid` 等于该按钮的 `operationguid`
- **材料 ↔ 表映射 1:1**：`workflowPvMaterial.materialguid` 必须在 `workflowPvMisTableSet.materialguid` 中找到
- **operation ↔ activity 反向归属**：每个 `workflowActivityOperation.activityguid` 必须等于其所属 activity 的 `activityguid`
- **vmlid 唯一**：所有 activity 的 vmlid 不能重复（开始固定 `-1`、结束固定 `1`、浏览固定 `-2`、申请固定 `2`、审批 ≥3 递增）；transition 的 vmlid 同样唯一

### 4. 设计红线、节点拆分关联强规则

**这一条是流程引擎能否正确加载的硬门禁，违反必然失败**：

- ⛔ **节点拆分红线**：开始活动（`activitytype=10`，纯启动）与申请活动（`activitytype=30`，`activityname=申请`）**必须分拆为两个独立的 activity**，禁止合并。开始节点**不能**绑定 `handleurl`、不能填表单。
- ⛔ **节点完整性红线**：5 类节点必须齐全 —— 开始(10) + 申请(30) + 审批(30, N 个) + 结束(20) + 浏览(100, 孤立)。漏任何一类都不行。
- ⛔ **节点名称红线**：开始活动 `activityname` 必须是 `开始`、结束活动 `activityname` 必须是 `结束`、申请活动 `activityname` 必须是 `申请`。
- ⛔ **空值红线**：开始 / 结束 / 浏览节点的 `handleurl`（浏览除外）/ `multitransactormode` / `timelimitenable` / `earlywarning_enable` / `isallowaddattachfile` / `is_passwhennotransactor` 必须为 `null`。
- ⛔ **流转顺序红线（重点）**：transition 必须形成 **开始 → 申请 → 审批₁ → ... → 审批ₙ → 结束** 的链路，**不能跳过申请节点**（如开始直接接审批）。浏览节点不参与流转（孤立）。
- ⛔ **退回闭环红线**：每个退回按钮必须配 1 条 `workflowConfig`（`belongto=22, configname=backTargetScope, sourceguid=按钮 operationguid`）。

### 5. 必须通过引擎运行校验

每次生成、修改工作流 yml 后，**必须**执行：

```bash
python3 scripts/validate_yml.py <app-root>/workflow/<流程名>.workflow.yml
```

**通过条件：错误数 = 0**。出现任何 error 必须修复后重新校验，警告（warn）也建议处理。如果作为整应用一部分生成，还需要跑 `python3 scripts/validate_yml.py --strict --check-refs <app-root>` 确认跨引用关系闭合，并把 spec v2 已废弃字段（驼峰键 / `tableid` / `fromMisTableId` / `fromFieldId`）一律升级为 error。

> ⛔ **路径红线（spec v2）**：`<app-root>` 必须是 `<...>/META-INF/resources/<...>/<apptag>/`，资产直接挂在 `<apptag>/` 下；**严禁**出现 `<apptag>/metadata/<asset>/...` 这种老结构。脚本会在落盘前对 `--app-root` 做 fail-fast 校验，路径里只要包含 `/metadata/` 段就直接拒绝。

### 6. 禁止手写 workflowVersion 子节点

必须用 `add_workflow.py` 生成 workflow 骨架。手写 `workflowVersion` 容易导致结构错误、字段名幻觉和必填项缺失；LLM 只整理业务差异为脚本 JSON 入参。

---

## 文件位置与命名

```
<apptag>/workflow/<流程名>.workflow.yml
```

推荐中文命名（如 `采购立项审核流程.workflow.yml`、`费用报销审核流程.workflow.yml`）。

## handleurl pagetag 取值规则

需要填 handleurl 的活动类型：**activitytype ∈ {30, 100}**——普通人工活动（30）使用 `add` 模式，浏览活动（100）使用 `detail` 模式。开始（10）/ 结束（20）/ 路由（40）/ 子流程（90）等其他类型不填。

`handleurl` 与 `mobilehandleurl` 默认形如：

```
home/vuepagedesigner/renderer/<add|detail>?pagetag=<page_tag>
```

`<page_tag>` 取自同应用 `<apptag>/page/<...>.json` 顶层 `pagetag` 字段。

### 多页面时的对应关系

| 节点类型 | 默认对应的 pagetag |
|---------|------------------|
| 申请（30, name="申请"） | `home/vuepagedesigner/renderer/add?pagetag=<表单页pagetag>` |
| 审批（30, 自定义 name） | 同上（共用表单页） |
| 浏览（100） | `home/vuepagedesigner/renderer/detail?pagetag=<详情页pagetag>`，无单独详情页时回落到表单页 pagetag |

### 取值流程（自然语言对话）

skill 在生成工作流前按以下顺序确定 pagetag：

1. 扫同应用 `<apptag>/page/` 目录，统计 `*.json` 数量。
2. **仅 1 份**：自动取该页面的 pagetag（form 与 detail 都用它）。
3. **多份**：以编号列表向用户问"哪个页面用作申请/审批节点（表单页）、哪个用作浏览节点（详情页）"。
4. 脚本对应参数：`add_workflow.py --pagetag-form <表单页 pagetag> --pagetag-detail <详情页 pagetag>`，未传时按上述自动推断。

> 自定义 handleurl（不以 `home/vuepagedesigner/renderer/` 开头）时 `validate_yml.py` 会输出 warn 提示，但不阻断。

`workflowPvMaterial` 的 PC 页面地址也使用同一 pagetag 来源：`pageurl_read` 使用 `home/vuepagedesigner/renderer/detail?pagetag=<page_tag_detail>`，`pageurl_readandwrite` 使用 `home/vuepagedesigner/renderer/add?pagetag=<page_tag_form>`；`mobilepageurl_read` / `mobilepageurl_readandwrite` 暂不自动填充，默认空字符串。

## ⛔ 设计红线（强校验，违反会导致流程发布失败或运行异常）

1. **节点拆分红线**：开始活动（`activitytype=10`，纯启动，不能填表单）与申请活动（`activitytype=30`，填报提交）**必须分拆为两个独立的 activity**，禁止合并。
2. **节点完整性**：流程必须固定包含 **5 类节点**：
   - 1 个开始活动（`activitytype=10`）
   - 1 个申请活动（`activitytype=30`，`activityname=申请`）
   - N 个审批活动（`activitytype=30`，`activityname` 自定义）
   - 1 个结束活动（`activitytype=20`）
   - 1 个浏览活动（`activitytype=100`，孤立节点，置于流程上方）
3. **节点角色唯一**：一个 activity 只能是单一类型，不能同时具备"开始 + 申请"能力。
4. **节点名称固定**：开始活动名称固定为 `开始`、结束活动名称固定为 `结束`，不要改名。
5. **空值规则**：开始/结束/浏览节点的以下字段必须为空（`null`）：
   - `handleurl`、`mobilehandleurl`（浏览节点除外，浏览节点允许填）
   - `multitransactormode`、`earlywarning_enable`
   - `isallowaddattachfile`、`timelimitenable`、`is_passwhennotransactor`
6. **流转闭环**：transition 必须为 `开始(10) → 申请(30) → ... → 结束(20)`，不能跳过申请节点直接连接审批节点。
7. **GUID 一致性**：所有子节点的 `processversionguid` 必须**完全一致**；`workflowProcessVersion.processguid` 与 `workflowProcess.processguid` 必须相等。
8. **退回闭环**：每个退回按钮（`operationtype=30`）必须在 `workflowConfig` 中有 1 条对应配置（`belongto=22, configname=backTargetScope, sourceguid=该按钮 operationguid`）。

## 顶层结构

```yaml
type: workflow                       # 全局固定标识

workFlow:                            # 流程根（注意 w 小写）
  workflowProcess:                   # 流程基本信息
    ...
  workflowVersion:                   # 流程版本结构
    activity:                        # 活动数组（直接平铺，无 WorkflowActivity 包装层）
      - activityguid: ...
        activityname: ...
        ...
        workflowActivityOperation:   # 该节点的按钮（数组，子结构）
          - operationguid: ...
            ...
    workflowConfig:                  # 退回按钮关联配置
      - rowguid: ...
        ...
    workflowPvMaterial:              # 流程版本材料（表单）
      - materialguid: ...
        ...
    workflowPvMisTableSet:           # 表单与数据库表映射
      - mistablesetguid: ...
        ...
    transition:                      # 节点流转关系
      - transitionguid: ...
        ...
    workflowProcessVersion:          # 流程版本详情
      ...
```

> ⚠️ **常见错误**：旧版本写法 `WorkFlow / WorkflowProcess / WorkFlowVersion / Activity / WorkflowActivity / Transition` 都不被引擎识别，必须按上面的小写命名。

> 🔎 各节点的详细字段定义请查看 `references/workflow/工作流/基础骨架/` 子文档（含外部方法与事件 `06-外部方法与事件.md`、流转条件见 `03-流转关系.md` 末尾、相关数据见 `04-表单材料与数据表.md` 末尾）。

## 数据关系（必遵守）

### 一对一
- `workflowProcess` ↔ `workflowProcessVersion`：1 个流程对应 1 个启用版本
- `workflowPvMaterial` ↔ `workflowPvMisTableSet`：1 个表单对应 1 个数据表映射
- `workflowActivity` ↔ `workflowActivityMaterial`：1 个活动对应 1 个表单权限

### 一对多
- `workflowProcessVersion` → `activity`：1 个版本对应 5+ 个活动（开始 + 申请 + N 审批 + 结束 + 浏览）
- 每个普通节点 → `workflowActivityOperation`：1-2 个按钮
- `workflowProcessVersion` → `transition`：1 个版本对应 N 条流转（活动数 -2，浏览节点不参与）
- 1 个退回按钮 → `workflowConfig`：1 条配置
- `workflowProcessVersion` → `method`：1 个版本对应 N 个外部方法（≥0）
- `workflowProcessVersion` → `workflowEvent`：1 个版本对应 N 个事件（≥0）
- `workflowProcessVersion` → `workflowContext`：1 个版本对应 N 个相关数据（≥0）
- `workflowProcessVersion` → `workflowPvMaterial`：1 个版本对应 N 个材料（≥1）
- `workflowActivityMaterial` → `workflowActivityFieldAccess`：1 个材料对应 ≥0 条字段权限

### 唯一标识关联
- 版本内所有子节点 `processversionguid` **必须完全一致**
- 流转 `fromactivityguid / toactivityguid` 必须匹配活动的 `activityguid`
- 按钮关联配置 `sourceguid` 必须匹配退回按钮的 `operationguid`
- 事件 `eventmethodguid` 必须匹配外部方法的 `methodguid`
- 流转条件 `transitionguid` 必须匹配所属 transition 的 `transitionguid`
- 同一源节点出现多条条件分支时，每条 outgoing transition 都必须有显式 `workflowTransitionCondition`；“否则/不满足条件”生成互补条件（如 `!=`、`<=`），不要只设 `is_default=10`
- 相关数据 `frommaterialguid` 必须匹配 `workflowPvMaterial.materialguid`

## `[#=xxx#]` 占位符

工作流系统的特殊语法，用于运行时取值：

| 占位符 | 含义 |
|--------|------|
| `[#=FirstMaterialUrl#]` | 第一个材料的 URL |
| `[#=申请人#]` | 流程发起人姓名 |
| `[#=PreviousStepActivity#]` | 上一步活动 |
| `[#=AllBeforeActivity#]` | 所有已流转活动（退回按钮的 targetactivity 通常用这个） |
| `[#=ExecutionContext#]` | 执行上下文 |

## 修改已有工作流

修改已有 workflow 是原地修正，不做版本迭代。除非用户明确要求“另建新流程/生成新版本”，否则：

- 必须保留 `workflowProcess.processguid`
- 必须保留 `workflowProcessVersion.processversionguid`
- 必须保留 `workflowProcessVersion.version`
- 未变化的 activity、operation、transition、material、config GUID 尽量保留
- 只有新增节点、按钮、连线、条件才生成新 GUID；删除项直接移除

推荐脚本（默认直接传目标节点数组，不依赖 IR）：

```bash
python3 scripts/update_workflow.py \
  --workflow-file <app-root>/workflow/<流程名>.workflow.yml \
  --activities-json '[{"name":"申请","type":"apply"},{"name":"科室负责人审批","type":"approve"}]' \
  --dry-run
```

`--from-ir .lowcode-plans/<apptag>/ir.yml --asset-id <asset-id>` 仅用于兼容旧计划或审计流程。

确认后去掉 `--dry-run` 写回，并执行：

```bash
python3 scripts/validate_yml.py <app-root>/workflow/<流程名>.workflow.yml
```

| 场景 | 操作 |
|------|------|
| 改流程名 | 改 `workflowProcess.processname` 和 `workflowProcessVersion.processversionname` |
| 加审批节点 | 在 `activity` 数组追加（vmlid 递增）+ 调整 `transition`（注意 vmlid 不重复）+ 加退回按钮则同时新增 `workflowConfig` |
| 删审批节点 | 从 `activity` 移除 + 删对应 `transition` + 删该节点退回按钮的 `workflowConfig` |
| 改节点处理人 | 改 `multitransactormode` + 配合 `targetactivitytransactorsource` |
| 改按钮 | 改对应 `workflowActivityOperation`；若变更退回按钮 GUID，记得同步 `workflowConfig.sourceguid` |
| 改流程方向 | 改 `workflowProcessVersion.direction`（`'0'`水平 / `'90'`垂直） |

## 校验规则与修复指引（validate_yml.py 实际执行）

| 校验项 | 等级 | 修复方式 |
|--------|------|---------|
| `type: workflow` | error | 顶部第一行加 `type: workflow` |
| 顶层用 `WorkFlow:`（驼峰） | warn（强制改） | 改为 `workFlow:`（小写 w） |
| activity 数组项带 `WorkflowActivity:` 包装 | warn（强制改） | 平铺：`- activityguid: ...` 直接当数组项字段 |
| 必含开始(10) + 申请(30, name="申请") + 审批(30) + 结束(20) + 浏览(100) | error | 漏哪个补哪个；浏览节点 vmlid=-2 孤立 |
| 开始节点名称必须是"开始"、结束节点必须是"结束" | error | 改 `activityname` |
| 开始节点直接当申请节点用（绑 handleurl/表单） | error | 拆成 2 个独立 activity |
| 开始/结束节点的 handleurl/multitransactormode/isallowaddattachfile/... 不为空 | error | 这些字段写 `null` |
| 浏览节点的 multitransactormode/isallowaddattachfile 不为空 | warn | 写 `null` |
| 不同节点的 `processversionguid` 不一致 | error | 统一为同一个 UUID |
| `workflowProcessVersion.processguid` ≠ `workflowProcess.processguid` | error | 改成相同值 |
| 退回按钮(operationtype=30) 没对应 `workflowConfig` | error | 每个退回按钮配 1 条 `workflowConfig`（`belongto=22, configname=backTargetScope, sourceguid=按钮 operationguid`） |
| 退回按钮 `multitransctormode` 不在 `OR/AND/OrAndRead` 集合 | error | 改为合法枚举值 |
| transition 用旧驼峰 `isTargetTransactorEditable` / `isShowAsOperationButton` | warn（强制改） | 改下划线 `is_targettransactor_editable` / `is_showasoperationbutton` |
| activity 的 vmlid 重复 | error | 开始 -1、结束 1、浏览 -2、申请 2、审批 ≥3 递增 |
| transition 的 from/to activityguid 找不到对应 activity | error | 检查 GUID 拼写或活动是否漏建 |
| 没有"开始 → 申请"的 transition | error | 补一条 `fromactivityguid=开始, toactivityguid=申请` 的变迁 |
| transition.vmlid 重复 / `<2` | error/warn | 从 2 开始递增不重复 |
| `workflowPvMaterial` 与 `workflowPvMisTableSet` 数量不匹配 | warn | 1:1 关系，1 个材料配 1 条数据表映射 |
| `tableid` 字段存在 | warn | spec v2 已废弃，删除该字段；引擎根据 `sql_tablename` 自动绑定 mis 表 ID |
| `multitransactormode` / `isallowaddattachfile` 写成字符串 `"10"` | warn | 改为整数 10 |
| `iconx/icony/direction/tag` 写成数字 | warn | 用字符串 `'50'` / `'90'` / `'20'` |

## 不在本 skill 范围内的事

- **状态机型工作流**（含 `statemachinetag`、`statusid` 等）：复杂，建议线上设计器画
- **加办/抄送/送阅读**等高级流程操作：手写难度大，建议线上调整
- **流程脚本/外部方法 Java 实现**：属于高码资产，参考 `epoint-framework-dev`
- **复杂条件分支**（金额、角色等条件）：明确出现条件分支时，把业务差异整理成 `--conditions-json` + `--contexts-json` 调用 `scripts/add_workflow.py` 生成，不从空白手写扩展节点；`--conditions-json` 可用 `fromActivity` / `toActivity` 指定源和目标，缺少对应 transition 时脚本会自动补线；“否则/不满足条件”必须写互补条件，不使用默认变迁代替；复杂条件建议线上设计器复核

## 快速生成脚本

```bash
# 最小骨架（开始 + 申请 + 1 个审批 + 结束 + 浏览）
python3 scripts/add_workflow.py --app-root <app-root> --name "<流程名>" --material "<表单名>"

# 多审批节点 + 关联表单数据表（完整入参）
python3 scripts/add_workflow.py \
  --app-root <app-root> \
  --name "费用报销审核流程" \
  --approvers "部门审核,主管审核,财务审核" \
  --material "费用报销申请单" \
  --sql-tablename formtable20260112164507245
```

完整参数见 `python3 scripts/add_workflow.py --help` 或 `references/workflow/工作流/生成与校验/06-脚本使用指南.md`。生成后必须执行：

```bash
python3 scripts/validate_yml.py <app-root>/workflow/<流程名>.workflow.yml
# 整应用 + spec v2 严格校验（已废弃字段 / metadata 残留 / 引用闭环 → error）
python3 scripts/validate_yml.py --strict --check-refs <app-root>
```

错误数 = 0 才算交付。

## 反面模式（不要生成）

| 错误写法 | 正确写法 | 说明 |
|---------|---------|------|
| `workflowVersion:` 下直接写数组 | `workflowVersion:` 下写对象 | 默认只有 1 个启用版本 |
| `workflowPvMisTableSet.rowguid` | `workflowPvMisTableSet.mistablesetguid` | 不要和 `workflowConfig.rowguid` 混淆 |
| `workflowProcessVersion.versionnum` | `workflowProcessVersion.version` | 默认值通常为 `V1` |
| `workflowPvMisTableSet.formid` | 不生成该字段 | 表单和数据表通过 `materialguid` + `sql_tablename` 关联 |

---

## 子目录导航表

以下子目录按**职责维度**组织工作流的详细文档：

| 子目录 | 用途（职责维度） | 入口文档 |
|--------|-----------------|----------|
| `基础骨架/` | 工作流核心字段定义（流程节点/活动按钮/流转关系/表单材料与数据表/流程版本/外部方法与事件） | 各编号文档（01~06） |
| `生成与校验/` | 工作流生成脚本使用指南与校验规则 | 01-生成脚本使用指南.md |
| `场景示例/` | 工作流场景示例 | 01-简单审批流.md |
