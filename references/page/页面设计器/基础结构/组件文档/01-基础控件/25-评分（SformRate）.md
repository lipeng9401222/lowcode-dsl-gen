---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 评分（SformRate）
sdoc-doc-id: ac3e29f1-85d3-4036-9c72-10c79cd2dbbc
---

# SformRate 评分

## 组件选择摘要

- 适用场景：满意度、星级、评分字段。
- 优先使用：业务值可用等级或星级表达。
- 不建议用于：普通数字录入或精确小数输入。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_170b6d5a/sform-rate.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `number` | `0` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态：必填、普通、只读、隐藏 |
| max | `number` | `5` | 最大评分分数 |
| size | `'large' \| 'default' \| 'small'` | `'default'` | 评分星星的尺寸 |
| allowHalf | `boolean` | `false` | 是否允许选择半星 |
| showText | `boolean` | `false` | 是否显示辅助文字 |
| showScore | `boolean` | `false` | 是否显示当前分数（与 showText 互斥） |
| clearable | `boolean` | `false` | 是否可以将值重置为 0 |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: number` | 当评分值更改时触发 |
