---
name: lowcode-gen-page
description: Epoint 低代码页面设计器原子生成器。根据 lowcode-dsl-gen IR 的 `pagedesigne` 资产生成或修改 `page/*.json`，处理页面标题、`pagetag`、`device`、`pageType`、模型、字段、查询条件、组件映射、页面引用和 JSON 校验。用于列表页、表单页、详情页、工作流办理页的页面设计器生成；默认使用桌面端，只有用户明确要求移动端、H5 或小屏时才使用 `mobile`。
---

# lowcode-gen-page

只处理 `assets[type=pagedesigne]`。

## 输入

```yaml
spec:
  title: "采购立项列表"
  pagetag: "purchaseproject_list"
  device: "desktop"
  pageType: "list"
  endpoint: "/api/purchaseproject"
  fields: []
  query: []
  layout:
    toolbar:
      position: "top"
      buttonPosition: "left"
      buttons:
        - { kind: "submit" }
        - { kind: "save" }
    sections:
      - title: "基本信息"
        layout:
          itemSpan: 12
        fields:
          - { name: "projectname", span: 24 }
```

## 必读资料

按这个顺序读，除非当前任务明显不需要：

1. `../../references/page/页面设计器/index.md`
2. `../../references/page/页面设计器/生成与校验/index.md`
3. `../../references/page/页面设计器/基础结构/index.md`
4. `../../references/page/页面设计器/基础结构/组件与字段对照.md`
5. 按页面类型选择：
   - 列表页：先读真实 JSON 样例 `../../references/page/设计器 Schema 规范定义/project_list.json`、`../../references/page/设计器 Schema 规范定义/task_list.json`，再读说明性文档 `../../references/page/页面设计器/场景示例/列表示例.md`
   - 表单/详情/工作流表单页：先读真实 JSON 样例 `../../references/page/设计器 Schema 规范定义/project_form.json`、`../../references/page/设计器 Schema 规范定义/task_form.json`，再读说明性文档 `../../references/page/页面设计器/场景示例/表单示例.md`
6. 只有在结构或校验被卡住时，再读：
   - `../../references/page/设计器 Schema 规范定义/index.md`
   - `../../references/page/设计器 Schema 规范定义/08-规范化与校验.md`
   - `../../references/page/页面设计器/检查清单/index.md`
   - `../../references/page/页面设计器/常见错误/index.md`

## Grill Gate 追问门禁

生成前必须确认以下关键事实，未确认的不得用模型猜测静默补齐。

### 必问事实

| 事实 | 说明 | 禁止猜测 |
|-----|------|---------|
| `title` 页面标题 | 中文标题 | ❌ |
| `pagetag` 页面标签 | 英文标识，需与 MIS 表名对齐 | ❌ |
| `pageType` 页面类型 | list / form / detail / workflow-form | ❌ |
| `fields` 字段列表 | 需要展示/编辑的字段 | ❌ |

### 可推断 / 安全默认

| 事实 | 来源 | 默认值 |
|-----|------|-------|
| `device` | 默认桌面端 | `desktop`（`safe_default`） |
| `endpoint` | 从 apptag/tableName 推断 | `repo_inferred` |
| 页面 `id` | 自动生成 | `safe_default` |

### 可选追问（影响生成但有安全默认）

- `device`：只有用户明确要求移动端/H5/小屏时才切到 `mobile`
- `layout`：表单页的分组结构、栅格布局
- `query`：列表页的查询条件字段
- 按钮/操作列：默认标准 CRUD 按钮，特殊交互需确认

### 禁止猜测

- **字段-组件映射**：不得仅按字段类型套控件，必须先看字段语义和设计稿
- **pagetag**：影响路由和引用关系，不得臆造
- **页面结构**：有设计稿/截图时必须先还原可见结构，不得直接用默认模板代替

### 确认矩阵

| 确认项 | 必须 | 说明 |
|-------|------|------|
| 页面标题和 pagetag | ✅ | 关键身份标识 |
| 页面类型 | ✅ | 决定页面骨架 |
| 字段列表 | ✅ | 核心展示/编辑内容 |
| 设计稿元素→组件映射 | 有设计稿时 ✅ | 精确还原 UI |
| 查询条件 | 列表页 ✅ | 搜索功能 |
| 布局分组 | 表单页建议 ✅ | 表单结构 |

## 执行步骤

1. 核对输入：`title`、`pagetag`、`device`、`pageType`、`endpoint`、`fields`、`query`、`layout`、跨资产引用。
2. 默认保持 `device=desktop`；只有用户明确要求移动端、H5 或小屏时才切到 `mobile`。
3. 先从设计稿、截图、原型、PRD 页面说明或运行端 mock 抽取页面 layout spec，再决定是否调用 `add_page.py`。只要存在可见 UI 依据，就必须先还原可见结构和交互意图，不得直接用 MIS 字段或默认模板代替。
4. 写入或更新 `.lowcode-plans/<apptag>/page/<asset-id>-plan.md`，至少记录：
   - 输入 IR 摘要
   - 关键事实来源
   - 页面结构计划
   - 设计稿/需求元素 -> 组件库组件 -> JSON 落点的映射表
   - 试运行命令与结果
   - 校验命令与结果
