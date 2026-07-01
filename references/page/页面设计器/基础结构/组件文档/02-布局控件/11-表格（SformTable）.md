---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 表格（SformTable）
sdoc-doc-id: 98886e77-0c07-4cde-a0f1-a417a0007ac3
---

# SformTable 表格

## 组件选择摘要

- 适用场景：数据列表、子表、可编辑表格、弹窗编辑表格。
- 优先使用：需要行列数据、分页、选择列、序号列或表格方法。
- 不建议用于：普通表单字段展示或简单文本列表。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782268688146_d63efbe8/sform-table.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| modelValue | `string` | `''` | 绑定模型 |
| idField | `string` | `'rowguid'` | 主键 |
| tableType | `'cell' \| 'dialog'` | `'cell'` | 表格形式：cell-表内编辑，dialog-弹窗编辑 |
| showIndexColumn | `boolean` | `true` | 是否显示序号列 |
| defaultShowIndex | `boolean` | `true` | 选择列合并序号列 |
| showSelectionColumn | `boolean` | `true` | 是否显示多选列 |
| checkType | `'checkbox' \| 'radio'` | `'checkbox'` | 选择列类型 |
| pageSize | `number` | `10` | 每页条数 |
| pageSizeType | `'system' \| 'custom' \| 'personal'` | `'custom'` | 分页方式 |
| frozenLeft | `number` | `0` | 左侧冻结列数 |
| frozenRight | `number` | `0` | 右侧冻结列数 |
| borderStyle | `'none' \| 'horizontal' \| 'full'` | `'none'` | 边框样式：none-无，full-全边框，horizontal-仅水平边框 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| change | `pagination: { current: number, pageSize: number, total: number }` | 分页变化时触发 |

## 暴露的方法 (Exposed Methods)

| 方法名 | 参数 | 说明 |
|--------|------|------|
| add | `item?: ViewNode` | 新增 |
| save | - | 保存修改数据 |
| batchAdd | `opt: { dialogConfigGuid, url, pageName, pageWidth, pageHeight }` | 批量添加 |
| refresh | - | 刷新表格数据 |
| deleteSelectionRows | `item?: ViewNode` | 删除选中行 |
| getSelectionRows | - | 获取选中的行数据 |
| addRows | `rows: any[]` | 批量新增行 |
| updateViewState | `state: Record<string, any>` | 更新视图状态 |
| dataGrid | - | 获取表格实例 |
| viewState | - | 获取视图状态 |
