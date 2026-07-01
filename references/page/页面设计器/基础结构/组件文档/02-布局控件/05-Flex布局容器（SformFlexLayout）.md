---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: Flex布局容器（SformFlexLayout）
sdoc-doc-id: cade7347-8214-49cb-89d4-dd50f8fb54be
---

# SformFlexLayout Flex布局容器

## 组件选择摘要

- 适用场景：横向/纵向弹性排列、对齐、间距控制。
- 优先使用：按钮组、局部工具区、左右对齐区域。
- 不建议用于：严格表单栅格。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| contentClass | `string` | `''` | 样式类名 |
| flexWrap | `boolean` | `false` | 是否换行 |
| flexItemMinWidth | `string` | `'200px'` | flex 项最小宽度 |

## 事件 (Events)

无
