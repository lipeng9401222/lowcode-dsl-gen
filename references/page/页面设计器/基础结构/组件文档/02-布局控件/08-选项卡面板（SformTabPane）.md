---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 选项卡面板（SformTabPane）
sdoc-doc-id: 476d2246-6931-4be0-a753-bb39d290cc56
---

# SformTabPane 选项卡面板

## 组件选择摘要

- 适用场景：选项卡中的单个页签面板。
- 优先使用：作为 SformTabs 的子项承载某个页签内容。
- 不建议用于：脱离 SformTabs 单独使用。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| label | `string` | `''` | 选项卡的标题 |
| closable | `boolean` | `false` | 选项卡是否可关闭 |
| lazy | `boolean` | `false` | 选项卡是否懒加载 |
| url | `string` | `''` | iframe 路径地址 |
| state | `'normal' \| 'hidden' \| 'readonly'` | `'normal'` | 状态 |
| defaultActive | `boolean` | `false` | 默认激活 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| load | `evt: Event, pane: TabsPaneContext` | iframe 加载完成后触发 |
