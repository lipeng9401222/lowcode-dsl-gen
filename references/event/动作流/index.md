# 动作流：event yml

欢迎使用动作流 DSL 文档！本文档详细说明基于"流式处理"工作流的动作流 DSL (YAML) 文件完整结构和使用方法。

## 1. 资产定位与边界

- **本资产解决**：`event` 用于描述**接口业务编排**——把"接收 Webhook 请求 → 初始化上下文 → 接口鉴权 → 业务执行 → 构建结果集 → 返回响应"等步骤拼成一个流程图（DAG）。每个 event yml 对应**一个 REST 接口**的完整业务编排。
- **与应用目录的对应关系**：`<apptag>/event/<动作流标识>.event.yml`（历史 `<标识>.yml` 仅兼容读取）

### ✅ 何时需要动作流 / ❌ 何时不要动作流

> **重要边界（避免主动建议生成无意义的 event）**：
>
> 动作流是"编排型"业务逻辑的载体。**纯粹的标准 CRUD（列表、详情、新增、修改、删除）一律不要走 event**——这些场景由 MIS 接口或 REST 接口直接提供，前端直连业务 controller 即可。

#### ❌ 不要生成动作流的场景

| 场景 | 为什么不需要 | 应该用什么 |
|------|------------|----------|
| 列表查询（`getDataGridModel` / `list` / `query` / `find` / `fetch` / `search`） | 标准列表接口由 MIS 表 + REST 自动提供 | MIS 接口 / `XxxRestService` 标准方法 |
| 详情查询（`getDetail` / `getById`） | 单表详情属于标准读 | 同上 |
| 新增 / 修改（`saveOrUpdate` / `create` / `update`） | 单表写入由 MIS 接口提供 | 同上 |
| 删除（`delete` / `remove`） | 单表删除属于标准写 | 同上 |
| 简单字段映射、单表读写无副作用 | 走 event 反而多一层冗余 | MIS 接口 / REST 直连 |

#### ✅ 主动建议生成动作流的场景（当前阶段唯一一类）

| 场景 | 业务特征 | 典型方法名 |
|------|---------|----------|
| **状态变更联动** | 同时改状态位 + 写日志 + 发消息中心 + 触发后续业务 | `dispatch` / `approve` / `reject` / `archive` / `cancel` / `submit` / `revoke` |

> **当前阶段的边界**：skill 默认**只把"状态变更联动"作为主动建议生成 event 的场景**。其他类型的编排（见下方"高级场景"）不要主动提出，必须等用户明确说出诉求后再考虑。

#### 🟡 高级场景（用户明确要求才考虑，不主动建议）

以下场景平台层面是支持的，但 skill **不要主动建议**生成 event；只有在用户明确表达诉求（如"用动作流推一下""定时同步""工作流回调挂动作流"）后才进入 event 阶段，并提示用户这是高级用法：

| 场景 | 触发关键词 |
|------|----------|
| 跨系统推送/拉取（调外部接口、发 webhook） | 用户主动说"推送给 / 拉取自 / 同步到 外部" |
| 定时同步（Cron、批量处理） | 用户主动说"定时 / 每天几点 / 周期性" |
| 工作流回调（`method.ruleguid` / `workflowEvent.ruleGuid` / `workflowTransitionCondition.ruleGuid`） | 用户主动说"工作流里挂动作流 / 流转条件用动作流" |
| 多节点编排（条件分支、迭代、代码节点） | 用户主动说"接口里要分支 / 循环 / 写脚本" |

#### 命名暗示规则

skill 收到接口需求时按命名前缀给出默认建议：

- 方法名匹配 `^(get|list|query|find|fetch|search|save|create|update|delete|remove)` → **默认走标准接口**，不要主动建议生成 event。
- 方法名匹配 `^(dispatch|approve|reject|archive|cancel|submit|revoke)` 或显式带"状态变更联动"语义 → **才主动建议生成 event**。
- 其他匹配 `^(sync|push|pull|notify|callback|on[A-Z])` 等模式 → 属于"高级场景"，**不主动建议**；用户明确要求时再考虑。

> 边界冲突时（如用户明确要求"列表也走动作流"），按用户明确意图执行，但要在生成计划里标注"非常规用法"并解释成本。

### 不在本 skill 范围内的事

- **从零手写**复杂分支动作流（含条件、循环、迭代）：建议在线上动作流设计器画好，导出 yml
- **业务方法 Java 实现**（`XxxRestService.xxxMethod`）：属于高码资产，参考 `epoint-framework-dev` skill
- **Java Context 类定义**（如 `PurchaseProjectContext`）：属于高码
- **高级动作流编辑**（如新增分支节点）：需要时让用户在线上设计器画好导出

### 文件位置与命名

```
<apptag>/event/<功能名/接口名>.event.yml
```

推荐命名：
- 接口标识形式：`purchaseproject_getDataGridModel.event.yml`（与 controller 接口方法名对应）
- 业务功能形式：`获取采购立项列表.event.yml`

