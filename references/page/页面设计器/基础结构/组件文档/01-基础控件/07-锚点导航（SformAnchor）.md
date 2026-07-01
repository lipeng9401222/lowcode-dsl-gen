---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 锚点导航（SformAnchor）
sdoc-doc-id: 831cdacd-c562-4124-bcff-1fb10b961248
---

# SformAnchor 锚点导航

## 组件选择摘要

- 适用场景：长页面分区导航、表单章节快速定位。
- 优先使用：页面存在多个区域，用户需要点击锚点跳转。
- 不建议用于：普通菜单、页签切换、折叠分组。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782266882686_0e46dc6d/sform-anchor.png)

## 属性 (Props)

| 属性名       | 类型                   | 默认值          | 说明                                              |
| ------------ | ---------------------- | --------------- | ------------------------------------------------- |
| className    | `string`               | `''`            | 自定义类名                                        |
| state        | `'normal' \| 'hidden'` | `'normal'`      | 状态                                              |
| target       | `string`               | `''`            | 生成锚点的目标容器 CSS 选择器，为空则默认扫描文档 |
| scrollTarget | `string`               | `''`            | 绑定 scroll 事件的滚动容器 CSS 选择器             |
| tags         | `string`               | `'h2,h3,h4,h5'` | 需要扫描的 HTML 标签，逗号分隔                    |
| type         | `'text' \| 'module'`   | `'text'`        | 显示类型                                          |
| layout       | `'left' \| 'right'`    | `'right'`       | 布局方向                                          |
| collapsible  | `boolean`              | `false`         | 是否开启折叠功能                                  |
| affix        | `boolean`              | `true`          | 是否开启固钉模式                                  |
| showBtn      | `boolean`              | `true`          | 是否显示类型切换按钮                              |
| offset       | `number`               | `0`             | 锚点滚动偏移距离                                  |
| affixOffset  | `number`               | `0`             | 固钉偏移距离                                      |
| maxWidth     | `number`               | `150`           | 导航栏最大宽度                                    |

## 事件 (Events)

| 事件名       | 参数                                   | 说明               |
| ------------ | -------------------------------------- | ------------------ |
| activeChange | `newValue: unknown, oldValue: unknown` | 导航切换后触发     |
| handleClick  | `value: unknown`                       | 点击导航后触发     |
| typeChange   | `type: string`                         | 导航类型切换后触发 |
