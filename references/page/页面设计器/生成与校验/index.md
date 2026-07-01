# 生成与校验

## 生成前确认

页面生成前至少确认：

- `title`：页面名称。
- `pagetag`：页面唯一标识。
- `id`：页面 Schema 的稳定本地 id，默认由 `pagetag` 派生：下划线转短横线并追加 `-page`，例如 `projectinfo_list` -> `projectinfo-list-page`。
- `pageId`：页面设计器运行时打开表单/详情页的真实 id，格式通常为 `page_<时间戳>`；列表页本身不需要顶层 `pageId`，列表页弹窗 URL 使用表单/详情页实际页面文件中的 `pageId`。没有真实导出值时，不要手工预留，省略 `--page-id` 让 `add_page.py` 生成。
- `pageType`：`list`、`form`、`detail` 等。
- `device`：默认 `desktop`，只有明确移动端/H5/小屏时使用 `mobile`。
- `model`：关联的 `mis.tableName`、模型别名和字段。
- `modelValue`：组件模型绑定必须使用表达式单元 `{ "$expr": "$model.<modelAlias>[.<fieldName>]" }`，不要使用旧字符串路径。
- `fields`：字段名、标题、类型、用途。
- `query`：列表查询条件。
- `endpoint`：是否有真实接口；没有时不要虚构。
- `openFrom`：模块菜单、工作流、页面按钮或独立访问。
- `references`：是否引用 `mis`、`event`、`workflow`、`module`。

## 需求识别

| 用户表达 | 默认页面类型 | 需要追问 |
|----------|--------------|----------|
| 列表、台账、查询、管理页 | `list` | 查询条件、表格列、按钮、数据来源 |
| 新增、编辑、申请、办理 | `form` | 字段、保存/提交动作、是否工作流页面 |
| 详情、查看、浏览 | `detail` | 只读字段、详情加载来源 |
| H5、移动端、小屏 | 对应类型 + `mobile` | 画布尺寸、移动端专属交互 |
| 工作流办理/审批页面 | `form` 或 `detail` | 申请/审批/浏览 pagetag、关联流程 |

### 工作流表单判定

- 用户只说“新增、编辑、详情表单”时，默认生成普通表单。
- 用户明确说“申请、审批、办理、退回、提交流程”等流程办理语义时，生成工作流表单。
- 用户只需要在页面展示流程状态时，可以用普通详情页加状态展示；只有页面要承载流程按钮、流程右侧区或审批历史时，才生成工作流表单。
- 页面要被 workflow 节点打开时，必须确认页面 `pagetag` 与 workflow 的 `handleurl` / `mobilehandleurl` 引用一致。
- `add_page.py` 不应自行猜测是否工作流表单；调度器或计划中应显式选择工作流表单场景，并提供 `pageId`、`pagetag`、关联 workflow 证据。

## 生成步骤

1. 根据页面类型读取 `../场景示例/index.md` 对应示例。
2. 先读 `../基础结构/组件与字段对照.md`，确认组件、节点类型和字段落点。
3. 根据字段和接口需要读取 `../基础结构/index.md` 中的模型、资源、动作、事件规范。
4. 维护 `.lowcode-plans/<apptag>/page/<asset-id>-plan.md`，记录输入 IR、字段来源、确认记录、生成计划和校验结果。
5. 用户明确批准后调用 `scripts/add_page.py`。
6. 使用 `scripts/validate_json.py` 校验目标页面文件。

## 计划文档

每个页面资产必须维护独立计划：

```text
.lowcode-plans/<apptag>/page/<asset-id>-plan.md
```

计划至少记录：

- 输入 IR 摘要：`title`、`pagetag`、`device`、`pageType`、`endpoint`、字段和查询条件。
- 来源表：字段来自用户、`mis`、接口文档还是推断。
- 页面结构计划：模型、视图树、资源、动作、事件。
- 跨资产引用：`mis.tableName`、`event`、`workflow`、`module`。
- dry-run 命令和结果。
- validate 命令和结果。

## 脚本

```bash
python3 scripts/add_page.py \
  --app-root /path/to/<apptag> \
  --type list \
  --title 采购立项列表 \
  --pagetag purchaseproject_list \
  --fields-json '[{"name":"projectname","label":"项目名称","type":"string"}]'
```

```bash
python3 scripts/validate_json.py <app-root>/page/<页面名>.page.yml
```