---

## 📖 什么是动作流

动作流（ActionFlow）是一个基于 DSL（领域特定语言）的流程编排引擎，支持通过可视化拖拽或 YAML 配置的方式构建业务自动化流程。

### 工具（业务动作）概念

**工具（Tool）** 是动作流的扩展机制，代表一个可执行的**业务动作**。

#### 为什么需要工具？

- 🔌 **扩展能力**：将任何业务逻辑封装为工具，无需修改核心引擎
- 🧩 **模块化设计**：每个工具独立开发、测试、部署
- 🔄 **可复用**：工具可以在不同流程中重复使用
- 🛠️ **灵活组合**：通过组合不同工具实现复杂业务流程

#### 工具分类

| 分类 | 说明 | 示例 |
|------|------|------|
| **自定义** | 用户自行开发的业务工具 | 自定义数据处理、特定业务逻辑封装 |
| **工具市场** | 从工具市场安装的第三方工具 | 通用工具、行业解决方案 |
| **MCP** | 通过模型上下文协议集成的工具 | 知识库检索、文档查询、实体管理 |
| **基础支撑** | 平台提供的基础能力工具 | 数据表操作、接口调用、资产管理 |
| **交易专用** | 电商/采购等交易场景专用工具 | 订单处理、支付集成、库存管理 |

---

## 2. 文档导航

> 本目录下所有平级子文档及一句话用途。供 LLM 与人类按需深读。

| 文档 | 用途 | 何时读 |
|------|------|--------|
| [`基础结构/app配置.md`](基础结构/app配置.md) | 应用级配置字段说明 | 生成 DSL 时了解顶层 app 结构 |
| [`基础结构/workflow配置.md`](基础结构/workflow配置.md) | 工作流配置字段说明 | 生成 DSL 时了解 workflow 层结构 |
| [`基础结构/graph结构.md`](基础结构/graph结构.md) | 节点和连接结构说明 | 生成 DSL 时了解 nodes/edges 格式 |
| [`基础结构/三段式骨架.md`](基础结构/三段式骨架.md) | 标准三段式动作流骨架与 event.yml 占位符表 | 快速创建标准动作流 |
| [`基础结构/字段约定.md`](基础结构/字段约定.md) | valueMode/formula/节点引用 ID 前缀等字段约定 | 配置节点参数时参考 |
| [`工具说明/MCP工具.md`](工具说明/MCP工具.md) | MCP 工具使用说明（query_action/query_table/read_document 等） | 需要查询资产或文档时 |
| [`学习指南/五步学习流程.md`](学习指南/五步学习流程.md) | AI 生成 DSL 的五步学习流程与资产使用优先级 | 首次生成动作流 DSL 时必读 |
| [`检查清单/六大检查清单.md`](检查清单/六大检查清单.md) | 生成后六大检查清单（结构/节点/连线/资产/数据映射/Webhook） | 生成 DSL 后逐项验证 |
| [`常见错误/常见错误与禁止事项.md`](常见错误/常见错误与禁止事项.md) | 高频错误速查与禁止操作 | 生成 DSL 后快速排错 |
| [`节点/业务动作/通用节点说明.md`](节点/业务动作/通用节点说明.md) | 业务动作节点通用配置规范 | 配置 biz-action 节点时 |
| [`场景示例/index.md`](场景示例/index.md) | 四大场景模式速查（Push/Pull/Schedule/交互） | 查找匹配业务场景时 |

---

## 3. 生成与修改对话速查

### 顶层结构

动作流 DSL 顶层结构为 `app` → `workflow` → `kind` → `version` → `dependencies`，详见 [`基础结构/app配置.md`](基础结构/app配置.md)。

### app 段（元信息）

应用级元信息配置，包含 `id`、`name`、`sign`、`rowguid` 等字段，详见 [`基础结构/app配置.md`](基础结构/app配置.md)。

### workflow.graph.nodes（节点）

#### 节点通用字段（所有 type 共有）

所有节点共有字段：`id`、`data.type`、`data.title`、`position`，详见 [`基础结构/graph结构.md`](基础结构/graph结构.md)。

#### 业务动作节点 (biz-action)

最常用的节点类型，调用业务资产执行操作，详见 [`节点/业务动作/通用节点说明.md`](节点/业务动作/通用节点说明.md)。

#### 结束节点 (end-vue / end)

流程终点，构建响应结果，详见 [`基础结构/graph结构.md`](基础结构/graph结构.md)。

### workflow.graph.edges（边）

连接节点的边，定义流程走向，详见 [`基础结构/graph结构.md`](基础结构/graph结构.md)。

### 标准三段式动作流（推荐架构）

推荐的动作流架构：Webhook 触发 → 业务动作 → 结束响应，详见 [`基础结构/三段式骨架.md`](基础结构/三段式骨架.md)。

### 标准三段式骨架（assets/templates/event.yml）

