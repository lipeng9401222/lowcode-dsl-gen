---
sdoc-project: 低代码产品开发文档
sdoc-doc-name: 下拉按钮（SformDropdown）
sdoc-doc-id: acf16eb8-03db-4a65-abef-813c2fd84664
---

# SformDropdown 下拉按钮

## 组件选择摘要

- 适用场景：更多操作、批量操作、按钮下拉菜单。
- 优先使用：多个相关操作需要收纳在一个入口下。
- 不建议用于：单个高频主操作，应使用 SformButton。
- 读取建议：生成页面时先根据本摘要判断是否命中；命中后再继续读取下方属性、事件、方法和示例。

## 示例图

![](https://oa.epoint.com.cn/h5/fileattaches/20260624/1782269688772_d28e515c/sform-dropdown.png)

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| state | `'normal' \| 'hidden'` | `'normal'` | 状态 |
| buttonText | `string` | `'下拉按钮'` | 按钮名称 |
| buttonType | `'' \| 'primary' \| 'success' \| 'warning' \| 'danger' \| 'info'` | `''` | 按钮语义 |
| plain | `boolean` | `false` | 是否朴素按钮 |
| text | `boolean` | `false` | 是否文字按钮 |
| dropdownItems | `DropdownItem[]` | `()` | 下拉项配置 |

### DropdownItem 类型

| 属性名 | 类型 | 说明 |
|--------|------|------|
| label | `string` | 选项名称 |
| command | `string` | 命令值 |
| disabled | `boolean` | 是否禁用 |
| divided | `boolean` | 是否显示分割线 |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| command | `command: string` | 当单击下拉项时触发 |
