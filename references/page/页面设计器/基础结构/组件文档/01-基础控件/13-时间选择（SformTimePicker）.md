---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 时间选择（SformTimePicker）
sdoc-doc-id: fbd1380f-6cca-4b7b-8a68-e1cf1dcb4ed2
---

# SformTimePicker 时间选择

## 组件选择摘要

- 适用场景：时分秒、开始时间、结束时间等时间选择。
- 优先使用：只关心一天内的具体时间，不包含日期。
- 不建议用于：年月日、日期范围、日期时间组合字段。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688740_fcefe1ff/sform-time-picker.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `'请输入时间选择'` | 提示语 |
| format | `string` | `'HH:mm:ss'` | 时间格式 |
| editable | `boolean` | `false` | 允许输入 |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string` | 当用户确认值时触发 |
| focus | `event: FocusEvent` | 当输入框获得焦点时触发 |
| blur | `event: FocusEvent` | 当输入框失去焦点时触发 |
| visibleChange | `value: boolean` | 当时间选择器的下拉框显示/消失时触发 |
