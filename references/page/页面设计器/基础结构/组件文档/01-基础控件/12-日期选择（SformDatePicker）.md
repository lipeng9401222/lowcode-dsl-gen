---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 日期选择（SformDatePicker）
sdoc-doc-id: da293fc2-0ac7-47f7-a7b7-87790c8f5188
---

# SformDatePicker 日期选择

## 组件选择摘要

- 适用场景：日期、日期时间、日期范围等时间点或区间选择。
- 优先使用：业务字段类型是日期、时间戳、开始结束日期。
- 不建议用于：仅时分秒选择，应使用 SformTimePicker。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782267222070_4d496ab8/sform-date-picker.png)

## 属性 (Props)

| 属性名           | 类型                                               | 默认值               | 说明                 |
| ---------------- | -------------------------------------------------- | -------------------- | -------------------- |
| modelValue       | `string`                                           | `''`                 | 关联字段双向绑定     |
| state            | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'`           | 状态                 |
| type             | `'date' \| 'daterange' \| 'month' \| 'monthrange'` | `'date'`             | 选择器类型           |
| placeholder      | `string`                                           | `'请输入日期'`       | 提示语               |
| startPlaceholder | `string`                                           | `'请输入开始日期'`   | 开始提示语           |
| endPlaceholder   | `string`                                           | `'请输入结束日期'`   | 结束提示语           |
| format           | `string`                                           | `'YYYY-MM-DD HH:mm'` | 日期格式（显示格式） |
| minDate          | `string`                                           | `''`                 | 开始日期             |
| maxDate          | `string`                                           | `''`                 | 结束日期             |
| editable         | `boolean`                                          | `false`              | 允许输入             |
| clearable        | `boolean`                                          | `true`               | 可清空               |
| width            | `string \| number`                                 | `'100%'`             | 宽度                 |
| tooltipPosition  | `string`                                           | `'none'`             | 提示位置             |
| tooltipContent   | `string`                                           | `''`                 | 提示内容             |

## 事件 (Events)

| 事件名        | 参数                | 说明                                   |
| ------------- | ------------------- | -------------------------------------- |
| change        | `value: string`     | 当用户确认值时触发                     |
| focus         | `event: FocusEvent` | 当输入框获得焦点时触发                 |
| blur          | `event: FocusEvent` | 当输入框失去焦点时触发                 |
| panelChange   | `value: string`     | 当导航按钮被点击时触发                 |
| visibleChange | `value: boolean`    | 当日期选择器的下拉菜单出现或消失时触发 |
