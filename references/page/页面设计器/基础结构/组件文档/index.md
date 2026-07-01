# 组件文档

这里归档页面设计器组件参考。每个控件单独维护一个文档，page 生成时先用本索引定位候选控件，再只读取命中的控件文件。

## 读取规则

- 不要一次性读取所有组件详情。
- 先读本索引，按字段类型或页面结构定位候选控件。
- 命中具体控件后，只读取对应控件文件中的“组件选择摘要”和后续属性、事件、方法、示例。
- 存在组件歧义时，最多读取 2 到 3 个候选控件文件进行比较。

## 基础控件

| 控件 | 适用场景 |
| --- | --- |
| [文本框（SformInput）](01-基础控件/01-文本框（SformInput）.md) | 普通文本、名称、编码、备注、说明、长文本等字段录入 |
| [数值调节器（SformInputNumber）](01-基础控件/02-数值调节器（SformInputNumber）.md) | 数量、金额、排序号、百分比、分值等数字录入 |
| [下拉选择（SformSelect）](01-基础控件/03-下拉选择（SformSelect）.md) | 固定枚举、字典项、状态、类型等下拉选择 |
| [级联选择器（SformCascader）](01-基础控件/04-级联选择器（SformCascader）.md) | 省市区、分类层级、业务级联等逐级选择 |
| [选择树（SformTreeSelect）](01-基础控件/05-选择树（SformTreeSelect）.md) | 部门、区域、分类等树形数据的下拉选择 |
| [树控件（SformTree）](01-基础控件/06-树控件（SformTree）.md) | 完整树结构展示、左侧树导航、树节点选择 |
| [锚点导航（SformAnchor）](01-基础控件/07-锚点导航（SformAnchor）.md) | 长页面分区导航、表单章节快速定位 |
| [复选框（SformCheckbox）](01-基础控件/08-复选框（SformCheckbox）.md) | 单个布尔勾选项 |
| [复选框组（SformCheckboxGroup）](01-基础控件/09-复选框组（SformCheckboxGroup）.md) | 一组候选项中允许选择多个 |
| [单选框组（SformRadioGroup）](01-基础控件/10-单选框组（SformRadioGroup）.md) | 一组候选项中只能选择一个 |
| [开关（SformSwitch）](01-基础控件/11-开关（SformSwitch）.md) | 启用/停用、是/否、开/关等即时状态切换 |
| [日期选择（SformDatePicker）](01-基础控件/12-日期选择（SformDatePicker）.md) | 日期、日期时间、日期范围等时间点或区间选择 |
| [时间选择（SformTimePicker）](01-基础控件/13-时间选择（SformTimePicker）.md) | 时分秒、开始时间、结束时间等时间选择 |
| [人员选择器（SformPersonPicker）](01-基础控件/14-人员选择器（SformPersonPicker）.md) | 选择人员、负责人、经办人、联系人等人员字段 |
| [人员部门选择（SformOrganizationSelect）](01-基础控件/15-人员部门选择（SformOrganizationSelect）.md) | 选择人员、部门、组织机构等组织对象 |
| [弹窗选择（SformButtonEdit）](01-基础控件/16-弹窗选择（SformButtonEdit）.md) | 通过弹窗选择业务数据后回填字段 |
| [按钮（SformButton）](01-基础控件/17-按钮（SformButton）.md) | 保存、提交、查询、重置、删除、新增等普通操作按钮 |
| [下拉按钮（SformDropdown）](01-基础控件/18-下拉按钮（SformDropdown）.md) | 更多操作、批量操作、按钮下拉菜单 |
| [上传控件（SformFileUpload）](01-基础控件/19-上传控件（SformFileUpload）.md) | 附件、文档、压缩包等通用文件上传 |
| [图片上传（SformImageUpload）](01-基础控件/20-图片上传（SformImageUpload）.md) | 图片上传、头像、证照、图片材料 |
| [富文本编辑器（SformEditorWrapper）](01-基础控件/21-富文本编辑器（SformEditorWrapper）.md) | 富文本内容编辑、公告正文、说明正文 |
| [文本控件（SformText）](01-基础控件/22-文本控件（SformText）.md) | 只读文本展示、说明文字、详情页字段展示 |
| [图片组件（SformImage）](01-基础控件/23-图片组件（SformImage）.md) | 图片展示、预览、详情页图片呈现 |
| [分割线（SformLine）](01-基础控件/24-分割线（SformLine）.md) | 视觉分隔、表单区域分组、内容间隔 |
| [评分（SformRate）](01-基础控件/25-评分（SformRate）.md) | 满意度、星级、评分字段 |
| [滑块（SformSlider）](01-基础控件/26-滑块（SformSlider）.md) | 区间内拖动选择数值、进度、比例 |
| [工作流按钮（SformWorkflowButton）](01-基础控件/27-工作流按钮（SformWorkflowButton）.md) | 工作流提交、审批、退回、流转类操作 |
| [工作流历史组件（SformWorkflowHistory）](01-基础控件/28-工作流历史组件（SformWorkflowHistory）.md) | 展示流程审批历史、流转记录 |
| [工作流右侧控件（SformWorkflowRight）](01-基础控件/29-工作流右侧控件（SformWorkflowRight）.md) | 工作流页面右侧审批辅助区域 |

## 布局控件

| 控件 | 适用场景 |
| --- | --- |
| [布局管理器（SformLayoutManager）](02-布局控件/01-布局管理器（SformLayoutManager）.md) | 页面顶层布局管理和整体区域组织 |
| [表单布局（SformFormLayout）](02-布局控件/02-表单布局（SformFormLayout）.md) | 表单主体布局，承载多个表单项 |
| [表单项（SformFormItem）](02-布局控件/03-表单项（SformFormItem）.md) | 单个字段的 label、校验状态和控件包裹 |
| [栅格布局（SformGridLayout）](02-布局控件/04-栅格布局（SformGridLayout）.md) | 多列栅格、规则列宽、字段按列排布 |
| [Flex布局容器（SformFlexLayout）](02-布局控件/05-Flex布局容器（SformFlexLayout）.md) | 横向/纵向弹性排列、对齐、间距控制 |
| [容器（SformDiv）](02-布局控件/06-容器（SformDiv）.md) | 普通区域包裹、局部容器 |
| [选项卡（SformTabs）](02-布局控件/07-选项卡（SformTabs）.md) | 多个业务页签之间切换 |
| [选项卡面板（SformTabPane）](02-布局控件/08-选项卡面板（SformTabPane）.md) | 选项卡中的单个页签面板 |
| [折叠面板（SformCollapse）](02-布局控件/09-折叠面板（SformCollapse）.md) | 多个可展开/收起的信息分组 |
| [工具栏（SformToolbar）](02-布局控件/10-工具栏（SformToolbar）.md) | 页面操作区、表格按钮区、查询按钮区 |
| [表格（SformTable）](02-布局控件/11-表格（SformTable）.md) | 数据列表、子表、可编辑表格、弹窗编辑表格 |
| [滚动条（SformScrollbar）](02-布局控件/12-滚动条（SformScrollbar）.md) | 内容区域过长，需要独立滚动 |
| [折叠面板项（SformCollapseItem）](02-布局控件/13-折叠面板项（SformCollapseItem）.md) | 折叠面板中的单个分组项 |
