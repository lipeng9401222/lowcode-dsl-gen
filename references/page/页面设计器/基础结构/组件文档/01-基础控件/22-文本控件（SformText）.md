---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 文本控件（SformText）
sdoc-doc-id: a71f1128-96ca-4475-876c-04d2f196a465
---

# SformText 文本控件

## 组件选择摘要

- 适用场景：只读文本展示、说明文字、详情页字段展示。
- 优先使用：内容只展示不编辑，或作为页面静态说明。
- 不建议用于：需要用户输入的文本字段。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| text | `string` | `'文本'` | 展示内容 |
| state | `'normal' \| 'hidden'` | `'normal'` | 状态 |
| foldForbidden | `boolean` | `false` | 禁止换行 |
| fontFamily | `string` | `'微软雅黑'` | 字体 |
| fontSize | `number` | `14` | 字号 |
| fontStyle | `string` | `'{}'` | 字体样式（JSON 字符串） |
| fontColor | `string` | `'#000000'` | 字体颜色 |
| textAlign | `string` | `'left'` | 对齐方式 |
| lineHeight | `number` | `22` | 行高 |
| labelText | `string` | `''` | 标签内容 |
| labelShow | `boolean` | `false` | 是否显示标签 |
| labelFontSize | `number` | `14` | 标签字号 |
| labelFontColor | `string` | `'#000000'` | 标签字体颜色 |
| labelLineHeight | `number` | `22` | 标签行高 |
| labelWidth | `string` | `'100px'` | 标签宽度 |
| backgroundColor | `string` | `''` | 背景色 |
| border | `string` | `'none'` | 边框样式 |
| borderRadius | `string` | `'0'` | 边框圆角 |
| boxmodel | `string` | `'{}'` | 盒模型（JSON 字符串） |
| labelTextAlign | `string` | `'left'` | 标签对齐方式 |
| flexDirection | `string` | `'row'` | 布局方向 |
| labelBoxModel | `string` | `'{}'` | 标签盒模型（JSON 字符串） |
| fontBoxModel | `string` | `'{}'` | 字体盒模型（JSON 字符串） |

## 事件 (Events)

无
