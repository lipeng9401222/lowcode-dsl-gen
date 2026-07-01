---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 折叠面板（SformCollapse）
sdoc-doc-id: 8c7450d7-6075-4a89-9b10-1ddfd5e05be0
---

# SformCollapse 折叠面板

## 组件选择摘要

- 适用场景：多个可展开/收起的信息分组。
- 优先使用：详情页或表单页按章节折叠展示。
- 不建议用于：业务页签切换，应使用 SformTabs。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_f2774045/sform-collapse.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| accordion | `boolean` | `false` | 手风琴模式 |
| showNav | `boolean` | `false` | 显示导航栏 |
| showIndex | `boolean` | `false` | 显示序号 |
| navAffix | `boolean` | `true` | 导航栏是否开启固钉 |
| headerPrefix | `'none' \| 'block'` | `'block'` | 标题前色块 |
| arrowType | `'text' \| 'icon'` | `'text'` | 箭头类型 |
| showArrow | `boolean` | `true` | 显示箭头按钮 |
| size | `'default' \| 'small' \| 'large'` | `'default'` | 尺寸 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `activeNames: string \| number \| null \| (string \| number \| null)[]` | 当前激活的面板变化时触发 |
