---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 图片组件（SformImage）
sdoc-doc-id: 4893ea9d-9d0f-4d7c-95f4-fcd350507832
---

# SformImage 图片组件

## 组件选择摘要

- 适用场景：图片展示、预览、详情页图片呈现。
- 优先使用：只展示图片，不承担上传动作。
- 不建议用于：需要选择或上传图片。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| imageWidth | `string` | `''` | 图片宽度 |
| imageHeight | `string` | `''` | 图片高度 |
| horizontalOffset | `number` | `0` | 水平偏移量 |
| verticalOffset | `number` | `0` | 垂直偏移量 |
| opacity | `number` | `100` | 透明度 |
| url | `string` | `''` | 图片地址 |
| radius | `number` | `0` | 圆角 |
| displayType | `'default' \| 'percentage' \| 'full'` | `'default'` | 显示方式 |

## 事件 (Events)

无
