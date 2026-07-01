---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 文本框（SformInput）
sdoc-doc-id: 9d78361c-4996-4b7e-8e9a-7be73153bd4b
---

# SformInput 文本框

## 组件选择摘要

- 适用场景：普通文本、名称、编码、备注、说明、长文本等字段录入。
- 优先使用：字符串字段、单行文本、多行文本 textarea。
- 不建议用于：数字精度、固定枚举、日期时间、人员组织等专用字段。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782264685634_4edff5a5/sform-input.png)

## 属性 (Props)

| 属性名          | 类型                                               | 默认值     | 说明                         |
| --------------- | -------------------------------------------------- | ---------- | ---------------------------- |
| modelValue      | `string`                                           | `''`       | 关联字段双向绑定             |
| state           | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态：必填、普通、只读、隐藏 |
| type            | `'text' \| 'textarea'`                             | `'text'`   | 类型：文本框或文本域         |
| placeholder     | `string`                                           | `''`       | 提示语                       |
| maxlength       | `number`                                           | `50`       | 字数限制                     |
| showWordLimit   | `boolean`                                          | `false`    | 是否显示计数器               |
| rows            | `number`                                           | `2`        | 输入框行数（仅 textarea）    |
| autosize        | `boolean`                                          | `false`    | 文本域自适应高度             |
| width           | `string \| number`                                 | `'100%'`   | 宽度                         |
| unit            | `string`                                           | `''`       | 单位（显示在文本框后）       |
| tooltipPosition | `string`                                           | `'none'`   | 提示位置                     |
| tooltipContent  | `string`                                           | `''`       | 提示内容                     |

## 事件 (Events)

| 事件名 | 参数                      | 说明                                        |
| ------ | ------------------------- | ------------------------------------------- |
| change | `value: string \| number` | modelValue 改变时触发（失去焦点或按 Enter） |
| focus  | `value: FocusEvent`       | 输入框获得焦点时触发                        |
| blur   | `value: FocusEvent`       | 输入框失去焦点时触发                        |
| clear  | -                         | 点击清空按钮时触发                          |
| input  | `value: string \| number` | Input 值改变时触发                          |
