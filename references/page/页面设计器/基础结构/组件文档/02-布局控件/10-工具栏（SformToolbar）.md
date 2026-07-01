---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 工具栏（SformToolbar）
sdoc-doc-id: 4e61360f-4518-44f1-b9cb-f34cc20c64c9
---

# SformToolbar 工具栏

## 组件选择摘要

- 适用场景：页面操作区、表格按钮区、查询按钮区。
- 优先使用：承载新增、删除、导入、导出、查询等操作按钮。
- 不建议用于：具体按钮本身，应使用 SformButton 或 SformDropdown。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782270671677_675fca44/sform-toolbar.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| showTitleSlot | `boolean` | `false` | 是否显示标题 |
| showButtonSlot | `boolean` | `true` | 是否显示按钮区域 |
| showSearchSlot | `boolean` | `false` | 是否显示搜索区域 |
| showActionsSlot | `boolean` | `false` | 是否显示操作区域 |
| position | `'top' \| 'bottom'` | `'top'` | 工具栏位置 |
| buttonPosition | `string` | `'left'` | 按钮位置 |
| tableId | `string` | `''` | 关联表格id |
| filterAdvancedFixed | `'popover' \| 'top' \| 'right'` | `'popover'` | 搜索区域位置 |
| filterLayout | `boolean` | `true` | 显示布局 |
| filterOperation | `boolean` | `true` | 显示筛选条件 |
| filterExtend | `boolean` | `false` | 显示添加条件 |
| filterCommon | `boolean` | `false` | 显示常用筛选 |
| filterLogicPlan | `boolean` | `false` | 显示查询按钮筛选 |

## 事件 (Events)

无
