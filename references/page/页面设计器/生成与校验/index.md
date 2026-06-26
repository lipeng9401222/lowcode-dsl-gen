# 生成与校验

## 生成前确认

页面生成前至少确认：

- `title`：页面名称。
- `pagetag`：页面唯一标识。
- `id`：页面 Schema 的稳定本地 id，默认由 `pagetag` 派生：下划线转短横线并追加 `-page`，例如 `projectinfo_list` -> `projectinfo-list-page`。
- `pageId`：页面设计器运行时打开表单/详情页的真实 id，格式通常为 `page_<时间戳>`；列表页本身不需要顶层 `pageId`，列表页弹窗 URL 使用表单页的 `pageId`。
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

## 生成步骤

1. 根据页面类型读取 `../场景示例/index.md` 对应示例。
2. 根据字段和接口需要读取 `../基础结构/index.md` 中的模型、资源、动作、事件规范。
3. 维护 `.lowcode-plans/<apptag>/page/<asset-id>-plan.md`，记录输入 IR、字段来源、确认记录、生成计划和校验结果。
4. 用户明确批准后调用 `scripts/add_page.py`。
5. 使用 `scripts/validate_json.py` 校验目标 JSON 文件。

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
python3 scripts/validate_json.py <app-root>/page/<页面名>.json
```

## 参数映射

| IR 字段 | 脚本/Schema 落点 | 说明 |
|---------|------------------|------|
| `title` | 页面标题、文件名候选 | 中文页面名 |
| `pagetag` | 页面唯一标识 | workflow/module 引用的关键值 |
| `id` | 顶层 `id` 和组件 `componentId` 后缀 | 使用稳定 schema id，例如 `projectinfo-list-page`，不要使用 `page_<时间戳>` |
| `pageId` | 表单/详情页顶层 `pageId` | 列表新增/修改/查看弹窗 URL 使用表单页 `pageId`，例如 `page_1781580614416`；列表页不需要顶层 `pageId` |
| `device` | `viewport.device` | 默认 `desktop` |
| `pageType` | 生成模板选择 | `list`、`form`、`detail` |
| `endpoint` | 预留给资源/action 生成 | 仅真实接口存在时生成 |
| `fields` | `models[*].fields` + 控件/列 | 优先来自 mis |
| `query` | 查询模型 + 查询区控件 | 仅列表页需要 |

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

- 新建文件必须使用 JSON 后缀：`<页面名>.json`。
- 新结构固定落在 `<apptag>/page/`。
- 表单页 `pageId` 必须能被列表页按钮 URL 引用；列表页不需要顶层 `pageId`，只保留顶层 `id`。
- 顶层 `id` 和组件 `componentId` 后缀保持稳定 schema id 逻辑，不使用 `page_<时间戳>`。
- 不生成 `<apptag>/page/*.epage`。
- 不生成 `<apptag>/metadata/...` 老结构。

## 校验失败处理

- `unknown_action`：补齐顶层 action 或修正事件引用。
- `unknown_resource_operation`：补齐资源 operation 或修正 `use`。
- `unknown_model` / `unknown_field`：修正模型 alias、字段名或从 `mis` 补字段。
- `invalid_event_value`：事件值改为 action id 字符串或字符串数组。
- `duplicate_id`：调整页面或节点显式 id。
- 跨引用失败：先确认模型 alias、字段名、componentId、`modelValue` 是否与设计器 JSON 一致。

