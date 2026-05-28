# 通用约定与默认值

本文档汇总所有跨组件类型的通用约定：默认值、命名规则、字段格式、校验规则。**遇到任何不确定的字段格式问题，先查这里**。

## 字段填充准则速查（避免幻觉）

写任何 yml 字段前，先核对以下 5 条：

1. **`type:` 标识必填**（appinfo/appref 除外）：第一行写正确的 `type` 值，详见下文「type 标识总表」。
2. **GUID/UUID 字段**：用 `python -c "import uuid; print(uuid.uuid4())"` 或脚本生成，**LLM 不要凭空编**。详见下文「GUID/UUID 字段」。
3. **时间戳字段**：格式 `YYYY-MM-DD HH:MM:SS`，从当前日期取；动作流 `app` 节点的 `created_at` 是 Unix 秒级整数。详见下文「时间戳字段」。
4. **枚举值**：见各 `references/<asset>/<中文目录>/index.md` 文档表格，**不能新造**；常见枚举（`isUse`、`mustfill`、`type` 等）在下文有总表。
5. **文件命名**：新建资产统一使用 `名字.类型.yml`；mis 表名无下划线；pagedesigne 后缀为 `.pagedesigne.yml`。详见 `references/directory-structure.md` 的「文件命名规则」节。

> 不确定时**先查本文档对应小节，再查对应 `references/<asset>/<中文目录>/index.md`，最后才问用户**。绝不凭直觉造字段。

## 默认值表（来自本工程现有实例）

| 字段 | 出现位置 | 默认值 | 说明 |
|------|---------|--------|------|
| `developerstag` | `appinfo.lowcode.yml` | `epoint` | 开发商，几乎不变 |
| `kitid` | `appinfo.lowcode.yml` | `businessprocess` | 套件标识，多套件时填全路径如 `frame.user` |
| `baseouguid` | `appinfo.lowcode.yml` | 空 | 独立单位默认不填；需要 `epoint` 或其他值时必须由用户明确提出或脚本显式传入 |
| `tenantguid` | 各 yml | 空字符串 `""` 或省略 | 多租户场景才用 |
| `extendappsource` | `appinfo.lowcode.yml` | 空 | 一般为空 |
| `organappsource` | `appinfo.lowcode.yml` | 空 | 一般为空 |

> **说明**：历史应用可能存在 `baseouguid: epoint`，但新建应用默认不再沿用该值。

## 字段类型与格式规范

### GUID/UUID 字段

所有 `xxxGuid`、`rowGuid`、`processGuid`、`activityGuid`、`transitionGuid`、`materialGuid` 等字段：

- **格式**：标准 UUIDv4，例如 `a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d`
- **生成方式**：用 `python -c "import uuid; print(uuid.uuid4())"` 或脚本生成；**LLM 不要瞎编**
- **特殊**：流程版本标识可以用语义化前缀，如 `V1-PROCESS-VERSION-GUID-0001`，但生产环境推荐 UUID

### 时间戳字段

- **格式**：`YYYY-MM-DD HH:MM:SS` 例如 `2026-04-08 00:00:00`
- **`createDate`/`updateDate`**：取生成 yml 时的当前时间
- **`created_at` (动作流 app 节点)**：Unix 秒级时间戳整数，例如 `1776765978`

### 字符串字段的引号

- **包含中文/特殊字符的值**：必须加双引号 `"采购立项"`
- **纯数字 ID 但是字符串语义的**：必须加双引号 `"95440001"`（避免被解析成数字）
- **简单英文/枚举值**：可以不加引号 `epoint`、`businessprocess`、`mobile`
- **有冒号、井号、引号、换行的字符串**：必须加双引号并对内部字符做 yml 转义

### 数字字段

- **整数**：直接写 `0`、`100`、`-1`
- **布尔标记**（如 `isVue: 0/1`、`isUse: 0/1`）：用 `0` 表否、`10` 或 `1` 表是；**详见各组件文档枚举说明**
- **浮点数**：如 `timeLimit: -1.0`，保留小数点

