---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 按钮（SformButton）
sdoc-doc-id: f0744bd6-0aba-4d46-b517-ffd2093dbb6c
---

# SformButton 按钮

## 组件选择摘要

- 适用场景：保存、提交、查询、重置、删除、新增等普通操作按钮。
- 优先使用：明确的单一操作命令。
- 不建议用于：多个折叠操作菜单，应使用 SformDropdown。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782264472505_6ce8a618/sform-button.png)

## 属性 (Props)

| 属性名     | 类型                                                              | 默认值     | 说明         |
| ---------- | ----------------------------------------------------------------- | ---------- | ------------ |
| state      | `'normal' \| 'hidden'`                                            | `'normal'` | 状态         |
| buttonText | `string`                                                          | `'按钮'`   | 按钮名称     |
| type       | `'' \| 'primary' \| 'success' \| 'warning' \| 'danger' \| 'info'` | `''`       | 按钮语义     |
| plain      | `boolean`                                                         | `false`    | 是否朴素按钮 |
| text       | `boolean`                                                         | `false`    | 是否文字按钮 |

## 事件 (Events)

| 事件名 | 参数 | 说明           |
| ------ | ---- | -------------- |
| click  | -    | 点击按钮时触发 |
