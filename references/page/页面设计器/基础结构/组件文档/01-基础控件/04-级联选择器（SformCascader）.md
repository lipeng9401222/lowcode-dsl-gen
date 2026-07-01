---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 级联选择器（SformCascader）
sdoc-doc-id: 8a60d156-082e-4818-ac32-a640951b17c4
---

# SformCascader 级联选择器

## 组件选择摘要

- 适用场景：省市区、分类层级、业务级联等逐级选择。
- 优先使用：选项存在明确父子层级，并且需要按层级逐级展开。
- 不建议用于：普通扁平枚举、独立树选择、人员组织选择。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `unknown` | `undefined` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `'请选择'` | 提示文字 |
| clearable | `boolean` | `true` | 可清空 |
| multiple | `boolean` | `false` | 是否多选 |
| filterable | `boolean` | `false` | 可搜索 |
| width | `string \| number` | `'100%'` | 宽度 |
| codeItem | `string` | `''` | 代码项 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |
| showAllLevels | `boolean` | `true` | 是否显示完整路径 |
| collapseTags | `boolean` | `false` | 是否折叠多选标签 |
| collapseTagsTooltip | `boolean` | `false` | 折叠标签是否显示提示 |
| separator | `string` | `' / '` | 层级分隔符 |
| checkStrictly | `boolean` | `false` | 任意级是否可选 |
| emitPath | `boolean` | `true` | 单选时是否返回完整路径 |
| lazyLoad | `boolean` | `false` | 是否按需加载数据 |
| expandTrigger | `'click' \| 'hover'` | `'click'` | 子节点展开方式 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: unknown` | 当绑定值变化时触发 |
| visibleChange | `value: boolean` | 当下拉框显示或隐藏时触发 |
| expandChange | `value: unknown` | 当展开选项变化时触发 |
| removeTag | `value: unknown` | 在多选模式下移除标签时触发 |
| clear | - | 点击清空图标时触发 |
| blur | `value: FocusEvent` | 当级联选择器失去焦点时触发 |
| focus | `value: FocusEvent` | 当级联选择器获得焦点时触发 |
