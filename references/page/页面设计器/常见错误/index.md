# 常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| 输出到 `pagedesigne/*.json` 或 `page/*.epage` | 混用了旧页面目录或旧页面文件格式 | 改为 `<apptag>/page/*.json` |
| 仍引用外部或旧技能路径 | 从历史文档复制后未更新路径 | 统一改为 `docs/skills/lowcode-dsl-gen/references/page/...` |
| 页面节点内联接口调用逻辑 | 破坏顶层资源/动作注册区 | 把接口放入 `resources`，调用放入 `actions` |
| `events` 直接写复杂对象 | 事件规范要求引用 action | 先定义 `actions.<id>`，再在 `events` 写 action id |
| `use` 找不到资源操作 | `resourceId.operationId` 没有对应定义 | 补齐 `resources.<resourceId>.operations.<operationId>` |
| 标准 CRUD 生成 event | event 只用于编排型业务逻辑 | 标准列表、详情、新增、修改、删除走标准接口或页面资源 |
| 工作流打开页面失败 | `workflow.handleurl` 中的 `pagetag` 不存在或不一致 | 先生成页面，再让 workflow 引用同一个 `pagetag` |
| 字段显示名丢失 | 只从接口字段推断，没有对齐 `mis` 字段说明 | 优先从 `mis` 字段描述或用户确认信息补 label |
| `model` 绑定解析失败 | alias 写错或字段没有进入 `models` | 修正 alias，或从 `mis`/字段清单补齐字段 |
| `textModel` 无法写入 | 文本字段不存在或不在同一模型上下文 | 补 `_text` 字段或改用已有文本字段 |
| 把 `columns` 写进普通节点 `props` | 表格列是 table 强结构 | 在 table 组件结构中声明 columns |
| `visible` 写成任意 JS | Schema 只允许布尔值或受限表达式 | 改成受限表达式或拆成 action/state |
| `actions.steps[].run` 循环调用 | action A run B，B 又 run A | 拆分公共步骤或改为单向调用 |
| `assign` 左侧不可写 | 把响应赋给了只读表达式或不存在路径 | 左侧改为 `model.<alias>.<field>` 等可写引用 |
| 页面根缺少 `children` | 只生成了模型或资源，没有生成视图树 | 补 `children: []` 或实际页面节点 |
| 移动端被默认生成 | 未明确移动端却使用了 mobile 模板 | 默认改回 `desktop`，仅明确 H5/移动端时使用 mobile |