### 数组字段

- **空数组**：写 `[]`，不要写 `null` 或省略
- **行内短数组**：`name: [行政区划, 审核状态]`
- **块状数组**：

  ```yaml
  items:
    - codetext: 草稿
      codevalue: "0"
    - codetext: 待审核
      codevalue: "1"
  ```

## type 标识总表（极重要）

每类 yml **第一行必须是** `type: <标识>`（appinfo/appref 例外）。这是渲染器二次校验依据，写错就完全不识别。

| 文件类型 | 第一行 type 值 | 备注 |
|---------|---------------|------|
| `appinfo.lowcode.yml` | （无 type） | 直接以 `developerstag:` 开头 |
| `appref.lowcode.yml` | （无 type） | 直接是数组 |
| `*.codeitem.yml` | `type: codeitem` | |
| `*.mis.yml` | `type: mis` | |
| `*.module.yml` | `type: module` | |
| `*.event.yml` | `type: event` | 文档原话 `type: code(组件标识)` 是泛指占位写法，实际取值视组件类型 |
| `*.workflow.yml` | `type: workflow` | |
| `*.pagedesigne.yml` | `"kind": "page"` + `"schemaVersion": "core-1.0"` | 文件后缀是 yml，内容仍为 Core Schema JSON 文本，字段叫 `kind` 不是 `type` |
| `*.api.yml` | `type: api` | 较少手写，多由 Java 注解扫描生成 |

> **历史包袱说明**：文档 `01-vue方案.md` 给的示例 `type: code(组件标识)` 是泛指占位写法（“code” = “标识”）。具体到实际值，codeitem 类 yml 的 `type` 字段取值就是 `codeitem`；其它各类用对应实例标识（mis/module/workflow/event）。本工程下早期存在的 `审核状态.codeitem.yml`、`会议类型.codeitem.yml` 等反面样本写为 `type: code`，属于历史遗留，应逐步让它们统一到 `type: codeitem`。

## 命名规则（apptag、表名、字段名等）

### apptag（应用标识）

- 全局唯一
- 全小写英文 + 数字
- 不能有短横线、下划线、点号
- 不超过 32 字符
- 推荐：业务名直译，如 `purchaseproject`、`xmlx`、`bidding`

### MIS 表名 / 字段名

- 表名、`name`、`tableName`：全小写英文 + 数字，首字符字母，**不能有下划线**，如 `customerinfo`
- 字段名：全小写英文 + 数字，可保留下划线，如 `customer_name`
- 表名不带项目前缀（不要 `epoint_xxx`），用业务语义如 `customerinfo`
- 字段名简短有意义：`customer_name` 而不是 `customer_full_name_value`
- 主键统一叫 `rowguid`（NVarchar(50) 存 UUID）或 `id`

### 代码项名称（codeitem name）

- 推荐用中文名（设计器/UI 直接展示），如 `审核状态`、`类型`
- 文件名与 yml 内 `name:` 字段保持一致

### 模块名称（module name）

- 推荐中文，如 `主体管理`、`采购立项`
- 含 `code` 字段是 4-8 位数字字符串，逐级编码

### 工作流名称（processName）

- 推荐 `XXX审核流程`、`XXX审批流程` 这类完整描述

## 表名引用一致性

数据表/字段被其他地方引用时，必须**完全一致**：

| 引用点 | 引用值要求 |
|-------|-----------|
| `mis.yml` 的 `tableName` | 与文件名（去扩展名）的英文部分一致 |
| `appref.lowcode.yml` 引用 mis | `name: [<tableName>]` 用 mis 的 `tableName` 值 |
| `event.yml` 中 biz-action 引用上下文 Java 类 | 完整类全限定名，如 `com.epoint.ztb.rest.qy.tradeplan.purchaseproject.context.PurchaseProjectContext` |
| `workflow.yml` 中 `materialGuid` | 与 `WorkflowPvMaterial.materialGuid` 完全一致 |

