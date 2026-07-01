---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 人员选择器（SformPersonPicker）
sdoc-doc-id: 59dfcf53-0751-4b70-8f0f-1ead6f663704
---

# SformPersonPicker 人员选择器

## 组件选择摘要

- 适用场景：选择人员、负责人、经办人、联系人等人员字段。
- 优先使用：字段目标是用户/人员，通常需要单选或多选人员。
- 不建议用于：同时选择部门、组织机构或混合组织对象。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string \| string[]` | `()` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| url | `string` | `'/personalpickaction/getCommonData'` | 人员数据接口 |
| morePageUrl | `string` | `''` | 更多选择页面地址 |
| pickerTitle | `string` | `''` | 列表标题 |
| placeholder | `string` | `''` | 提示文字 |
| effect | `'light' \| 'dark' \| 'danger'` | `'light'` | 弹层主题 |
| clearable | `boolean` | `true` | 可清空 |
| cacheData | `PersonType[]` | `undefined` | 缓存人员数据 |
| collapseTags | `boolean` | `true` | 是否折叠标签 |
| maxCollapseTags | `number` | `3` | 最大折叠标签数 |
| showTagIcon | `boolean` | `true` | 是否显示头像 |
| multiple | `boolean` | `true` | 是否多选 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string \| string[]` | 当选定的值发生变化时触发 |
