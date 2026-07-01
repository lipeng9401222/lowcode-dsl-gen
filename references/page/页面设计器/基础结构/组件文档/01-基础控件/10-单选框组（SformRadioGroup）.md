---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 单选框组（SformRadioGroup）
sdoc-doc-id: f2edba7b-bcce-4308-a60f-023f27429b5d
---

# SformRadioGroup 单选框组

## 组件选择摘要

- 适用场景：一组候选项中只能选择一个。
- 优先使用：选项数量较少且适合平铺展示的单选枚举。
- 不建议用于：选项很多的单选，通常使用 SformSelect 更合适。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_84b960a4/sform-radio-group.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| width | `string \| number` | `'100%'` | 宽度 |
| codeItem | `string` | `''` | 代码项 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string \| number \| boolean` | 绑定值变化时触发 |