如果只想先看页面效果，可以在 `add_page.py` 上加 `--mock-data` 生成兜底数据，或使用 `--initial-json` / `--initial-json-file` 传入精确预览数据，让模型携带默认初始值。

列表页的可见结构应优先来自设计稿或需求文档，而不是组件默认值。选择列、序号列、操作列、组合展示列都应作为显式结构处理：

```json
{
  "table": {
    "props": {
      "showSelectionColumn": true,
      "checkType": "checkbox",
      "showIndexColumn": false,
      "defaultShowIndex": false
    },
    "columns": [
      { "kind": "sequence", "field": "seq", "title": "序", "width": 80, "align": "center" },
      { "field": "project_name", "title": "项目名称" },
      { "field": "onsite_date", "title": "驻场日期" }
    ],
    "actions": {
      "title": "查看",
      "align": "center"
    }
  }
}
```

## 参数映射

| IR 字段 | 脚本/Schema 落点 | 说明 |
|---------|------------------|------|
| `title` | 页面标题，也是默认文件名 | 中文页面名 |
| `pagetag` | 页面唯一标识 | workflow/module 引用的关键值；默认与 `mis.tableName` 对齐生成，如 `projectinfo_form` |
| `id` | 顶层 `id` 和组件 `componentId` 后缀 | 使用稳定 schema id，例如 `projectinfo-list-page`，不要使用 `page_<时间戳>` |
| `pageId` | 表单/详情页顶层 `pageId` | 列表新增/修改/查看弹窗 URL 使用目标页面文件已生成的 `pageId`；没有真实导出值时由 `add_page.py` 生成，列表页不需要顶层 `pageId` |
| `device` | `viewport.device` | 默认 `desktop` |
| `pageType` | 生成模板选择 | `list`、`form`、`detail` |
| `endpoint` | 预留给资源/action 生成 | 仅真实接口存在时生成 |
| `fields` | `models[*].fields` + 控件/列 | 优先来自 mis |
| `query` | 查询模型 + 查询区控件 | 仅列表页需要 |
| `mock-data` | `models[*].initial` | 生成预览兜底数据，不影响正式落盘结构 |
| `initial-json` / `initial-json-file` | `models[*].initial` | 精确传入预览数据 |
| `layout.table.props` | `table.props` | 控制选择列、序号列、分页、边框等表格形态 |
| `layout.table.columns` | `table.children` | 控制可见列顺序、列标题、组合展示列、独立序号列 |

## 模型绑定

组件的 `props.modelValue` 使用表达式单元：

```json
{ "modelValue": { "$expr": "$model.projectinfo.projectname" } }
```

表格绑定集合模型时绑定到模型根：

```json
{ "modelValue": { "$expr": "$model.projectinfo" } }
```

不要再生成旧字符串写法：

```json
{ "modelValue": "projectinfo.projectname" }
```

## 落盘规则

- 新建文件必须使用页面 YAML 后缀：`<页面名>.page.yml`，默认取中文 `title`。
- 新结构固定落在 `<apptag>/page/`。
- 表单页 `pageId` 必须能被列表页按钮 URL 引用；列表页不需要顶层 `pageId`，只保留顶层 `id`。
- 严禁为了提前生成列表 URL 在计划或 IR 中手工预留 `page_<时间戳>`；必须先生成配套表单页，再读取页面文件顶层 `pageId` 回填列表。标准新增、编辑、详情默认复用这个 `pageId`，由设计器当前约定的运行模式区分编辑和只读详情。
- 顶层 `id` 和组件 `componentId` 后缀保持稳定 schema id 逻辑，不使用 `page_<时间戳>`。
- 不生成 `<apptag>/page/*.epage`。
- 不生成 `<apptag>/metadata/...` 老结构。
- 如果页面对应某个 `mis` 表，`pagetag`、`models[*].sqlTableName`、模型 `alias` 默认都应尽量与 `mis.tableName` 保持一致；文件名默认与中文 `title` 保持一致。

## 校验失败处理

- `unknown_action`：补齐顶层 action 或修正事件引用。
- `unknown_resource_operation`：补齐资源 operation 或修正 `use`。
- `unknown_model` / `unknown_field`：修正模型 alias、字段名或从 `mis` 补字段。
- `invalid_event_value`：事件值改为 action id 字符串或字符串数组。
- `duplicate_id`：调整页面或节点显式 id。
- 跨引用失败：先确认模型 alias、字段名、componentId、`modelValue` 是否与设计器 JSON 一致。

