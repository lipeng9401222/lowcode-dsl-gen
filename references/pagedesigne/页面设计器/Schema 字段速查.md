# Schema 字段速查

> 本文档从 `页面设计器/index.md` 拆出，包含 viewport/theme 配置、表达式系统、校验规则与常见错误速查表。

## viewport（视口）

```json
{
  "width": 390,
  "height": 844,
  "unit": "px",
  "device": "mobile"
}
```

`device` 取值：`mobile` / `desktop` / `tablet` / `embedded`

## theme（主题）

```json
{
  "background": "#FFFFFF",
  "textColor": "#111827",
  "fontFamily": "system"
}
```

仅放页面级**默认**视觉变量；具体组件样式在节点 `style` 中。

## 表达式系统

可在以下位置使用受限表达式：

- 字段规则：`fields.*.rules.required` / `submit` / `mask` / `validate[].when` / `validate[].expression`
- 视图规则：`ViewNode.visible`
- 动作：`steps[].when` / `assign` 右侧 / `params` / `body`

### 引用上下文

| 前缀 | 含义 |
|------|------|
| `model.*` | 业务数据模型 |
| `params.*` | 当前 action/页面入参 |
| `response.*` | 上一步响应 |
| `user.*` | 当前用户上下文 |
| `env.*` | 运行环境信息 |
| `meta.*` | 页面元信息 |

### 允许运算符

`==` `!=` `>` `>=` `<` `<=` `&&` `||` `!` `+` `-` `*` `/` `%`

### 允许函数

`empty()` / `notEmpty()` / `includes()` / `len()` / `sum()` / `concat()` / `today()` / `now()` / `state(path)`

### 禁止能力

赋值、循环、对象构造、原型访问、网络请求、动态函数调用、任意 JavaScript 执行。

## 校验规则（来自 Schema 规范）

| 校验项 | 校验方式 |
|-------|---------|
| `schemaVersion` 是 `core-1.0` | 字符串 |
| `kind` 是 `page` | 字符串 |
| `children` 是数组 | 类型 |
| 节点 `type` 是非空字符串 | 类型 |
| 节点 `events` 引用顶层 actions | 引用闭合 |
| `events` value 是 string 或 array of string | 类型 |
| `visible` 是布尔或受限表达式 | 类型 |
| `model` 引用能解析到 models 中字段 | 引用解析 |
| `textModel` 引用能解析到可写字段 | 引用解析 |
| 节点 `source` 引用存在的 resources | 引用 |
| `actions.steps[].use` 引用存在的 `resource.operation` | 引用 |
| `actions.steps[].run` 不形成循环 | 依赖图 |
| `actions.steps[].function.name` 引用已注册方法 | 注册表 |
| `assign` 左侧是可写引用 | 表达式 |
| 字段 rules 表达式通过白名单解析 | 表达式 |
| `state()` path 能解析到节点 id 或 `page.*` | 状态注册 |
| 同一页面 id 不重复 | 唯一性 |

## 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| 顶层 type 用 `"type": "page"`（应为 `"kind"`） | 加载失败 | 改为 `"kind": "page"` |
| 节点 events 直接写 step 数组 | schema 不识别 | 抽到顶层 `actions`，节点只引用 id |
| `model: "user.name"` 但 models 里没有 `user` | 解析失败 | 在 `models` 中声明 |
| 节点 `props.columns` 写 table 的列定义 | 协议不允许 | 把 `columns` 提到节点根（与 `props` 同级） |
| 表达式包含 JavaScript 语法 | 校验拦截 | 改用受限表达式（白名单运算符 + 函数） |
| `validate[].validator` 引用不存在的 action | 校验拦截 | 在 `actions` 中注册自定义校验 |
