---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 弹窗选择（SformButtonEdit）
sdoc-doc-id: 9a4f9c0a-f9f2-4cd5-9fbe-c72fa4276871
---

# SformButtonEdit 弹窗选择

## 组件选择摘要

- 适用场景：通过弹窗选择业务数据后回填字段。
- 优先使用：选择项目、合同、客户等需要列表弹窗检索的数据。
- 不建议用于：简单枚举、树形选择、人员组织选择。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 关联字段双向绑定 |
| state | `'required' \| 'normal' \| 'readonly' \| 'hidden'` | `'normal'` | 状态 |
| placeholder | `string` | `'请选择'` | 提示文字 |
| clearable | `boolean` | `true` | 可清空 |
| width | `string \| number` | `'100%'` | 宽度 |
| tooltipPosition | `string` | `'none'` | 提示位置 |
| tooltipContent | `string` | `''` | 提示内容 |
| dialogConfigGuid | `string` | `''` | 弹出框配置GUID |
| url | `string` | `''` | 打开地址 |
| pageName | `string` | `''` | 弹窗名称 |
| withValue | `any` | `undefined` | 带值配置 |
| urlParams | `any` | `()` | url参数 |
| openType | `'dialog' \| 'modal'` | `'dialog'` | 打开方式 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `value: string \| number` | 当选定的值发生变化时触发 |
