# 页面设计器：page json

## 1. 资产定位与边界

`pagedesigne` 资产描述页面设计器页面，文件落在应用根目录：

```text
<apptag>/page/<页面名>.json
```

页面内容以 Core Schema 表达，覆盖页面标题、`pagetag`、设备类型、页面类型、视图树、视图模型、资源、动作、事件、规则和字段绑定。

> 详细 Core Schema 字段以 [`../设计器 Schema 规范定义/index.md`](../设计器%20Schema%20规范定义/index.md) 为准；本目录负责把这些字段组织成 lowcode-dsl-gen 可执行的页面生成规则。

### 何时生成页面设计器资产

| 场景 | 说明 |
|------|------|
| 列表页 | 查询区、工具栏、表格、分页、行操作 |
| 表单页 | 新增、编辑、详情、审批办理表单 |
| 工作流办理页 | 被 `workflow` 的 `handleurl` / `mobilehandleurl` 通过 `pagetag` 引用 |
| 模块菜单页 | 被 `module` 菜单 URL 指向页面运行时 |

### 不在本资产范围内的事

- `mis` 表结构和字段主数据定义。
- 标准 CRUD 后端接口实现。
- 复杂接口编排和状态变更联动，属于 `event`。
- 审批节点、流转、按钮、材料和版本结构，属于 `workflow`。
- Java、Vue 高码实现。

### 设计红线

- 新建页面资产只能写入 `<apptag>/page/*.json`。
- 不生成 `<apptag>/page/*.epage`，不生成 `<apptag>/metadata/...`。
- 页面 Schema 必须保持 `schemaVersion: core-1.0`、`kind: page`。
- 视图节点事件只能引用顶层 `actions`，不能把动作步骤内联到节点。
- 资源必须声明在顶层 `resources`，节点只能通过 `source` 引用资源 id。
- 标准 CRUD 页面不主动生成 `event`；只有状态变更联动、外部同步、工作流回调等编排型诉求才考虑动作流。
- 默认 `device=desktop`；只有用户明确移动端、H5、小屏时才使用 `mobile`。

## 2. 文档导航

| 子目录 | 何时读 |
|--------|--------|
| [`../设计器 Schema 规范定义/index.md`](../设计器%20Schema%20规范定义/index.md) | Core Schema 主规范入口 |
| [`基础结构/index.md`](基础结构/index.md) | 快速了解页面根对象、视图树、模型、资源、动作的分工 |
| [`场景示例/index.md`](场景示例/index.md) | 按列表页、表单页选择可参考示例 |
| [`生成与校验/index.md`](生成与校验/index.md) | 生成前字段收集、脚本调用、落盘和校验流程 |
| [`检查清单/index.md`](检查清单/index.md) | 交付前逐项自检 |
| [`常见错误/index.md`](常见错误/index.md) | 校验失败或页面运行异常时排查 |

## 3. 生成与修改速查

生成页面前必须确认：

- 页面名称 `title`
- 页面标识 `pagetag`
- 页面类型 `pageType`：常见为 `list`、`form`、`detail`
- 设备类型 `device`：默认 `desktop`
- 关联模型：优先来自同应用 `mis`
- 字段清单：字段名、标题、类型、是否查询条件、是否表格列、是否表单控件
- 后端来源：标准列表、REST endpoint、动作流 event，或暂不绑定接口
- 页面打开来源：模块菜单、工作流节点、按钮跳转或独立页面

生成后必须执行：

```bash
python3 scripts/validate_json.py <target-file>
```

## 4. 与其他资产的引用关系

- 引用 `mis`：页面模型字段应与 `mis.tableName` 和字段定义保持一致。
- 可引用 `event`：按钮或页面事件可绑定动作流，但标准 CRUD 不主动生成动作流。
- 被 `workflow` 引用：工作流办理、浏览节点通过 `pagetag` 打开页面。
- 被 `module` 引用：菜单 URL 可指向页面设计器渲染器。

## 5. 页面 Schema 生成策略

### 页面根对象

- `schemaVersion` 固定 `core-1.0`。
- `kind` 固定 `page`。
- `id` 可由 normalizer 生成；如果生成器显式写入，必须稳定且页面内唯一。
- `title` 使用用户确认的页面名称。
- `viewport.device` 默认 `desktop`。
- `models`、`resources`、`actions`、`events`、`children` 必须存在且类型正确。

### 视图树

- 页面结构从 `children` 开始；具名区域使用 `slots`。
- 基础节点使用 `type`、`model`、`textModel`、`source`、`props`、`style`、`events`、`visible`、`children`。
- `model` 使用短路径，如 `taskinfo.taskname`。
- `textModel` 只用于值/文本成对控件，且必须能解析到可写字段。
- 表格列属于表格组件强结构，不降级写到普通节点 `props.columns`。

### 视图模型

- 表单、详情、审批办理页使用 `record` 模型。
- 列表表格使用 `collection` 模型。
- 查询条件可使用独立 `record` 模型；若沿用平台标准列表示例，也可绑定列表模型字段。
- 字段类型和 label 优先来自同应用 `mis`。

### 资源、动作、事件

- `resources` 声明 endpoint、dictionary、tree、upload、route、workflow 等外部依赖。
- `actions` 只使用规范白名单 step：`use`、`assign`、`run`、`validate`、`reset`、`log`、`notify`、`open`、`close`、`confirm`、`workflow`、`navigate`、`function`。
- 页面级 `events.load` 常用于列表刷新或详情加载。
- 节点事件常见 `click`、`change`、`submit`、`reset`、`pageChange`、`sortChange`、`selectionChange`。

## 6. 资料是否够用

当前 `page` 参考目录已有 Core Schema 主体规范和列表/表单示例，足够支撑第一阶段的页面设计器 JSON 生成：

- 列表页：已有查询区、表格、工具栏、分页示例。
- 表单页：已有 record 模型、表单控件和按钮示例。
- 资源/动作：已有 endpoint、actions、events 规范。
- 校验：已有规范化与校验规则。

后续建议补强三类资料：

- 详情页/只读页独立示例。
- 工作流办理页示例，包括申请、审批、浏览三种 `pagetag` 用法。
- 页面与 `module` 菜单 URL、`workflow.handleurl` 的完整联动示例。
