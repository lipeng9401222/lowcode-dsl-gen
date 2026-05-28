# Graph 图结构

## 概述

Graph 是 Dify 工作流的核心结构，定义了节点及其连接关系。

```yaml
graph:
  edges: []          # 节点连接
  nodes: []          # 节点定义
  viewport: {}       # 视图配置
```

## Nodes (节点)

### 节点通用结构

每个节点的通用结构（流式处理版本）：

```yaml
nodes:
- data:                     # 节点数据
    variables: []           # 变量配置
    type: "start"           # 节点类型
    title: "Webhook触发"     # 节点标题
    selected: false         # 是否选中
    desc: ""                # 节点描述
  targetPosition: "left"    # 目标位置
  width: 244                # 宽度
  sourcePosition: "right"   # 源位置
  positionAbsolute:         # 绝对位置
    x: 80
    y: 282
  id: "1753410057316"       # 节点ID
  position:                 # 位置
    x: 80
    y: 282
  type: "custom"            # 节点类型
  selected: false           # 是否选中
  height: 54                # 高度
  sourceId: "1753410057316" # 源节点ID
  resultType: 2             # 结果类型
```

### 节点通用字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 节点唯一标识符，通常为时间戳 |
| type | string | 节点类型，流式处理版本使用 "custom" |
| data | object | 节点核心数据 |
| data.type | string | 节点的实际类型（start、llm、code等） |
| data.title | string | 节点显示标题 |
| data.desc | string | 节点描述 |
| data.selected | boolean | 是否选中状态 |
| data.variables | array | 节点变量配置 |
| position | object | 节点在画布上的位置（相对） |
| positionAbsolute | object | 节点在画布上的绝对位置 |
| width | number | 节点宽度 |
| height | number | 节点高度 |
| sourcePosition | string | 输出连接点位置（left/right/top/bottom） |
| targetPosition | string | 输入连接点位置（left/right/top/bottom） |

### 节点类型

| 类型 | 说明 | 文档链接 |
|------|------|----------|
| start | Webhook 触发节点 | [详情](../触发节点/webhook触发节点.md) |
| llm | LLM 节点 | [详情](../处理节点/LLM节点.md) |
| code | 代码节点 | [详情](../处理节点/代码节点.md) |
| biz-action | 业务动作节点（数据表操作） | [查询](../数据节点/数据表查询节点.md) / [插入](../数据节点/数据表插入节点.md) |
| if-else | 条件判断节点 | [详情](../控制节点/条件判断节点.md) |
| iteration | 迭代节点 | [详情](../控制节点/迭代节点.md) |
| iteration-start | 迭代开始节点 | [详情](../控制节点/迭代节点.md#迭代开始节点) |
| end-vue | 结束节点 | [详情](../结束节点/结束节点.md) |

## Edges (连接)

### 连接结构

```yaml
edges:
- sourceHandle: "source"    # 源连接点
  data:                     # 连接数据
    sourceType: "start"     # 源节点类型
    targetType: "llm"       # 目标节点类型
    isInLoop: false         # 是否在循环中
  id: "1753410057316-source-1753410080199-target"  # 连接ID
  source: "1753410057316"   # 源节点ID
  type: "custom"            # 连接类型
  targetHandle: "target"    # 目标连接点
  target: "1753410080199"   # 目标节点ID
  zIndex: 0                 # 层级
```

### 连接字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 连接唯一标识符，格式：`{源节点ID}-source-{目标节点ID}-target` |
| source | string | 源节点ID |
| target | string | 目标节点ID |
| sourceHandle | string | 源连接点名称，通常为 "source" |
| targetHandle | string | 目标连接点名称，通常为 "target" |
| type | string | 连接类型，通常为 "custom" |
| data.sourceType | string | 源节点的类型 |
| data.targetType | string | 目标节点的类型 |
| data.isInLoop | boolean | 是否在循环中 |
| zIndex | number | 显示层级 |

### 连接命名规范

连接 ID 的标准格式：
```
{源节点ID}-{源连接点名称}-{目标节点ID}-{目标连接点名称}
```

示例：
```
1753410057316-source-1753410080199-target
```

## Viewport (视图配置)

### 视图结构

```yaml
viewport:
  x: 94.15419129314671      # 视图X坐标
  "y": 266.85527211554086   # 视图Y坐标
  zoom: 0.7071067811865487   # 缩放比例
```

### 字段说明

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| x | number | 视图水平位置坐标 | 94.15419129314671 |
| y | number | 视图垂直位置坐标 | 266.85527211554086 |
| zoom | number | 视图缩放比例 | 0.7071067811865487 (约 70.7%) |

### 缩放比例说明

- `1.0`：100% 原始大小
- `0.5`：50% 缩小
- `2.0`：200% 放大
- 通常范围：0.1 ~ 3.0

## 节点布局建议

1. **合理间距**：节点之间保持适当间距，便于查看和编辑
2. **从左到右**：按执行顺序从左到右排列节点
3. **分层布局**：复杂流程可以分层展示，使用视图缩放
4. **对齐原则**：同类型或同层级节点对齐，提高可读性

## 相关文档

- [App 配置](./app配置.md)
- [Workflow 配置](./workflow配置.md)
- [节点类型详解](../README.md#节点类型)
