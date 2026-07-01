---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 人员部门选择（SformOrganizationSelect）
sdoc-doc-id: 20dc9754-2bcb-4783-9854-604986a82e24
---

# SformOrganizationSelect 人员部门选择

## 组件选择摘要

- 适用场景：选择人员、部门、组织机构等组织对象。
- 优先使用：字段可能包含部门、组织或人员部门混合选择。
- 不建议用于：纯人员字段且不涉及组织，应优先考虑 SformPersonPicker。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782267013367_53fbd1e6/sform-organization-select.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `'请选择'` | 提示文字 |
| clearable | `boolean` | `true` | 可清空 |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |
| interactive | `'dropdown' \| 'dialog'` | `'dropdown'` | 交互形式 |
| mode | `'people' \| 'dept'` | `'people'` | 模式：人员/部门 |
| multiple | `boolean` | `false` | 是否多选 |
| range | `'company' \| 'department' \| 'all'` | `'company'` | 选择范围 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string \| number` | 当选定的值发生变化时触发 |
