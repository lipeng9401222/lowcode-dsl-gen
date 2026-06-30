# 基础结构

本目录用于按主题索引 Core Schema 基础结构。详细规范仍以 `../../设计器 Schema 规范定义/` 下的原始文档为准。

| 主题 | 参考文档 | 说明 |
|------|----------|------|
| 页面根对象 | [`../../设计器 Schema 规范定义/02-页面 Schema.md`](../../设计器%20Schema%20规范定义/02-页面%20Schema.md) | `schemaVersion`、`kind`、标题、视口、主题、注册区 |
| 视图树 | [`../../设计器 Schema 规范定义/03-视图树.md`](../../设计器%20Schema%20规范定义/03-视图树.md) | `children`、`slots`、组件节点、布局关系 |
| 视图模型 | [`../../设计器 Schema 规范定义/04-视图模型.md`](../../设计器%20Schema%20规范定义/04-视图模型.md) | `record`、`collection`、字段、模型别名 |
| 资源 | [`../../设计器 Schema 规范定义/05-资源.md`](../../设计器%20Schema%20规范定义/05-资源.md) | endpoint、资源操作、资源引用 |
| 动作与事件 | [`../../设计器 Schema 规范定义/06-动作与事件.md`](../../设计器%20Schema%20规范定义/06-动作与事件.md) | actions、events、动作步骤 |
| 规则与表达式 | [`../../设计器 Schema 规范定义/07-规则与表达式.md`](../../设计器%20Schema%20规范定义/07-规则与表达式.md) | 校验、显隐、禁用、表达式边界 |
| 组件文档 | [`组件文档/index.md`](组件文档/index.md) | 组件属性、事件、布局与控件能力原文 |
| 组件与字段对照 | [`组件与字段对照.md`](组件与字段对照.md) | 组件文档名、JSON 节点类型、字段含义、选型矩阵、关键 props、生成器覆盖范围 |

## 1. 页面根对象

页面根对象必须能被识别为 Core Schema 页面：

```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "title": "采购立项列表",
  "viewport": { "device": "desktop" },
  "theme": {},
  "models": [],
  "resources": {},
  "actions": {},
  "events": {},
  "children": []
}
```

生成规则：

- `schemaVersion` 固定 `core-1.0`。
- `kind` 固定 `page`。
- `viewport.device` 默认 `desktop`；移动端仅在用户明确要求时使用。
- `models` 只放业务数据模型，类型为 `record` 或 `collection`。
- `children` 是唯一页面根视图树，必须是数组。
- `resources`、`actions`、`events` 是顶层注册区，即使为空也保留对象结构。

## 2. 视图树

节点通用字段：

| 字段 | 生成规则 |
|------|----------|
| `id` | 可省略交给 normalizer；显式生成时页面内唯一 |
| `name` | 控件中文名，可用于可读性 |
| `type` | 运行态组件类型，必须非空 |
| `model` | 主数据绑定，短路径如 `taskinfo.taskname` |
| `textModel` | 文本侧绑定，用于下拉、树选择等 text/value 场景 |
| `source` | 只引用顶层 `resources` 的 id |
| `props` | 组件语义配置，不放接口调用和运行时缓存 |
| `style` | 作者显式样式 |
| `events` | 引用顶层 `actions` |
| `visible` | 布尔值或受限表达式 |
| `children` | 默认子节点 |
| `slots` | 具名插槽，值为节点数组 |

结构规则：

- `children` 和 `slots` 都表达子节点，但强互斥组件应按具体组件扩展处理。
- 基础 `ViewNode` 根属性不承载 `label`、`title`、`items`、`gap` 等控件专用字段；简单展示配置写入 `props`。
- 表格 `columns` 是 table 组件的强结构字段，不写入普通节点的 `props.columns`。

## 2.1 组件选型最小流程

写 page JSON 时，skill 至少按下面顺序判断：

1. 页面类型决定骨架：
   - `list`：优先 `toolbar + table`
   - `form/detail`：优先 `layout-manager + collapse + form-layout + form-item`
2. 字段语义决定控件：
   - 普通文本、长文本、数值、布尔、日期、字典、层级分类、人员组织、外部对象、附件图片分别走对应专用控件
3. 组件能力决定 props：
   - 例如 `select` 要确认 `codeItem/multiple/filterable`
   - `date-picker` 要确认 `type/format`
   - `organization-select` 要确认 `mode/range/interactive`
   - `button-edit` 要确认 `dialogConfigGuid/url/pageName`

如果第 2 步和第 3 步没有明确答案，不要直接落盘，先回到 `组件与字段对照.md` 补选型。

## 3. 视图模型

模型生成规则：

- `record`：单条数据，适用于表单、详情、查询条件。
- `collection`：多条数据，适用于表格、列表。
- `alias` 在页面内唯一，字段绑定都通过 alias 短路径引用。
- `source` 可表达 `mis`、`interface` 等来源；优先与已有 `mis` 对齐。
- `sqlTableName` 应与同应用 `mis.tableName` 保持一致。

字段生成规则：

- 字段名使用后端或 `mis` 的真实字段名。
- `label` 优先来自 `mis` 字段描述，其次来自用户确认。
- 字段类型按 Schema 支持类型映射，不确定时保守使用 `string` 并在计划中标注待确认。
- 值/文本成对字段保留 `_text` 或业务已有文本字段，用于 `textModel`。

## 4. 资源

资源只声明页面需要的外部依赖，节点通过 `source` 或 action step 引用。

常见资源类型：

| 类型 | 用途 |
|------|------|
| `endpoint` | REST 接口，如列表、详情、保存 |
| `dictionary` | 数据字典 |
| `tree` | 树选择、组织机构、分类 |
| `upload` | 上传资源 |
| `route` | 路由或页面跳转 |
| `workflow` | 工作流能力 |

`endpoint` 资源必须声明 `operations`，例如 `list`、`detail`、`save`。动作中通过 `资源id.操作id` 引用。

## 5. 动作与事件

动作统一放在顶层 `actions`：

```json
{
  "actions": {
    "refreshList": {
      "steps": [
        {
          "use": "taskApi.list",
          "params": { "keyword": "model.search.keyword" },
          "assign": { "model.taskList": "response.items" }
        }
      ]
    }
  }
}
```

事件只引用 action id：

```json
{
  "events": {
    "load": "refreshList"
  }
}
```

白名单 step：`use`、`assign`、`run`、`validate`、`reset`、`log`、`notify`、`open`、`close`、`confirm`、`workflow`、`navigate`、`function`。

## 6. 规则与表达式

- 字段级校验写在 `models[*].fields.<field>.rules`。
- 节点显隐写在 `visible`，不能提升到 `props`。
- 表达式必须使用受限语法，不写任意 JavaScript。
- `validate[].validator` 必须引用存在的顶层 action。
- `state(path)` 的 path 必须能解析到节点 id 或 `page.*` 键。
