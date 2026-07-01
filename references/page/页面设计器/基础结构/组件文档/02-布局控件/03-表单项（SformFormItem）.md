---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 表单项（SformFormItem）
sdoc-doc-id: 41f901e0-9e53-4255-a3f5-f27f099bb5df
---

# SformFormItem 表单项

## 组件选择摘要

- 适用场景：单个字段的 label、校验状态和控件包裹。
- 优先使用：表单中的每一个字段项。
- 不建议用于：页面整体表单布局或纯容器。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| label | `string` | `'表单项'` | 标签文本 |
| labelPosition | `'left' \| 'right'` | `'right'` | 标签位置 |
| labelTooltip | `string` | `''` | 表单项 label 区域的帮助提示文本 |
| span | `number` | `24` | 栅格占用的列数（基于 24 栅格） |

## 事件 (Events)

无
