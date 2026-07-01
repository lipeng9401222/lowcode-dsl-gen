---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 工作流右侧控件（SformWorkflowRight）
sdoc-doc-id: 5f020018-9842-450f-9949-eb13604de662
---

# SformWorkflowRight 工作流右侧控件

## 组件选择摘要

- 适用场景：工作流页面右侧审批辅助区域。
- 优先使用：流程审批页面需要右侧流程信息或辅助操作区域。
- 不建议用于：非流程页面的普通侧栏。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782268441213_01143035/sform-workflow-right.png)

## 属性 (Props)

该组件无自定义属性，数据通过 pageConfig.workflow 自动获取并合并默认字段。

### 默认字段

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| stepName | `string` | `''` | 步骤名称 |
| opinion | `string` | `''` | 签署意见 |
| isUseAiReview | `boolean` | `false` | 是否使用 AI 审查 |

## 事件 (Events)

无