5. 先定页面骨架，再定字段控件：
   - `list`：优先对齐真实 JSON 的 `list-container -> toolbar + table`
   - `form/detail/workflow-form`：优先对齐真实 JSON 的 `layout-manager -> slots.main -> collapse -> collapse-item -> form-layout -> form-item -> control`
6. 组件选型以 `组件与字段对照.md` 和组件文档为准：
   - 先看字段语义，不只看字段类型
   - 先判断设计稿元素属于哪个组件族，再生成 JSON 节点
   - 显式 `widget/component/editor` 优先
   - 自动推断只作为默认回退
7. 审批通过后调用 `../../scripts/add_page.py`；当设计稿或组件库要求的结构无法由默认参数表达时，必须通过 `layout-json`、`initial-json` 或后处理补齐，不得交付退化模板。
8. 必须运行 `../../scripts/validate_json.py <target-file>`。

## 高优先级规则

### 硬规则

- 页面生成优先级固定为：设计稿/截图/原型/运行端 mock > PRD 页面说明 > 现有真实 JSON 样例 > MIS 字段 > 默认模板。只要存在可见 UI 依据，就禁止仅按数据模型字段生成页面。
- 有设计稿或截图时必须先输出 layout spec；layout spec 未覆盖可见结构、关键交互、组件选择、数据绑定和打开方式时，不得进入落盘。
- 页面 JSON 默认落盘为 `page/<pagetag>.json`；`pagetag`、文件名、模型 `alias`、`models[*].sqlTableName` 默认优先与关联 `mis.tableName` 对齐。
- 顶层 `id` 是稳定 schema 标识；列表页通常不需要顶层 `pageId`。
- 表单/详情运行时目标必须使用真实 `pageId`。没有设计器导出值时，不要手工预留或编造，省略 `--page-id` 让 `add_page.py` 生成；列表页按钮再读取配套表单 JSON 的最终 `pageId`。
- 标准新增、编辑、详情默认复用同一个表单页和同一个 `pageId`，由设计器当前约定的运行模式区分编辑和只读详情；只有需求明确要求独立详情布局时，才单独规划详情页。
- 页面字段必须分层：MIS 字段是数据模型字段，不等同于页面展示字段；表单/详情页优先使用 `layout.sections[].fields`，未提供时才回退到 `fields`。
- 页面中的按钮、查询、选择、表格、表单分组、弹窗、树、上传、分页、状态展示、链接和行内操作都以设计稿/PRD 为准；默认模板只能用于需求未说明的部分。
- 设计稿出现组件库中已有的结构或控件时，必须映射到对应组件，不得退化为普通 input、普通文本或默认 CRUD。
- 设计稿出现示例数据时，应使用 `initial-json` / `initial-json-file` 或模型 initial 记录预览数据；不要让空数据页掩盖页面结构是否还原。

### 生成原则

- 真实设计器 JSON 是结构基线，Markdown 示例是说明材料。参考真实 JSON 时只复用节点层级、slot 位置、模型绑定形态和常用 props，不复制业务字段、标题、模型名、页面 id 或节点 id。
- 页面结构优先还原需求文档、设计稿、截图、现有 JSON 或运行端 mock；未出现且需求未说明的结构不要主动添加，除非它是当前功能必要交互。
- 先定页面骨架，再按字段语义和组件库选控件。显式 `widget/component/editor` 优先；自动推断只是回退，不要只按字段类型套控件。
- 组件库映射必须可审计：子计划中为每个关键设计稿元素记录“设计稿元素 / 组件库组件 / page JSON type+componentName / JSON 落点”。不要只写“按组件库生成”。
- 表单布局按 24 栅格表达设计稿。同一行字段的 `span` 总和应凑满 24，具体比例按视觉宽度、字段内容长短和控件类型确定；没有明确宽度差异时再按字段数量均分。
- 行内控件默认撑满当前 `form-item`；列表列、选择列、序号列、操作列、分组表头等都按表格强结构生成，不降级塞进普通节点 `props`。

### 回退与边界

- 信息不足时才使用默认模板：列表页回退到标准列表骨架；表单页回退到单个 `collapse-item + form-layout.itemSpan=12`。
- 需求没有出现选择列、序号列、操作列或系统字段时不要主动添加；如果交互必需但列结构未说明，使用默认形态并在生成说明中标注为默认推断。
- 模型绑定使用表达式单元，具体字段绑定、组件 props、分组列、操作列、mock/initial 数据等实现细节按 references 和 `add_page.py` 支持能力处理。

## 边界

- 不要为标准 CRUD 页面主动生成 `event`。
- 不要在这里生成 `workflow` 资产；这里只消费或引用相关 `pagetag` / URL。
- 节点事件只能引用顶层 `actions`，不要把动作步骤内联到节点。
- 页面外部依赖声明在顶层 `resources`；节点只通过 `source` 或 action step 引用。
- 没有需求文档、没有设计稿、信息不足时，再回退到默认模板，不要反过来。
