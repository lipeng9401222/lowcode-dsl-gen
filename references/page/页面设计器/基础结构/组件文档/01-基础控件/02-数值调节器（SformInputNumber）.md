---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 数值调节器（SformInputNumber）
sdoc-doc-id: dc69579f-49e5-4429-9a07-634b91f1e383
---

# SformInputNumber 数值调节器

## 组件选择摘要

- 适用场景：数量、金额、排序号、百分比、分值等数字录入。
- 优先使用：需要数值校验、步进调整、最小值最大值限制的字段。
- 不建议用于：纯文本编号、带复杂格式的金额展示、枚举选择。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782268688146_98935289/sform-input-number.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `''` | 提示语 |
| min | `number` | `0` | 最小值 |
| max | `number` | `100` | 最大值 |
| step | `number` | `1` | 操作步长 |
| precision | `number` | `-1` | 数值精度（小数位数） |
| showControls | `boolean` | `true` | 显示按钮 |
| clearable | `boolean` | `false` | 可清空 |
| width | `string \| number` | `'100%'` | 宽度 |
| unit | `string` | `''` | 单位（显示在输入框后） |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: number \| undefined` | 绑定值被改变时触发 |
| focus | `event: FocusEvent` | 在组件 Input 获得焦点时触发 |
| blur | `event: FocusEvent` | 在组件 Input 失去焦点时触发 |
