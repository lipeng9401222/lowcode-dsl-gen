# 页面设计器：pagedesigne yml

## 1. 资产定位与边界

`pagedesigne` 是统一作者态页面协议（Core Schema），用于描述页面结构、数据模型、外部资源、行为、规则和校验约束。**文件后缀使用 yml，内容仍为 Core Schema JSON 文本**。

> ⚠️ **格式说明**：虽然其他元数据都用 yml，但 `pagedesigne/` 目录下的新建文件统一用 `.pagedesigne.yml`（如 `xxx.pagedesigne.yml`）；内部仍写 Core Schema JSON 文本。

- 本资产解决：页面结构、数据模型、外部资源、行为、规则和校验约束的声明式描述
- 不在本资产范围内的事：

### 不在本 skill 范围内的事

  - **PC/小屏组件具体扩展属性**（columns 之外的根属性）：由具体运行态/物料包定义，本 skill 不枚举
  - **设计器内部 normalize/validate 逻辑实现**：属于设计器/平台职责
  - **复杂动画交互**：建议在线上设计器调整
  - **Vue SFC 页面手写**：属于高码资产，参考 `epoint-framework-dev`
- 与 metadata 目录的对应关系：`metadata/<apptag>/pagedesigne/`

## 2. 文档导航

> 列出本目录下所有平级子文档及一句话用途。供 LLM 与人类按需深读。

| 文档 | 用途 | 何时读 |
|------|------|--------|
| `Schema 字段速查.md` | Schema 字段定义速查表（viewport/theme/表达式/校验规则/常见错误） | 需要查阅具体字段定义时 |
| `视图模型速查.md` | 视图模型定义速查（models/children/ViewNode） | 需要查阅视图模型结构时 |
| `设计器 Schema 规范定义/` | 完整 Schema 规范（8 份子文档 + 示例） | 需要深入了解设计器 Schema 时 |

## 3. 生成与修改对话速查

### 文件位置与命名

```
<metadata>/pagedesigne/<页面名>.pagedesigne.yml
```

推荐命名：
- 业务页面：`采购立项列表.pagedesigne.yml`、`采购立项表单.pagedesigne.yml`
- 复用模板：`公共布局.pagedesigne.yml`

### 对话脚本（创建新页面 schema）

#### 第一步：基本信息

```
你要创建什么页面？
- 页面标题（中文，如 员工列表）：
- 页面 id（英文，可省略，自动生成）：
- 设备类型（默认 desktop；仅当用户明确说"移动端 / 小屏 / 手机端 / H5"等场景时切 mobile，其他显式提到时切 tablet/embedded；
  参考 `references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/sform/demo.md` 的 `viewport.device: desktop`）：
- 是列表页还是表单页？
```

> 💡 **device 字段建议作为可选项询问**：除非用户明确说移动端，否则默认 `desktop`，对话里**主动给出推荐值**而不是必填项，避免每次都打断流程。脚本侧 `add_pagedesigne.py --device` 已默认 `desktop`，与本约定一致。

#### 第二步：数据模型

```
列表页：
- 数据来源接口（URL）？
- 列表显示哪些字段？字段名 + 显示名 + 类型：
  例: name | 姓名 | string
      deptName | 部门 | string
- 有查询条件吗？查询字段：

表单页：
- 主对象名（如 employee）：
- 字段及校验：
  例: name | 姓名 | string | required
      email | 邮箱 | string | email format, required
- 提交接口 URL：
```

#### 第三步：交互

```
- 表格行点击进入详情？详情路由是？
- 是否有新增按钮？新增弹窗还是新页面？
- 是否要刷新/查询/导出按钮？
```

#### 第四步：创建计划 + 明确批准

按用户提供的信息先组装页面创建计划，列出页面类型、数据模型、主要交互和目标文件 `<metadata>/pagedesigne/<title>.pagedesigne.yml`。用户明确回复"批准创建"后，再生成 Core Schema JSON 文本并落盘校验。

### 快速生成脚本

优先使用 `scripts/add_pagedesigne.py` 创建常见页面 schema：

```bash
python scripts/add_pagedesigne.py \
  --metadata <metadata目录> \
  --type list \
  --title "采购立项列表" \
  --endpoint "/api/purchaseproject" \
  --fields-json '[{"name":"project_name","label":"项目名称","type":"string"}]' \
  --query-json '[{"name":"keyword","label":"关键词","type":"string"}]'
```

支持的页面类型：

| type | 用途 |
|------|------|
| `list` | 列表页，生成 search model、collection model、endpoint list action、table |
| `form` | 表单页，生成 record model、save action、form children |
| `detail` | 详情页，生成 record model、detail action、text 展示节点 |
| `custom` | 自定义骨架，适合先生成最小 schema 后手工补复杂结构 |