模板文件 `assets/templates/event.yml` 提供标准三段式骨架占位符，详见 [`基础结构/三段式骨架.md`](基础结构/三段式骨架.md)。

### 字段细节

#### valueMode 与 formula

字段值配置模式与公式引用规则，详见 [`基础结构/字段约定.md`](基础结构/字段约定.md)。

### 修改已有动作流

### 命令清单

### 快速生成脚本

#### 创建标准三段式动作流

```bash
python scripts/add_event.py \
  --app-root <app-root> \
  --name "获取采购立项列表" \
  --sign getDataGridModel \
  --apptag purchaseproject \
  --biz-action PurchaseProjectListRestService_getDataGridModel \
  --context-class com.epoint.ztb.rest.qy.tradeplan.purchaseproject.context.PurchaseProjectContext
```

> 详细脚本参数说明见 [`references/directory-structure.md`](../../directory-structure.md) 的脚本 cheatsheet 节。

#### DSL 校验

```bash
python scripts/check_dsl.py <app-root>/event/<动作流名>.event.yml
```

#### DSL 校验脚本 🆕

校验内容包括：结构完整性、节点 ID 唯一性、edge 引用闭合、formula 跨节点引用等。

#### 通用校验

```bash
python scripts/validate_yml.py --check-refs <app-root>
```

### 修改已有动作流场景速查

由于动作流结构复杂，修改场景主要支持以下典型操作：

| 场景 | 操作方式 |
|------|----------|
| 修改业务节点的 action 或 formData | 找到 `data.type == 'biz-action'` 且 title 匹配的节点，改 `actionData.formData` |
| 增加一个业务节点 | 在 nodes 数组里插入新节点，并新增对应 edges |
| 修改 webhook URL | 找到 `data.type == 'start'` 节点，改 `formData[0].value` |
| 修改响应取值表达式 | 找到 end 节点，改 `responseParams[0].defaultValue.formula.expression` |
| 修改 sign / name | 改顶层 `app.sign` 和 `app.name` |

**避免**：手动重新调整 nodes 的 position 坐标 / 重新生成所有 ID（会破坏 edges 引用）。

### DSL 生成检查清单 🆕

### DSL 生成检查清单

生成动作流 DSL 后必须逐项检查（详见 [`检查清单/六大检查清单.md`](检查清单/六大检查清单.md)）：

| 检查类别 | 关键检查项 |
|---------|-----------|
| **结构** | YAML 以 `---` 开头；顶层顺序 `app` → `workflow` → `kind` → `version` → `dependencies`；`app.id` == `app.rowguid` |
| **节点** | 所有节点 `id` 唯一；开始节点无入站；结束节点无出站；条件节点 true/false 分支都有连线 |
| **连线** | `source`/`target` 指向存在的节点；`id` 格式 `{source}-source-{target}-target`；迭代节点双层连线 |
| **资产** | 优先使用业务专有资产；参数配置来源正确（场景示例 > 面板配置 > query_action） |
| **Webhook** | `requestBody` 有 `UID: "root"` 根节点；数组使用三层结构；`ParentTaskUID` 是字符串 |

### 节点类型速查 🆕

### 节点类型速查

| 节点 `data.type` | 含义 | 说明 |
|------------------|------|------|
| `start` | Webhook 触发 | 流程起点，定义请求体结构 |
| `schedule` | 定时任务触发 | Cron 表达式定时触发 |
| `biz-action` | 业务动作 | 调用业务资产（最常用） |
| `if-else` | 条件分支 | true/false 两条分支 |
| `iteration` / `iteration-vue` | 迭代 | 循环处理列表数据 |
| `code` | 代码执行 | Groovy 脚本 |
| `variable-assigner` | 变量赋值 | 赋值操作 |
| `end-vue` / `end` | 结束 | 流程终点，构建响应 |

> 详细节点文档见 `references/event/动作流/节点/` 目录。

### 四大场景模式（从 dsl-gen-api 合并）🆕

四大场景模式速查见 [`场景示例/index.md`](场景示例/index.md)：Push（接收数据）、Pull（输出数据）、Schedule（定时同步）、交互模式（工作流触发）。

### 资产使用优先级 🆕

详见 [`学习指南/五步学习流程.md`](学习指南/五步学习流程.md) 中的资产使用优先级说明。

### 详细参考文档索引 🆕

详细参考文档索引见上方 § 2 文档导航表。

---

## 4. 与其他资产的引用关系

- **引用其他资产**：
  - `appref`：动作流通过 `dependencies` 引用应用引用配置
  - `mis`：通用数据表资产需要 MIS 表结构（通过 `query_table` 查询）
  - `codeitem`：代码节点可引用代码项
- **被其他资产引用**：
  - `workflow`：工作流中的事件钩子可触发动作流
  - `pagedesigne`：页面设计器按钮事件可调用动作流接口
- **跨资产校验脚本**：`scripts/validate_yml.py --check-refs`
