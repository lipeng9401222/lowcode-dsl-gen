# 页面 Schema 规范定义

本目录是 `lowcode-dsl-gen` 中页面设计器 `pagedesigne` 资产的 Core Schema 规范来源。生成页面资产时，产物落到应用根目录的 `page/*.page.yml`，文件内容承载页面设计器 Core Schema。

> 当前目录只描述页面 Schema 本身；应用目录、文件命名、计划文档、脚本调用和跨资产校验规则，统一以 `../../directory-structure.md` 和 `../../conventions.md` 为准。

## 资产定位

`page` 参考资料服务于 `pagedesigne` 资产生成，主要解决：

- 列表页、表单页、详情页等页面结构生成。
- 页面视图树、视图模型、字段绑定、资源、动作、事件的规范化。
- 根据 `mis`、`event`、`workflow` 等资产补齐页面引用。
- 为 `scripts/add_page.py` 和 `scripts/validate_json.py` 提供生成与校验依据。

输出位置：

```text
<apptag>/page/<页面名>.page.yml
```

## 文档导航

| 文档 | 用途 | 何时读 |
|------|------|--------|
| [`01-概览.md`](01-概览.md) | Core Schema 的适用范围、设计原则和模块关系 | 首次生成或理解页面协议边界时 |
| [`02-页面 Schema.md`](02-页面%20Schema.md) | 页面顶层结构、基础字段和注册区 | 生成页面根对象时 |
| [`03-视图树.md`](03-视图树.md) | `children`、`slots`、组件节点和布局树 | 组织页面结构和组件层级时 |
| [`04-视图模型.md`](04-视图模型.md) | `models`、字段、绑定、record/collection | 设计表单模型、列表模型和字段绑定时 |
| [`05-资源.md`](05-资源.md) | `resources`、接口资源、资源操作定义 | 页面需要调用后端接口或动作流时 |
| [`06-动作与事件.md`](06-动作与事件.md) | `actions`、`events`、动作步骤和事件引用 | 页面加载、按钮点击、保存、刷新等交互时 |
| [`07-规则与表达式.md`](07-规则与表达式.md) | 校验规则、显示规则、表达式边界 | 处理必填、显隐、禁用和业务规则时 |
| [`08-规范化与校验.md`](08-规范化与校验.md) | normalize/validate 要求和常见静态错误 | 落盘前和校验报错修复时 |
| [`列表示例.md`](列表示例.md) | 内嵌真实设计器导出的列表页 Core Schema 示例 | 生成列表页、查询区、表格、工具栏时 |
| [`表单示例.md`](表单示例.md) | 内嵌真实设计器导出的表单页 Core Schema 示例 | 生成新增、编辑、详情、审批表单时 |
| [`工作流列表结构.md`](工作流列表结构.md) | 工作流列表入口的按钮、URL 和流程参数结构 | 生成从列表发起或查看流程的页面时 |
| [`工作流表单示例.md`](工作流表单示例.md) | 内嵌真实设计器导出的工作流表单 Core Schema 示例 | 生成申请、审批、办理、浏览表单时 |

## 生成优先级

生成页面时按下面顺序读取资料：

1. 先读本 `index.md`，确认页面资产边界和产物位置。
2. 根据页面类型优先读取内嵌真实 JSON 的示例文档：列表页读 `列表示例.md`；表单/详情页读 `表单示例.md`。
3. 示例文档中的“示例一 / 示例二”均为完整 Core Schema，可直接作为结构基线。
4. 按需读取结构规范：页面根对象读 `02-页面 Schema.md`，组件层级读 `03-视图树.md`，字段和模型读 `04-视图模型.md`。
5. 需要接口、动作流或页面事件时，再读 `05-资源.md` 和 `06-动作与事件.md`。
6. 落盘前必须读 `08-规范化与校验.md`，并运行校验脚本。

真实 JSON 样例的定位：