脚本会写入 `<metadata>/pagedesigne/<页面名>.pagedesigne.yml` 并调用 `validate_yml.py` 自检。复杂页面仍可用模板补充，但补完后必须跑：

```bash
python scripts/validate_yml.py <目标.pagedesigne.yml>
```

## 4. 与其他资产的引用关系

- 引用其他资产：resources 中可引用 endpoint（后端接口）、dictionary/tree（代码项/组织树）、workflow（工作流服务）
- 被其他资产引用：module 中的菜单路由指向 pagedesigne 页面
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs`

---

## 顶层结构（CorePageSchema）

```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "id": "employee-page",
  "title": "员工管理",
  "viewport": {
    "width": 390,
    "height": 844,
    "unit": "px",
    "device": "mobile"
  },
  "theme": {
    "background": "#FFFFFF",
    "textColor": "#111827",
    "fontFamily": "system"
  },
  "models": {},
  "resources": {},
  "actions": {},
  "events": {
    "load": "refreshEmployees"
  },
  "children": []
}
```

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `schemaVersion` | string | ✅ | 固定 `"core-1.0"` |
| `kind` | string | ✅ | 固定 `"page"` |
| `id` | string | ❌ | 页面稳定标识（缺省由 normalize 生成） |
| `title` | string | ✅ | 页面标题（中文） |
| `viewport` | object | ❌ | 设计器画布配置（详见 `Schema 字段速查.md`） |
| `theme` | object | ❌ | 页面级默认视觉变量（详见 `Schema 字段速查.md`） |
| `models` | object | ❌ | 页面数据模型（详见 `视图模型速查.md`） |
| `resources` | object | ❌ | 接口、字典、树、上传等外部依赖 |
| `actions` | object | ❌ | 行为注册表（接口调用、赋值、校验等） |
| `events` | object | ❌ | 页面级事件 → action 引用 |
| `children` | array | ✅ | 唯一视图节点树（详见 `视图模型速查.md`） |

## resources（外部资源）

声明页面依赖的外部能力。**只描述"有什么能力"**，不描述何时调用。

### 资源类型

| type | 用途 | 节点引用方式 |
|------|------|---------------|
| `endpoint` | 一组命名后端操作（list/save/delete） | action 中 `use: "xxx.list"` |
| `dictionary` | 平铺选项数据（下拉/单选/多选） | 节点 `source: "xxxOptions"` |
| `tree` | 层级数据（部门树/区划树） | 节点 `source: "xxxTree"` |
| `upload` | 文件/图片上传入口 | 节点 `source: "avatarUpload"` |
| `route` | 导航目标（页面/弹窗/链接） | action 中 `navigate: "xxxRoute"` |
| `workflow` | 工作流服务入口 | action 中 `workflow.use: "xxx.start"` |

### endpoint 示例

```json
{
  "employeeApi": {
    "type": "endpoint",
    "baseUrl": "/api/employees",
    "operations": {
      "list": { "method": "GET", "path": "" },
      "detail": { "method": "GET", "path": "/detail" },
      "save": { "method": "POST", "path": "" }
    }
  }
}
```

### dictionary（静态/远程）

```json
{
  "genderOptions": {
    "type": "dictionary",
    "source": "static",
    "options": [
      { "label": "男", "value": "M" },
      { "label": "女", "value": "F" }
    ]
  },
  "deptOptions": {
    "type": "dictionary",
    "source": "remote",
    "request": { "method": "GET", "url": "/api/departments" },
    "map": { "label": "name", "value": "id" }
  }
}
```

### tree

```json
{
  "deptTree": {
    "type": "tree",
    "request": { "method": "GET", "url": "/api/departments/tree" },
    "map": {
      "label": "name",
      "value": "id",
      "children": "children"
    }
  }
}
```

### upload

```json
{
  "avatarUpload": {
    "type": "upload",
    "request": { "method": "POST", "url": "/api/files/avatar" },
    "accept": ["image/png", "image/jpeg"],
    "maxSizeMb": 5,
    "map": { "url": "url", "id": "id", "name": "filename" }
  }
}
```

### route

```json
{
  "employeeDetailRoute": {
    "type": "route",
    "path": "/employees/detail",
    "params": { "id": "model.employee.id" }
  }
}
```

### workflow

```json
{
  "employeeWorkflow": {
    "type": "workflow",
    "processKey": "employee_onboarding",
    "operations": {
      "start": {
        "method": "POST",
        "path": "/start",
        "body": "model.employee"
      }
    }
  }
}
```

## actions（行为注册表）

```json
{
  "refreshEmployees": {
    "steps": [
      {
        "use": "employeeApi.list",
        "params": { "keyword": "model.search.keyword" },
        "assign": { "model.employeeList": "response.items" }
      }
    ],
    "onError": {
      "notify": "加载失败",
      "stop": true
    }
  }
}
```

### step 白名单

| step 操作 | 含义 |
|----------|------|
| `use` | 调用资源操作（如 `employeeApi.list`） |
| `assign` | 模型赋值 |
| `run` | 执行另一个 action |
| `validate` | 校验模型/字段/节点 |
| `reset` | 重置模型/字段 |
| `log` | 调试输出 |
| `notify` | 提示消息 |
| `open` | 打开弹窗/抽屉 |
| `close` | 关闭弹窗 |
| `confirm` | 二次确认 |
| `workflow` | 调用工作流资源 |
| `navigate` | 跳转路由 |
| `function` | 执行已注册的自定义 JS 方法 |

### step 条件 `when`

```json
{
  "when": "model.employee.type == 'external'",
  "assign": { "model.employee.vendorRequired": true }
}
```

## events（事件）

页面级 events 和节点 events **结构相同**：key 是事件名，value 是 action id 或 id 数组。

```json
{
  "events": {
    "load": "refreshEmployees",
    "beforeLeave": ["confirmDirty"]
  }
}
```

### 常见节点事件名约定

`init` / `change` / `click` / `submit` / `reset` / `open` / `close` / `pageChange` / `sortChange` / `selectionChange`

## 完整示例（最小可用列表页）

```json
{
  "schemaVersion": "core-1.0",
  "kind": "page",
  "id": "employee-list",
  "title": "员工列表",
  "viewport": { "width": 1440, "height": 900, "unit": "px", "device": "desktop" },
  "models": {
    "search": {
      "type": "record",
      "fields": {
        "keyword": { "type": "string", "label": "关键词" }
      }
    },
    "employeeList": {
      "type": "collection",
      "primaryKey": "id",
      "fields": {
        "id": { "type": "string" },
        "name": { "type": "string", "label": "姓名" },
        "deptName": { "type": "string", "label": "部门" }
      }
    }
  },
  "resources": {
    "employeeApi": {
      "type": "endpoint",
      "baseUrl": "/api/employees",
      "operations": {
        "list": { "method": "GET", "path": "" }
      }
    }
  },
  "actions": {
    "refreshEmployees": {
      "steps": [
        {
          "use": "employeeApi.list",
          "params": { "keyword": "model.search.keyword" },
          "assign": { "model.employeeList": "response.items" }
        }
      ]
    }
  },
  "events": {
    "load": "refreshEmployees"
  },
  "children": [
    {
      "type": "input",
      "model": "search.keyword",
      "props": { "label": "搜索" },
      "events": { "change": "refreshEmployees" }
    },
    {
      "type": "table",
      "model": "employeeList",
      "columns": [
        { "type": "field", "field": "name", "label": "姓名" },
        { "type": "field", "field": "deptName", "label": "部门" }
      ]
    }
  ]
}
```

## 参考实现示例

| 示例文件 | 用途 | 适用场景 |
|---------|------|---------|
| `references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/sform/demo.md` | PC 表单页（device=desktop） | **生成 PC 表单/详情页时优先参考**，含完整 models/resources/actions/children |
| `references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/smallscreen/demo.md` | 小屏页面（device=mobile） | 用户明确说移动端 / H5 / 手机端时参考 |

需要时让 LLM 现读现用，不要默认全文加载到上下文。

## 深度参考文档索引

复杂页面生成时按需加载以下子文档（不要一次全读）：

| 子文档 | 何时读 |
|--------|--------|
| `pagedesigne/页面设计器/设计器 Schema 规范定义/01-概览.md` | 需了解整体架构时 |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/02-页面 Schema.md` | 顶层字段细节 |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/03-视图树.md` | ViewNode 节点详细规范 |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/04-视图模型.md` | models 字段细节/rules |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/05-资源.md` | resources 各类型详细定义 |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/06-动作与事件.md` | actions/events 深度说明 |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/07-规则与表达式.md` | 表达式白名单详细 |
| `pagedesigne/页面设计器/设计器 Schema 规范定义/08-规范化与校验.md` | normalize/validate 规则 |
| `references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/sform/demo.md` | PC 表单页完整示例（desktop） |
| `references/pagedesigne/页面设计器/设计器 Schema 规范定义/示例/smallscreen/demo.md` | 小屏页面完整示例（mobile） |
