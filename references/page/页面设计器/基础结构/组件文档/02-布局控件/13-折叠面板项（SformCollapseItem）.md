---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 折叠面板项（SformCollapseItem）
sdoc-doc-id: 73d71a06-a8f6-4dff-b648-d97d067f6e28
---

# SformCollapseItem 折叠面板项

## 组件选择摘要

- 适用场景：折叠面板中的单个分组项。
- 优先使用：作为 SformCollapse 的子项承载一个可展开区域。
- 不建议用于：脱离 SformCollapse 单独使用。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| state | `'normal' \| 'hidden' \| 'readonly'` | - | 状态 |
| showArrow | `boolean` | - | 显示箭头按钮 |
| title | `string` | `''` | 标题 |
| tooltip | `string \| object` | `''` | 标题右侧的帮助提示内容 |
| tooltipMode | `'tooltip' \| 'text'` | `'tooltip'` | 帮助提示展示形式 |
| tooltipStatus | `'default' \| 'primary' \| 'success' \| 'warning' \| 'danger'` | `'default'` | 纯文本模式下的文字状态 |
| defaultActive | `boolean` | `true` | 默认展开 |

## 事件 (Events)

无