- `列表示例.md`：内嵌项目列表、任务列表等列表页完整 JSON，重点参考 `list-container -> toolbar + table`、`collection` 模型、表格列和工具栏按钮的组织方式。
- `表单示例.md`：内嵌项目表单、任务表单等表单页完整 JSON，重点参考 `layout-manager -> slots.main -> collapse -> collapse-item -> form-layout -> form-item -> control`、`record` 模型和字段绑定方式。
- `工作流列表结构.md`：基于真实工作流列表导出的结构差异，重点参考 `process-button`、`processGuid` 和行操作 URL。
- `工作流表单示例.md`：内嵌工作流表单完整 JSON，重点参考 `workflow-button`、`workflow-right`、`workflow-history`、`scrollbar`、`anchor` 和附件上传结构。
- 生成新页面时只复用结构规律，不复制样例里的业务字段、标题、模型名、页面 id 或节点 id；这些值必须来自当前需求、MIS 或已生成资产。

## 页面顶层结构

页面 schema 是一个单一页面对象，顶层字段以 Core Schema 为准：

```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "id": "purchaseproject-list",
  "title": "采购立项列表",
  "viewport": {},
  "theme": {},
  "models": [],
  "resources": {},
  "actions": {},
  "events": {},
  "children": []
}
```

核心约束：

- `models` 必须是数组。
- `resources`、`actions`、`events` 是顶层注册区。
- `children` 是页面根视图树。
- 节点事件只引用顶层 `actions`，不要在节点内联复杂后端逻辑。
- 页面中的资源和动作只在真实需要时生成，不为纯静态页面强行补接口。

## 页面类型规则

### 列表页

适用于查询区、表格、分页、工具栏按钮等场景。

- 表格数据使用 `collection` 模型。
- 查询条件可以使用独立 `record` 模型，也可以按平台标准列表示例绑定到列表模型。
- 有真实接口时，补 `endpoint` 资源、刷新 action 和页面 `load` 事件。
- 无真实接口且走平台标准列表能力时，不强行生成自定义接口资源。
- 默认保留分页配置，常用默认 `pageSize: 10`。

### 表单页

适用于新增、编辑、详情和流程表单。

- 单对象数据使用 `record` 模型。
- 控件通过 `props.modelValue` 或对应显示属性绑定字段。
- 保存、提交、审批等按钮通过 `actions` 承载行为。
- 没有接口或动作流信息时，只生成页面结构和字段绑定，不虚构保存逻辑。
- 工作流页面需要与 `workflow` 的 `handleurl` / `mobilehandleurl` 使用的 `pagetag` 保持一致。

## 跨资产关系

- `mis`：页面模型字段优先来自同应用 `mis` 的表字段；`models[*].sqlTableName` 应能回到对应 `mis.tableName`。
- 页面英文标识默认也与 `mis.tableName` 对齐：推荐 `pagetag=<mis.tableName>_<pageType>`，模型 `alias` 默认与 `mis.tableName` 一致；文件名默认使用中文 `title`，即 `<页面名>.page.yml`。
- `event`：复杂状态变更、外部推送、工作流回调等动作可通过资源或 action 引用动作流，但标准 CRUD 不主动生成 event。
- `workflow`：工作流节点通过页面 `pagetag` 打开申请、审批、浏览等页面；页面生成完成后，workflow 才能稳定引用它。
- `module`：菜单 URL 可指向页面运行时地址，例如 `home/vuepagedesigner/renderer/list?pagetag=<pagetag>`。

## 默认值约定

- 默认 `viewport.device = desktop`。
- 只有用户明确提出移动端、H5、小屏时才生成 mobile 相关结构。
- 默认主题保持轻量，不主动引入运行时框架私有字段。
- 字典、人员、树选择等需要同时显示文本时，保留值字段和对应 `_text` 字段。

## 校验清单

页面生成完成后至少检查：

- `schemaVersion` 是否为 `core-1.0`。
- `kind` 是否为 `page`。
- `pagetag` 是否存在且在应用内唯一。
- 模型 `alias` 是否唯一。
- 字段绑定是否引用真实模型和字段。
- `events` 引用的 action 是否存在。
- `actions[*].steps[*].use` 引用的资源和操作是否存在。
- 输出路径是否为 `<app-root>/page/*.page.yml`。
- 生成后执行 `scripts/validate_json.py <target-file>`。
