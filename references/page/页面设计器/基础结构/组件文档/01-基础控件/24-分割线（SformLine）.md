---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 分割线（SformLine）
sdoc-doc-id: 111079e5-1ca8-4b14-bf36-e99206657d76
---

# SformLine 分割线

## 组件选择摘要

- 适用场景：视觉分隔、表单区域分组、内容间隔。
- 优先使用：需要简单分隔线表达区块边界。
- 不建议用于：复杂分组展开收起，应使用折叠面板布局控件。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| tooltipPosition | `string` | `'top'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |
| width | `string \| number` | `'100%'` | 宽度 |
| state | `'normal' \| 'hidden'` | `'normal'` | 状态 |
| direction | `'horizontal' \| 'vertical'` | `'horizontal'` | 方向 |
| length | `string \| number` | `'100%'` | 长度 |
| thickness | `string \| number` | `'1px'` | 粗细 |
| color | `string` | `'#e5e7eb'` | 颜色 |
| margin | `string` | `'0px'` | 外边距 |
| padding | `string` | `'0px'` | 内边距 |

## 事件 (Events)

无
