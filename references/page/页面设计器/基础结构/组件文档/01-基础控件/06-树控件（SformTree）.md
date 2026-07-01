---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 树控件（SformTree）
sdoc-doc-id: bfc5861c-b547-4c3a-826e-855ec36d6608
---

# SformTree 树控件

## 组件选择摘要

- 适用场景：完整树结构展示、左侧树导航、树节点选择。
- 优先使用：需要常驻树面板、节点展开收起、树节点驱动右侧内容。
- 不建议用于：表单里的单个树形下拉字段。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688740_49cc0256/sform-tree.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'normal' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| codeItem | `string` | `''` | 代码项 |
| multiple | `boolean` | `false` | 是否多选 |
| onlyCheckLeaf | `boolean` | `false` | 只能勾选叶子节点 |
| checkStrictly | `boolean` | `false` | 严格模式，父子节点选中不再关联 |
| checkedStrategy | `'all' \| 'parent' \| 'child'` | `'all'` | 定制回填方式：all(全显示)、parent(只显示父)、child(只显示子) |
| draggable | `boolean` | `false` | 是否可以拖拽 |
| showFilter | `boolean` | `false` | 是否开启搜索功能 |
| filterPlaceholder | `string` | `''` | 过滤输入框的 placeholder |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| select | `value: (string \| number)[]` | 点击树节点时触发 |
| check | `value: (string \| number)[]` | 点击树节点复选框时触发 |
