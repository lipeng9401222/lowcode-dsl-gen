---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 下拉选择（SformSelect）
sdoc-doc-id: 90f91a6b-edf8-4b50-a264-2493d331a772
---

# SformSelect 下拉选择

## 组件选择摘要

- 适用场景：固定枚举、字典项、状态、类型等下拉单选或多选。
- 优先使用：选项扁平、数量适中、无需层级关系的选择字段。
- 不建议用于：树形结构、级联层级、人员部门选择。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782270671677_8332a5ac/sform-select.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `'请选择'` | 提示文字 |
| clearable | `boolean` | `true` | 可清空 |
| multiple | `boolean` | `false` | 是否多选 |
| filterable | `boolean` | `false` | 可搜索 |
| width | `string \| number` | `'100%'` | 宽度 |
| codeItem | `string` | `''` | 代码项 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string \| number \| Array<string \| number>` | 当选定的值发生变化时触发 |
| visibleChange | `value: boolean` | 当下拉菜单出现/消失时触发 |
| removeTag | `value: string \| number` | 在多选模式下移除标签时触发 |
| clear | - | 在可清除的 Select 中点击清除图标时触发 |
| blur | `value: FocusEvent` | 当输入框失去焦点时触发 |
| focus | `value: FocusEvent` | 当输入框获得焦点时触发 |
