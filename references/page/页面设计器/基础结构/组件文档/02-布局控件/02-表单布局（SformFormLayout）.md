---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 表单布局（SformFormLayout）
sdoc-doc-id: 67b6e9ba-2959-4cdf-9787-0f640d78ef04
---

# SformFormLayout 表单布局

## 组件选择摘要

- 适用场景：表单主体布局，承载多个表单项。
- 优先使用：新增、编辑、详情、查询条件等表单区域。
- 不建议用于：单个字段项本身，应使用 SformFormItem。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782270671677_a50121f4/sform-form-layout.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| gutter | `number` | `0` | 栅格间距（单位 px） |
| itemSpan | `number` | `24` | 默认列宽（基于 24 栅格） |

## 事件 (Events)

无
