# App 配置详解

## 配置结构

```yaml
app:
  mode: "actflow"                   # 工作流模式
  use_icon_as_answer_icon: false    # 是否使用图标作为回答图标
  icon: ""                          # Emoji 图标
  name: "流式处理"                  # 应用名称
  sign: "liushichuli"               # 动作流标识（与接口标识一致，必须唯一）
  description: ""                   # 应用描述
  icon_background: ""               # 图标背景色(16进制)
  id: "bd3d9f5a-05e3-4606-901e-1f9c19a4bf97"  # 应用ID（UUID格式，动作流唯一标识）
  created_at: 1737450004            # 创建时间（Unix时间戳，秒级）
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| mode | string | ✅ | 工作流模式 | `actflow` / `advanced-chat` / `workflow` |
| use_icon_as_answer_icon | boolean | ❌ | 是否使用图标作为回答图标 | true / false |
| icon | string | ❌ | Emoji 图标 | "🤖" |
| name | string | ✅ | 应用名称（中文） | "流式处理" |
| sign | string | ✅ | 动作流标识（与接口标识一致，**必须唯一**，位于 name 之后） | "liushichuli" |
| description | string | ❌ | 应用描述 | "这是一个流式处理工作流" |
| icon_background | string | ❌ | 图标背景色(16进制) | "#FF5733" |
| id | string | ✅ | 应用唯一标识符（UUID格式，**动作流唯一标识**） | "bd3d9f5a-05e3-4606-901e-1f9c19a4bf97" |
| created_at | integer | ✅ | 创建时间（Unix时间戳，秒级） | 1737450004 |
| sign | string | ✅ | 动作流标识（与接口标识一致，**必须唯一**） | "liushichuli" |

**⚠️ 重要约束**：
- **id 字段为动作流的唯一标识**，使用标准 UUID 格式，确保全局唯一
- **sign 字段为动作流标识**，与接口标识一致，必须唯一
- **created_at 使用秒级时间戳**（10位数字），可通过 `Math.floor(Date.now() / 1000)` 生成

## 工作流模式 (mode)

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `actflow` | 行动流模式 | 自动化工作流、API集成、流式处理 |
| `advanced-chat` | 高级对话模式 | 多轮对话、智能客服 |
| `workflow` | 标准工作流模式 | 单次任务、数据处理 |

### actflow 模式特点

- 支持流式处理
- 适合 Webhook 触发
- 可实现复杂的业务流程自动化
- 支持多节点协同工作

### advanced-chat 模式特点

- 支持多轮对话
- 保存对话历史
- 适合客服场景
- 支持上下文理解

### workflow 模式特点

- 单次执行
- 适合批处理任务
- 数据转换和处理
- 简单的自动化流程

## 配置建议

1. **选择合适的模式**：根据业务场景选择对应的工作流模式
2. **设置有意义的名称**：便于管理和识别
3. **添加描述信息**：帮助团队成员理解工作流用途
4. **配置图标**：使用合适的 Emoji 或背景色便于视觉识别
5. **生成唯一 ID**：使用标准 UUID 格式，确保动作流全局唯一
6. **设置动作流标识（sign）**：
   - 与接口标识一致，确保在整个系统中唯一
   - 示例：`name: "采购立项管理"` → `sign: "caigoulixiangguanli"`
7. **设置创建时间**：使用当前时间的秒级时间戳（10位数字）

## 生成示例

假设要创建名为"采购立项管理"的动作流：

```yaml
app:
  mode: "actflow"
  use_icon_as_answer_icon: false
  icon: ""
  name: "采购立项管理"
  sign: "caigoulixiangguanli"                  # 动作流标识，位于 name 之后
  description: "处理采购立项的审批和数据管理"
  icon_background: ""
  id: "56534901-7d24-435a-9073-bcd9286583af"  # 生成的UUID，动作流唯一标识
  created_at: 1737450004                        # 当前时间戳（秒级）
```

## 顶层结构总览

动作流 yml 文件的顶层结构顺序如下（**必须严格遵循此顺序**）：

```yaml
type: event              # 固定标识（顶层第一行）
app:                     # 应用元信息（第二块）
  mode: "actflow"
  ...
kind: "app"              # 固定值
version: "3.0"           # 固定值
dependencies: []         # 固定空数组
workflow:                # 流程编排（节点 + 边）
  conversation_variables: []
  environment_variables: []
  features: {}
  graph:
    nodes: []
    edges: []
    viewport: {}
```

> ⚠️ **顶层字段顺序**：`type` → `app` → `kind` → `version` → `dependencies` → `workflow`。这是 `assets/templates/event.yml` 模板的权威顺序。

### 顶层字段总表

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| `type` | string | ✅ | 资产类型标识 | `event` |
| `app` | object | ✅ | 应用元信息（详见下方字段说明） | — |
| `kind` | string | ✅ | 固定值 | `"app"` |
| `version` | string | ✅ | 固定值 | `"3.0"` |
| `dependencies` | array | ✅ | 固定空数组 | `[]` |
| `workflow` | object | ✅ | 流程编排（详见 [workflow配置.md](./workflow配置.md)） | — |

### app 段完整字段总表

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| `mode` | string | ✅ | 固定 `actflow` | `"actflow"` |
| `use_icon_as_answer_icon` | boolean | ❌ | 是否使用图标作为回答图标 | `false` |
| `icon` | string | ❌ | Emoji 图标 | `""` |
| `name` | string | ✅ | 动作流名称（中文） | `"采购立项_列表_获取列表数据接口"` |
| `sign` | string | ✅ | 接口标识（与 controller 方法名一致，**必须唯一**） | `"getDataGridModel"` |
| `description` | string | ❌ | 应用描述 | `""` |
| `icon_background` | string | ❌ | 图标背景色(16进制) | `""` |
| `id` | string | ✅ | UUID，动作流唯一标识 | `"57b3467e-5008-4953-a4dc-36f835b48a35"` |
| `rowguid` | string | ✅ | 与 `id` 相同（**必须一致**） | `"57b3467e-5008-4953-a4dc-36f835b48a35"` |
| `created_at` | integer | ❌ | Unix 秒级时间戳 | `1776765978` |
| `code` | string | ❌ | name 的小写化、去特殊字符 | `"purchaseprojectgetdatagridmodel"` |

> ⚠️ `app.id` 与 `app.rowguid` **必须相等**，这是校验规则之一。

## 相关文档

- [Workflow 配置](./workflow配置.md)
- [Graph 结构](./graph结构.md)
- [三段式骨架](./三段式骨架.md)
- [字段约定](./字段约定.md)
