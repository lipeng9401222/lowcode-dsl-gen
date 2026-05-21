# 页面 Schema

页面 Schema 的 TypeScript 对应类型为 `CorePageSchema`。它定义页面级元信息、顶层注册区和唯一视图树。

## 结构

```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "id": "employee-page",
  "title": "员工管理",
  "viewport": {
    "width": 390,
    "height": 844,
    "unit": "px",
    "device": "mobile"
  },
  "theme": {
    "background": "#FFFFFF",
    "textColor": "#111827",
    "fontFamily": "system"
  },
  "models": {},
  "resources": {},
  "actions": {},
  "events": {
    "load": "refreshEmployees"
  },
  "children": []
}
```

## 字段

- `schemaVersion`：协议版本，固定为 `core-1.0`。
- `kind`：Schema 类型，当前固定为 `page`。
- `id`：页面稳定标识。AI 可省略，由 normalizer 生成。
- `title`：页面标题。
- `viewport`：设计器画布配置，服务小屏、PC、平板、嵌入式画布等场景。
- `theme`：页面级默认视觉变量。
- `models`：页面数据结构，仅包含 `record` 和 `collection` 两类业务数据模型。
- `resources`：接口、字典、树、上传、路由、工作流等外部依赖声明。
- `actions`：接口调用、赋值、校验、弹窗、提示、工作流、导航等行为注册表。
- `events`：页面级事件到顶层 `actions` 的引用，结构与节点 `events` 相同。
- `children`：唯一页面节点树。

## viewport

```json
{
  "width": 390,
  "height": 844,
  "unit": "px",
  "device": "mobile"
}
```

- `width` 和 `height` 是设计器画布建议尺寸。
- `unit` 当前支持 `px`。
- `device` 可为 `mobile`、`desktop`、`tablet`、`embedded`。

## theme

```json
{
  "background": "#FFFFFF",
  "textColor": "#111827",
  "fontFamily": "system"
}
```

`theme` 表达页面级默认视觉变量。组件专属样式应放在节点 `style` 中，最终 CSS 映射由渲染器决定。

## events

页面级 `events` 与节点 `events` 同构：key 为事件名（不强制枚举，运行时可扩展），value 为顶层 `actions` 的 id 或 id 数组。

```json
{
  "events": {
    "load": "refreshEmployees",
    "beforeLeave": ["confirmDirty"]
  }
}
```
