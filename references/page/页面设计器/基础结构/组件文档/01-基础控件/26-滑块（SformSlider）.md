---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 滑块（SformSlider）
sdoc-doc-id: f64158d4-d87f-472a-a398-5bbce522b251
---

# SformSlider 滑块

## 组件选择摘要

- 适用场景：区间内拖动选择数值、进度、比例。
- 优先使用：用户通过拖动选择近似数值比手输更自然。
- 不建议用于：需要精确输入的金额、数量、编号。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688694_08187071/sform-slider.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `number` | `0` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态：必填、普通、只读、隐藏 |
| min | `number` | `0` | 最小值 |
| max | `number` | `100` | 最大值 |
| step | `number` | `1` | 步进大小 |
| showInput | `boolean` | `false` | 是否显示输入框 |
| showInputControls | `boolean` | `true` | 是否显示输入框的控制按钮 |
| size | `'large' \| 'default' \| 'small'` | `'default'` | 滑块包装器的尺寸 |
| inputSize | `'large' \| 'default' \| 'small'` | `'default'` | 输入框的尺寸 |
| showStops | `boolean` | `false` | 是否显示断点 |
| vertical | `boolean` | `false` | 是否垂直模式 |
| height | `string` | `''` | 滑块高度（垂直模式下生效，如 `200px`） |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: number` | 当值发生改变时触发（拖动滑块释放鼠标时触发） |
| input | `value: number` | 当数据发生更改时触发（滑动过程中实时发出） |
