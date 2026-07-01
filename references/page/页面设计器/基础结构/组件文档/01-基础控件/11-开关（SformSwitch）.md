---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 开关（SformSwitch）
sdoc-doc-id: 980e87a2-088a-483d-9746-ed2f0797b65e
---

# SformSwitch 开关

## 组件选择摘要

- 适用场景：启用/停用、是/否、开/关等即时状态切换。
- 优先使用：二值状态字段，且界面语义适合开关。
- 不建议用于：需要明确勾选确认的协议类字段。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688740_294bc11e/sform-switch.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| activeText | `string` | `''` | 开启时的描述文字 |
| inactiveText | `string` | `''` | 关闭时的描述文字 |
| activeValue | `boolean \| string \| number` | `true` | 开启时的值 |
| inactiveValue | `boolean \| string \| number` | `false` | 关闭时的值 |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: boolean \| string \| number` | 绑定值被改变时触发 |
