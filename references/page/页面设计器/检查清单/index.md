# 检查清单

生成或修改页面设计器 JSON 后逐项检查：

## 1. 文件与目录

1. 文件路径是 `<apptag>/page/<页面名>.json`。
2. 文件名使用 `.json` 后缀。
3. 不存在 `<apptag>/metadata/...` 新增路径。
4. 不新增 `<apptag>/page/*.epage`。
5. 页面 `pagetag` 在应用内唯一。

## 2. 页面根对象

1. `schemaVersion` 为 `core-1.0`。
2. `kind` 为 `page`。
3. `title` 与用户确认页面名一致。
4. `viewport.device` 符合用户要求，默认 `desktop`。
5. 顶层 `pageId` 存在，使用真实设计器格式 `page_<时间戳>`。
6. 顶层 `id` 可作为本地 schema/component id 基础，不要求与 `pageId` 一致。
7. `models` 是数组。
8. `resources`、`actions`、`events` 是对象。
9. `children` 是数组。

## 3. 模型与字段

1. 模型 `alias` 不重复。
2. 模型类型只使用 `record` 或 `collection`。
3. 字段绑定引用真实模型和字段。
4. `textModel` 引用同一上下文可写字段。
5. 与 `mis` 关联的页面，`sqlTableName` 能匹配同应用 `mis.tableName`。
6. 字段 label、类型和规则有来源记录。

## 4. 视图树

1. 每个节点 `type` 是非空字符串。
2. 节点 `source` 引用存在的资源。
3. 节点 `events` 只引用顶层 action。
4. `visible` 只使用布尔值或受限表达式。
5. 显式 `id` 页面内不重复。
6. 表格列结构完整，字段列能映射到模型字段。
7. 基础节点不滥用根属性承载组件专用字段。

## 5. 资源、动作、事件

1. 顶层 `events` 引用的 action 存在。
2. 节点 `events` 引用的 action 存在。
3. `events` value 只使用字符串或字符串数组。
4. `actions.steps[].use` 能找到对应 `resource.operation`。
5. `actions.steps[].run` 不形成循环依赖。
6. `assign` 左侧是可写引用。
7. `function.name` 引用运行时允许的注册方法，不内联 JS。

## 6. 场景规则

1. 标准 CRUD 页面不主动生成 event。
2. 列表页分页、查询条件、表格列结构完整。
3. 表单页必填、只读、隐藏等规则有明确来源。
4. 详情页不生成保存按钮。
5. 列表页新增/修改/查看 URL 中的 `pageId` 取自目标表单页 JSON 的顶层 `pageId`。
6. 工作流引用的申请、审批、浏览页面 `pagetag` 已存在。
7. 模块菜单 URL 指向的 `pagetag` 已存在。

## 7. 脚本校验

1. `scripts/validate_json.py <target-file>` 无 error。
2. 校验命令和结果已写入页面资产计划文档。
