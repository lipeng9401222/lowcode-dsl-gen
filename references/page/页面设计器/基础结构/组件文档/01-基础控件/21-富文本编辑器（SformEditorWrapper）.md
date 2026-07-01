---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 富文本编辑器（SformEditorWrapper）
sdoc-doc-id: 9794a7c0-bb09-4f24-b984-4c7248ff9a60
---

# SformEditorWrapper 富文本编辑器

## 组件选择摘要

- 适用场景：富文本内容编辑、公告正文、说明正文。
- 优先使用：需要加粗、图片、段落、格式化内容的长文本。
- 不建议用于：普通备注或纯文本输入。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| height | `number` | `272` | 编辑器高度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

无
