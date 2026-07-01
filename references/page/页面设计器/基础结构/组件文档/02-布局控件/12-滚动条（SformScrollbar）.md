---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 滚动条（SformScrollbar）
sdoc-doc-id: d4deb7c4-b3b0-409e-b595-ba95faa45de3
---

# SformScrollbar 滚动条

## 组件选择摘要

- 适用场景：内容区域过长，需要独立滚动。
- 优先使用：局部容器滚动，而不是整个页面滚动。
- 不建议用于：内容不溢出的普通容器。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| height | `string` | `''` | 容器高度，如 400px、100% 等 |
| maxHeight | `string` | `''` | 最大高度 |
| always | `boolean` | `false` | 滚动条是否一直显示 |
| visible | `boolean` | `true` | 是否显示滚动条 |
| noresize | `boolean` | `false` | 不响应容器尺寸变化 |
| wrapClass | `string` | `''` | 包裹容器的自定义类名 |
| viewClass | `string` | `''` | 视图的自定义类名 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| scroll | `event: { scrollTop: number, scrollLeft: number }` | 触发滚动事件时返回滚动的距离 |
