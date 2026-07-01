---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 工作流按钮（SformWorkflowButton）
sdoc-doc-id: 58926594-5438-4860-8efe-f8f54dba8871
---

# SformWorkflowButton 工作流按钮

## 组件选择摘要

- 适用场景：工作流提交、审批、退回、流转类操作。
- 优先使用：页面接入流程引擎并需要流程动作按钮。
- 不建议用于：普通业务保存、查询、新增按钮。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782268441213_df7acefd/sform-workflow-button.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| saveAction | `string` | `''` | 保存动作路径 |
| submitAction | `string` | `''` | 提交动作路径 |
| formAction | `string` | `''` | 表单动作路径 |

## 事件 (Events)

无
