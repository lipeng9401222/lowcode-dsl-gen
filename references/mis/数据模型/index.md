# 数据表/数据模型：mis yml

## 1. 资产定位与边界

`mis` 是低代码体系里的"**数据表 + 数据模型**"二合一描述：既描述底层 SQL 表结构，又描述对应模型的字段元信息（用于表单渲染、列表渲染、查询条件等）。

- 与 应用根目录的对应关系：`<apptag>/mis/<表名>.mis.yml`（历史 `<表名>.yml` 仅兼容读取）
- 不在本资产范围内的事：
  - 字典枚举值的定义属于 `codeitem`，详见 `references/codeitem/代码项/index.md`
  - 业务流程审批属于 `workflow`（通过 `tableid` 反向引用 mis 表），详见 `references/workflow/工作流/index.md`
  - 页面布局/表单 UI 属于 `pagedesigne`/`event`，详见各自资产文档

## 2. 文档导航

> 本资产的所有内容均承载于本 index.md（R6.3 例外为 appinfo/appref；其他资产若超 600 行需拆出平级文档）。
> 章节速查：
> - § 文件位置与命名：见下文「[文件位置与命名](#文件位置与命名)」
> - § 完整字段表（顶层 / fields 30+ 属性 / type 枚举 / fielddisplaytype 枚举 / relations）：见下文「[完整字段表](#完整字段表)」
> - § 标准示例：见下文「[标准示例（来自文档完整结构）](#标准示例来自文档完整结构)」
> - § 字段填充策略（必问 / 偏好 / 模板默认）：见下文「[字段填充策略（避免每个字段都问-30-个属性）](#字段填充策略避免每个字段都问-30-个属性)」
> - § 校验规则与常见错误：见下文「[校验规则](#校验规则)」「[常见错误](#常见错误)」

## 3. 生成与修改对话速查

> 详细对话脚本与脚本调用：见下文「[对话脚本（创建新-mis-表）](#对话脚本创建新-mis-表)」「[修改已有-mis-表](#修改已有-mis-表)」「[快速生成脚本](#快速生成脚本)」与脚本 cheatsheet `references/directory-structure.md`。

## 4. 与其他资产的引用关系

- 引用其他资产：
  - 字段属性 `datasourceCodename` 引用 `codeitem` 的 `name`（如 `审核状态`）
  - `relations.targetmodel` 引用同应用内的其他 `mis.tableName`
- 被其他资产引用：
  - `workflow` 的 `workflowPvMisTableSet.tableid` 反向关联 mis 表
  - `event`/`pagedesigne` 通过 `tableid` 或表名引用 mis（数据源/表单）
  - 跨应用引用通过 `appref` 的 `engineguid: mis` 暴露
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs <app-root>`

---

`mis` 是低代码体系里的"数据表 + 数据模型"二合一描述：既描述底层 SQL 表结构，又描述对应模型的字段元信息（用于表单渲染、列表渲染、查询条件等）。

## 文件位置与命名

```
<app-root>/mis/<表名>.mis.yml
```

- 文件名必须使用**英文表名**（如 `customerinfo.mis.yml`），英文表名小写英文数字且不能有下划线
- yml 内 `tableName` 字段是**真正的 SQL 表名**，必须与文件名英文部分一致

## 完整字段表

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定 `mis` |
| `name` | string | ✅ | 模型名称（一般与 tableName 相同） |
| `description` | string | ❌ | 模型描述（中文） |
| `tableName` | string | ✅ | SQL 表名（小写英文数字，无下划线） |
| `fields` | array | ✅ | 字段列表 |
| `relations` | array | ❌ | 关联关系列表 |

### fields 子项字段（每个字段 30+ 属性）

#### 必备核心属性

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 字段名（英文 + 下划线） |
| `type` | string | ✅ | 字段数据类型；见下方枚举 |
| `description` | string | ✅ | 描述（中文，作为显示名） |
| `length` | int | ✅ | 字段长度 |
| `notnull` | bool | ❌ | 是否非空 |
| `mustfill` | bool | ❌ | 是否必填（UI 校验） |
| `defaultvalue` | string | ❌ | 默认值 |

#### type 枚举（数据库字段类型）

| type 值 | 含义 | 长度 | 默认 fielddisplaytype |
|---------|------|------|----------------------|
| `nvarchar` | 字符串型 | 50/200/500/1000 | `textbox` |
| `Integer` 或 `int` | 整数型 | 4 | `spinner` |
| `Numeric` | 双精度浮点型 | 18,2 | `spinner` |
| `DateTime` 或 `datetime` | 日期型 | — | `datepicker` |
| `ntext` | 大文本型 | — | `textarea` |
| `Image` | 二进制型 | — | `webuploader` |

#### `fielddisplaytype` 枚举（UI 控件类型）

| 值 | 控件 |
|---|------|
| `textbox` | 文本输入框（默认） |
| `combobox` | 下拉列表 |
| `datagrid` | 表格控件 |
| `radiobuttonlist` | 单选按钮组 |
| `checkbox` | 复选框 |
| `spinner` | 数字微调 |
| `datepicker` | 日期控件 |
| `ouradiotree` | 部门单选树 |
| `ouchecktree` | 部门多选树 |
| `userradiotree` | 部门用户单选树 |
| `userchecktree` | 部门用户多选树 |
| `webuploader` | 文件上传 |
| `webeditor` | ewebeditor |
| `textarea` | 多行文本 |
| `dropdownradiotree` | 下拉单选树 |
| `dropdownchecktree` | 下拉多选树 |
| `fckeditor` | 富文本编辑器 |
| `checkboxlist` | 复选框组 |

#### 框架字段（业务语义）

| 字段 | 类型 | 说明 |
|------|------|------|
| `isframeou` | bool | 是否是部门字段 |
| `isframeuser` | bool | 是否是用户字段 |
| `isforeignkey` | bool | 是否主键 |
| `autoincrease` | bool | 是否自增 |
| `uniquefield` | bool | 是否唯一 |
| `iscustom` | bool | 是否自定义字段 |

#### 字典/代码项绑定

| 字段 | 类型 | 说明 |
|------|------|------|
| `datasourceCodename` | string | 绑定代码项名称（如 `审核状态`） |

#### 数字相关属性

| 字段 | 类型 | 说明 |
|------|------|------|
| `precision` | int | 数字精度（小数位数） |
| `fieldjd` | int | 字段精度（数据库层面） |
| `fieldnumtype` | int | 字段数字类型 |
| `ismillisecond` | bool | 是否毫秒级（DateTime 字段） |
| `frameMj` | int | 框架敏感度（脱敏等级） |

#### UI 显示控制属性

| 字段 | 类型 | 说明 |
|------|------|------|
| `controlwidth` | int | 控件宽度 |
| `ordernumingrid` | int | 在表格中的列顺序 |
| `dispfielddesc` | bool | 是否显示字段描述 |
| `fielddesc` | string | 字段描述（额外说明文字） |
| `todispingrid` | bool | 是否在表格中显示 |
| `isquerycondition` | bool | 是否作为查询条件 |
| `isorderfield` | bool | 是否排序字段 |
| `orderdirection` | string | 排序方向 `asc`/`desc` |
| `isexportexcel` | bool | 是否参与 Excel 导出 |
| `gridmultirows` | bool | 表格多行展示 |
| `gridwidth` | int | 表格列宽度 |
| `dispInadd` | bool | 新增表单中是否显示 |
| `originalType` | string | 原始字段类型（导入时记录） |

### relations 关联关系

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 关联名称 |
| `currentmodel` | string | ✅ | 当前表 |
| `currentfield` | string | ✅ | 当前字段 |
| `targetmodel` | string | ✅ | 目标表 |
| `targetfield` | string | ✅ | 目标字段 |
| `type` | int | ✅ | 关联类型：`0`=一对一，`1`=一对多 |

## 标准示例（来自文档完整结构）

```yaml
# 固定标识
type: mis
# 模型名称
name: customerinfo
# 描述
description: 客户基础信息表，存储客户核心档案数据
# 表名
tableName: customerinfo
# 字段列表
fields:
    # 字段名
  - name: customer_name
    # 类型
    type: nvarchar
    # 描述 显示名称
    description: 客户姓名
    # 长度
    length: 50
    # 代码项绑定
    datasourceCodename: ""
    # 字段显示类型
    fielddisplaytype: textbox
    # 是否是部门字段
    isframeou: false
    # 是否是用户字段
    isframeuser: false
    # 是否主键
    isforeignkey: false
    # 是否自增字段
    autoincrease: false
    # 是否必填字段
    mustfill: false
    # 字段默认值
    defaultvalue: ""
    # 是否唯一字段
    uniquefield: false
    # 是否非空字段
    notnull: true
    fieldjd: 2
    ismillisecond: false
    precision: 0
    frameMj: 0
    controlwidth: 1
    ordernumingrid: 10
    dispfielddesc: false
    fielddesc: ""
    todispingrid: true
    isquerycondition: false
    isorderfield: false
    orderdirection: "asc"
    isexportexcel: false
    gridmultirows: false
    gridwidth: 100
    dispInadd: true

  - name: customer_status
    type: nvarchar
    description: 客户状态
    length: 50
    datasourceCodename: 审核状态     # ← 绑定代码项
    fielddisplaytype: combobox       # ← 下拉显示
    notnull: true
    mustfill: true
    todispingrid: true
    gridwidth: 100
    dispInadd: true

  - name: create_time
    type: datetime
    description: 创建时间
    length: 50
    fielddisplaytype: datepicker
    notnull: true
    todispingrid: true
    gridwidth: 100
    dispInadd: true

# 关联关系
relations:
    # 关联名称
  - name: link_to_customer_main
    # 目标表
    targetmodel: customer_main
    # 目标字段
    targetfield: rowguid
    # 当前字段
    currentfield: pid
    # 当前表
    currentmodel: customerinfo
    # 类型（0-一对一，1-一对多）
    type: 1
```

## 对话脚本（创建新 mis 表）

### 第一步：基本信息

```
你要创建什么数据表？
1. 这张表的英文表名想叫什么？（小写英文数字、无下划线，如 customerinfo；如果没想好，可以根据中文名建议一个）
2. 这张表的中文描述是什么？（如 客户信息表）
```

### 第二步：核心字段（按字段类型分组询问）

```
请告诉我这张表的字段。我用以下分类问你，每类填了再下一类：

1. 主键字段：默认有一个 rowguid (nvarchar, 50, 主键)，要改吗？

2. 普通文本字段（nvarchar）：
   - 字段名 | 描述 | 长度 | 是否必填
   例: customer_name | 客户姓名 | 50 | 是

3. 数字字段（Integer/Numeric）：

4. 日期字段（datetime）：

5. 字典/下拉字段（绑定 codeitem）：
   - 字段名 | 描述 | 绑定代码项名 | 是否必填
   例: customer_status | 客户状态 | 审核状态 | 是

6. 部门/用户字段（特殊框架字段）：

7. 大文本/附件字段（ntext/Image）：
```

> 用户可一次性甩一段需求："客户信息表，要有姓名(50)、手机号(50, 唯一)、状态(下拉, 绑定审核状态)、创建时间"，AI 自动拆解。

### 第三步：关联关系（可选）

```
如果这张表要关联其他表，请直接描述关联关系；没有关联可以说"不关联其他表"。
需要的信息：
- 关联表名（targetmodel）
- 当前字段（currentfield）
- 目标字段（targetfield）
- 关系类型（一对一/一对多）
```

### 第四步：创建计划 + 明确批准

```
我准备把这张数据表写入 `.lowcode-plans/<apptag>-plan.md` 并先等你确认：

- 路径：<app-root>/mis/customerinfo.mis.yml
- 字段：
  - customer_name (nvarchar 50, 必填)
  - customer_mobile (nvarchar 50, 唯一)
  - customer_status (nvarchar 50, combobox 绑定 审核状态, 必填)
  - create_time (datetime)
- 关联：
  - 一对多 -> customer_main(rowguid)

请回复"批准创建"后我再写文件；也可以直接说要调整字段或关联关系。若表名或字段清单不完整，我会继续追问，不会直接落盘。
```

## 修改已有 mis 表

```
当前 customerinfo.mis.yml 字段：
  - customer_name (nvarchar 50)
  - customer_mobile (nvarchar 50)
  ...

你要：
1. 添加新字段
2. 删除某字段（哪个？）
3. 修改某字段属性（哪个字段？哪个属性？）
4. 调整关联关系
```

### 添加字段对话

```
新字段：
- 字段名（英文 + 下划线）：customer_phone
- 显示名（中文）：客户固定电话
- 类型：nvarchar/Integer/Numeric/datetime/ntext/Image
- 长度（如 50）：
- 这个字段是否必填？可以说"必填"或"非必填"：
- 是否绑定代码项？如绑定，代码项名是？
- 显示控件类型？默认 textbox
```

直接调用 `python scripts/add_mis_field.py --mis <yml绝对路径> --name customer_phone --type nvarchar --length 50 --description "客户固定电话"`。

## 字段填充策略（避免每个字段都问 30 个属性）

字段属性虽多，但**大部分有合理默认值**。对话时只问关键属性，其他用模板默认值填：

### 必问的属性（用户必须给）

- `name`、`type`、`description`、`length`

### 偏好级属性（询问 1-2 个常用的）

- `mustfill`（是否必填）：默认 false
- `notnull`（数据库非空）：默认 true
- `datasourceCodename`（绑定代码项）：默认空

### 模板自动填充的属性（用默认值）

| 属性 | 默认值 |
|------|--------|
| `defaultvalue` | `""` |
| `autoincrease` | `false` |
| `uniquefield` | `false` |
| `isforeignkey` | `false` |
| `isframeou` | `false` |
| `isframeuser` | `false` |
| `iscustom` | `false` |
| `fieldjd` | `2` |
| `ismillisecond` | `false` |
| `precision` | `0` |
| `frameMj` | `0` |
| `fielddisplaytype` | 根据 `type` 推断（见上表） |
| `controlwidth` | `1` |
| `ordernumingrid` | 自增（10, 20, 30...） |
| `dispfielddesc` | `false` |
| `fielddesc` | `""` |
| `todispingrid` | `true` |
| `isquerycondition` | `false` |
| `isorderfield` | `false` |
| `orderdirection` | `"asc"` |
| `isexportexcel` | `false` |
| `gridmultirows` | `false` |
| `gridwidth` | `100` |
| `dispInadd` | `true` |

> **关键经验**：写字段时不要拼命填全部 30+ 属性，**只显式写"非默认"的部分**。`scripts/add_mis_field.py` 会自动用模板默认值补齐。

## 校验规则

| 校验项 | 校验方式 |
|-------|---------|
| 第一行 `type: mis` | 字符串校验 |
| `tableName` 与文件名英文部分一致 | 文件名比对 |
| `name` 与 `tableName` 相同（推荐） | 一致性 |
| `fields` 非空数组 | 数组校验 |
| 每个字段有 `name`、`type`、`description`、`length` | 必填字段 |
| 字段 `type` 在合法枚举内 | 枚举校验 |
| `fielddisplaytype` 在合法枚举内 | 枚举校验 |
| `datasourceCodename` 引用的代码项存在（高级） | 跨文件校验 |
| 关联中 `targetmodel` 是已存在的 mis | 跨文件校验 |

## 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| `type: nvarchar(50)` 而不是分开写 type 和 length | 解析失败 | 改为 `type: nvarchar` + `length: 50` |
| `datasourceCodename: 审核状态` 但代码项不存在 | 下拉框为空 | 先创建代码项再绑定 |
| `tableName` 用驼峰命名（CustomerInfo） | SQL 报错 | 改为小写英文数字且无下划线（customerinfo） |
| 字段 type 是 `String` 而不是 `nvarchar` | 不识别 | 改为 `nvarchar` |
| 漏 `length: 50` | 数据库建表失败 | 必填，按字段长度填 |

## 快速生成脚本

```bash
# 创建空 mis 表
python scripts/add_mis_field.py \
  --app-root <app-root> \
  --table customerinfo \
  --table-desc "客户信息表" \
  --create

# 给已有表追加字段
python scripts/add_mis_field.py \
  --mis <yml绝对路径> \
  --name customer_phone \
  --type nvarchar --length 50 \
  --description "客户固定电话" \
  --mustfill false
```
