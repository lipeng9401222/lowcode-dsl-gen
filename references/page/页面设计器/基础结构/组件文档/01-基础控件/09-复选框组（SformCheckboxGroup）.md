---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 复选框组（SformCheckboxGroup）
sdoc-doc-id: cb8b7b77-3c9f-499f-9fa4-0bcb79ad8d3f
---

# SformCheckboxGroup 复选框组

## 组件选择摘要

- 适用场景：一组候选项中允许选择多个。
- 优先使用：多选枚举、标签、适用范围等多个值字段。
- 不建议用于：单个布尔勾选项、单选枚举。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_9038cbf3/sform-checkbox-group.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| codeItem | `string` | `''` | 代码项 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: Array<string \| number \| boolean>` | 绑定值变化时触发 |
