---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 选择树（SformTreeSelect）
sdoc-doc-id: 41ab00ed-8f4e-4d63-bea4-7da59f0e1103
---

# SformTreeSelect 选择树

## 组件选择摘要

- 适用场景：部门、区域、分类等树形数据的下拉选择。
- 优先使用：字段本身需要选择树节点，但不需要完整树面板常驻展示。
- 不建议用于：扁平枚举、级联路径选择、完整树控件展示。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688740_db376405/sform-tree-select.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `'请选择'` | 提示文字 |
| clearable | `boolean` | `true` | 可清空 |
| filterable | `boolean` | `false` | 可搜索 |
| width | `string \| number` | `'100%'` | 宽度 |
| codeItem | `string` | `''` | 代码项 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |
| multiple | `boolean` | `false` | 是否多选 |
| onlyCheckLeaf | `boolean` | `false` | 只能勾选叶子节点 |
| lazyLoad | `boolean` | `false` | 数据按需加载 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string \| number` | 当选定的值发生变化时触发 |
| visibleChange | `value: boolean` | 当下拉菜单出现/消失时触发 |
| removeTag | `value: string \| number` | 在多选模式下移除标签时触发 |
| clear | - | 在可清除的 TreeSelect 中点击清除图标时触发 |
| blur | `value: FocusEvent` | 当输入框失去焦点时触发 |
| focus | `value: FocusEvent` | 当输入框获得焦点时触发 |
| select | `value: (string \| number)[]` | 点击树节点时触发 |
| check | `value: (string \| number)[]` | 点击树节点复选框时触发 |
