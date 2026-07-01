---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 选项卡（SformTabs）
sdoc-doc-id: d600e424-0ec4-4e99-96f1-66d6aa98facb
---

# SformTabs 选项卡

## 组件选择摘要

- 适用场景：多个业务页签之间切换。
- 优先使用：同一页面内存在并列分区，需要用标签页切换。
- 不建议用于：只需要展开收起的分组。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782270671677_34b5c78b/sform-tabs.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| size | `'default' \| 'small' \| 'large'` | `'default'` | 选项卡的尺寸 |
| type | `'' \| 'card' \| 'border-card' \| 'section'` | `''` | 选项卡的类型 |
| editable | `boolean` | `false` | 选项卡是否可添加和关闭 |
| tabPosition | `'top' \| 'right' \| 'bottom' \| 'left'` | `'top'` | 选项卡的位置 |
| stretch | `boolean` | `false` | 选项卡宽度是否自动适应其容器 |
| fullLayout | `boolean` | `false` | 选项卡内容高度是否撑满其容器 |
| headerTarget | `string` | `''` | 将 Tab 头部挂载到指定元素 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| tabClick | `pane: TabsPaneContext, ev: Event` | 点击选项卡时触发 |
| tabChange | `name: string \| number` | 当前激活的 tab 变更时触发 |
| tabRemove | `name: string \| number` | 点击选项卡移除按钮时触发 |
| tabAdd | - | 点击选项卡添加按钮时触发 |
| edit | `paneName: string \| number \| undefined, action: 'remove' \| 'add'` | 点击选项卡添加或移除按钮时触发 |