## 国际化与字符编码

- 所有 yml 文件用 **UTF-8 (无 BOM)** 编码
- 中文字段、中文文件名都允许
- 文件**结尾必须有换行符**（POSIX 规范）

## YAML 风格规范

- **缩进**：用 **2 空格**，不要用 tab
- **数组**：`- ` 后接一个空格，缩进两格
- **注释**：`# ` 后空一格再写中文，便于阅读
- **空字段**：值是空字符串时写 `""`，不要写 `null`（设计器更友好）

### 标准模板（所有 yml 通用风格）

```yaml
# 固定标识
type: codeitem
# 代码名称
name: 审核状态
# 代码说明
description: 审核状态字典
# 代码子项列表
items:
  - codetext: 草稿
    codevalue: "0"
    ordernumber: 5
```

## 引用关系（appref.lowcode.yml）

引用其他应用的资产，使用 `engineguid` + `name` 数组。`engineguid` 取值：

| engineguid 值 | 引用什么 |
|--------------|---------|
| `codeitem` | 代码项 |
| `mis` | 数据表/数据模型 |
| `module` | 模块 |
| `event` | 动作流 |
| `workflow` | 工作流 |
| `pagedesigne` | 页面 |

详见 `references/appref/引用配置/index.md`。

## 校验规则速查（验证 yml 是否合法）

### 应用级校验

- [ ] `appinfo.lowcode.yml` 存在
- [ ] `apptag` 字段值与目录名一致
- [ ] `developerstag` 字段值与目录第一层一致
- [ ] 所有引用的资产实际存在

### 文件级校验

- [ ] 第一行是正确的 `type:` 值（appinfo/appref 除外）
- [ ] 所有 GUID 是合法 UUIDv4
- [ ] 所有时间戳格式正确
- [ ] 所有引用关系（如 mis 字段引用 codeitem 名称）实际存在
- [ ] 没有未在白名单内的字段名

### 字段级校验

- [ ] 必填字段不能为空
- [ ] 枚举值必须在合法集合内
- [ ] `mustfill: true` 的字段必须有 `defaultvalue` 或在 UI 上提示

> **自动校验**：调用 `python scripts/validate_yml.py <文件或目录>`，会输出详细错误清单。

## 重复声明区（避免高频疑问）

| 疑问 | 答案 |
|-----|-----|
| `type: code` 还是 `type: codeitem`？ | **`type: codeitem`**。 |
| `kitid` 必填吗？ | 组件内有多个套件时必填；单套件可以省略（fallback 当前组件套件） |
| `baseouguid` 应该用什么值？ | 新建默认填空；只有用户明确要求独立单位时才填 `epoint` 或其他值 |
| 文件用单扩展 `.yml` 还是双扩展 `.codeitem.yml`？ | 新建强制双扩展 `名字.类型.yml`；单扩展只兼容历史文件 |
| 在 yml 里写注释吗？ | 推荐写！会被插件保留，便于人和 AI 阅读 |
| 字符串什么时候加引号？ | 含中文/特殊字符/纯数字字符串语义时必须加；纯英文枚举值可省略 |

## references 命名约定

本节显式声明 `references/` 目录的命名规则，作为后续新增文档的强制约束。

1. **英文资产目录小写**：主资产的一级目录名采用全小写英文（`appinfo` / `appref` / `codeitem` / `mis` / `module` / `event` / `workflow` / `pagedesigne`），且与应用根目录下 8 类资产子目录名严格一致。
2. **中文业务子目录**：主资产的二级目录名采用中文业务名（如 `动作流`、`工作流`、`代码项`、`数据模型`、`模块`、`页面设计器`、`应用配置`、`引用配置`），禁止使用版本号、英文缩写或拼音。
3. **index.md 必备**：每个中文业务子目录下必须有 `index.md` 作为入口文档。
4. **长度阈值 600 行**：`index.md` 篇幅控制在 600 行以内；超出部分拆到平级子文档。`appinfo` 和 `appref` 为例外，允许超过。
