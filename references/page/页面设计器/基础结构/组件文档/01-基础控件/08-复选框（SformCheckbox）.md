---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 复选框（SformCheckbox）
sdoc-doc-id: 343fb7d2-73f9-4ed9-8f0d-aa055517f2dd
---

# SformCheckbox 复选框

## 组件选择摘要

- 适用场景：单个布尔勾选项，例如是否同意、是否启用。
- 优先使用：只有一个勾选项且值表达 true/false 或是否。
- 不建议用于：多个选项的多选，应使用 SformCheckboxGroup。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_ba93d857/sform-checkbox.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| label | `string` | `'复选框'` | 复选框文本 |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: boolean \| string \| number` | 绑定值被改变时触发 |
