# 代码项：codeitem yml

## 1. 资产定位与边界

`codeitem` 是低代码体系里的"**数据字典**"，用于定义业务枚举值（如审核状态、采购类型、行政区划）。每个 codeitem yml 描述**一组**同主题的代码值。

- 与 应用根目录的对应关系：`<apptag>/codeitem/<代码项名称>.codeitem.yml`（历史 `<名称>.yml` 仅兼容读取）
- 不在本资产范围内的事：
  - 字典在 UI 上的呈现样式（下拉/单选）由 `mis` 字段的 `fielddisplaytype` 决定，详见 `references/mis/数据模型/index.md`
  - 跨应用引用代码项的写法属于 `appref`，详见 `references/appref/引用配置/index.md`

## 2. 文档导航

> 本资产的所有内容均承载于本 index.md（R6.3 例外为 appinfo/appref；其他资产若超 600 行需拆出平级文档）。
> 章节速查：
> - § 文件位置与命名：见下文「[文件位置与命名](#文件位置与命名)」
> - § 完整字段表（顶层 / items 子项 / 嵌套子项）：见下文「[完整字段表](#完整字段表)」
> - § 标准示例 + 简单示例：见下文「[标准示例（来自本工程-审核状态yml）](#标准示例来自本工程-审核状态yml)」「[简单示例（无嵌套）](#简单示例无嵌套)」
> - § 字段细节（codevalue 加引号 / ordernumber / 引用代码项的位置）：见下文「[字段细节](#字段细节)」
> - § 校验规则与常见错误：见下文「[校验规则](#校验规则)」「[常见错误](#常见错误)」

## 3. 生成与修改对话速查

> 详细对话脚本与脚本调用：见下文「[对话脚本（创建新代码项）](#对话脚本创建新代码项)」「[修改已有代码项](#修改已有代码项)」「[快速生成脚本](#快速生成脚本)」与脚本 cheatsheet `references/directory-structure.md`。

## 4. 与其他资产的引用关系

- 引用其他资产：无（codeitem 是叶子资产，不引用其他 yml）
- 被其他资产引用：
  - `mis` 字段的 `datasourceCodename` 写代码项 `name`（如 `审核状态`），详见下文「[引用代码项的位置](#引用代码项的位置)」
  - 跨应用引用通过 `appref` 的 `engineguid: codeitem` 暴露
  - 前端 Vue 页面通过 `useDictionary('<name>')` 加载
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs <app-root>`

---

代码项即"数据字典"，用于定义业务枚举值（如审核状态、采购类型、行政区划）。每个 codeitem yml 描述**一组**同主题的代码值。

## 文件位置与命名

```
<app-root>/codeitem/<代码项名称>.codeitem.yml
                    或
<app-root>/codeitem/<代码项名称>.codeitem.yml
```

- 推荐**中文名**作为文件名（如 `审核状态.codeitem.yml`），与 yml 内 `name:` 字段保持一致
- 新建必须使用 `.codeitem.yml`；单扩展 `.yml` 仅兼容历史文件

## 完整字段表

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | **固定为 `codeitem`** |
| `name` | string | ✅ | 代码名称，与文件名一致 |
| `description` | string | ❌ | 代码说明 |
| `items` | array | ✅ | 代码子项列表 |

### items 子项字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `codetext` | string | ✅ | 显示文本（中文，如 `草稿`） |
| `codevalue` | string | ✅ | 实际值（**必须加引号**保持字符串型，如 `"0"`） |
| `ordernumber` | int | ❌ | 排序号；越小越靠前；省略默认 0 |

### 嵌套子项

代码子项支持**多层嵌套**，子项内继续写 `- codetext` 列表，缩进对齐：

```yaml
items:
  - codetext: 审核驳回
    codevalue: "3"
    ordernumber: 4
    # 子项嵌套子项，支持多层
    - codetext: 审核驳回-1
      codevalue: "31"
      ordernumber: 0
    - codetext: 审核驳回-2
      codevalue: "32"
      ordernumber: 0
```

> ⚠️ 注意嵌套语法：父项的 `- codetext: ...` 与子项的 `- codetext: ...` 是同一级 list，靠**缩进**表示嵌套。这是 yml 文档原始示例的写法，渲染器可识别。

## 标准示例（来自本工程 `审核状态.codeitem.yml`）

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
  - codetext: 待审核
    codevalue: "1"
    ordernumber: 2
  - codetext: 审核通过
    codevalue: "2"
    ordernumber: 3
  - codetext: 审核驳回
    codevalue: "3"
    ordernumber: 4
      # 子项嵌套子项，支持多层
      - codetext: 审核驳回-1
        codevalue: "31"
        ordernumber: 0
      - codetext: 审核驳回-2
        codevalue: "32"
        ordernumber: 0
```

## 简单示例（无嵌套）

```yaml
type: codeitem
name: 类型
description: 类型字典
items:
  - codetext: A
    codevalue: "0"
    ordernumber: 5
  - codetext: B
    codevalue: "1"
    ordernumber: 2
  - codetext: C
    codevalue: "2"
    ordernumber: 3
```

## 对话脚本（创建新代码项）

### 第一步：基本信息

```
你要创建什么代码项？
1. 这个代码项叫什么？（如 审核状态、采购类型）
2. 它大概描述什么业务含义？如果名称已经清楚，可以省略描述。
```

### 第二步：录入子项

```
请提供代码子项，每行一个，格式：
  显示文本 | 值 | 排序号(可选)

例如：
  草稿 | 0 | 5
  待审核 | 1 | 2
  审核通过 | 2 | 3

输入完毕请输入"完成"。
```

> 用户也可以一句话给：「审核状态有 草稿/待审核/审核通过/审核驳回 四个状态」，AI 自动拆分。

### 第三步（可选）：是否有嵌套子项？

```
如果某个子项还要继续细分，直接说明要细分哪一项以及子状态列表。
例如："审核驳回下面再分材料不全、资格不符。"
```

### 第四步：更新计划与追溯 + 明确批准

```
我准备把这个代码项写入 `.lowcode-plans/<apptag>-plan.md` 并先等你确认：

- 路径：<app-root>/codeitem/审核状态.codeitem.yml
- 名称：审核状态
- 子项：
  - 草稿：0，排序 5
  - 待审核：1，排序 2
  - ...

请回复"批准创建"后我再写文件；也可以直接说要调整哪一项。若缺少子项信息，我会继续追问，不会直接落盘。
```

每次追问子项、排序策略或嵌套关系前，都要先把问题和选项写入计划文档的 `对话确认记录`；用户回复后回填确认结果，再决定是否进入批准。

## 修改已有代码项

```
当前 审核状态.codeitem.yml 内容：
  - codetext: 草稿, codevalue: "0", ordernumber: 5
  - codetext: 待审核, codevalue: "1", ordernumber: 2
  - codetext: 审核通过, codevalue: "2", ordernumber: 3
  - codetext: 审核驳回, codevalue: "3", ordernumber: 4

你要：
1. 添加新子项
2. 删除某子项（哪个？）
3. 修改某子项的文本/值/排序
4. 给某子项添加嵌套子项
```

## 字段细节

### `codevalue` 加引号的原因

- 即使值是数字，也是**字符串语义**，必须加引号 `"0"`
- 不加引号会被 yml 解析器当作 number，导致与代码项字段（`fielddisplaytype: combobox`）数据类型不匹配
- 推荐数字值：`"0"`、`"1"`、`"99"`；字母值：`"A"`、`"B"`；编码值：`"320100"`

### `ordernumber` 的作用

- 控制下拉框、单选框等组件中选项的显示顺序
- 越小越靠前
- 不写则按 yml 中数组顺序展示，但**推荐显式写**避免变化

### 引用代码项的位置

代码项被以下地方引用：

| 引用点 | 字段 | 写法 |
|-------|------|-----|
| MIS 字段 | `datasourceCodename` | 写代码项 name，如 `审核状态` |
| Vue 页面 | 通过 `useDictionary` API 加载 | `useDictionary('审核状态')` |
| 跨应用引用 | `appref.lowcode.yml` | `engineguid: codeitem, name: [审核状态]` |

## 校验规则

| 校验项 | 校验方式 |
|-------|---------|
| 第一行是 `type: codeitem` | 字符串校验 |
| `name` 与文件名（去扩展）一致 | 文件名比对 |
| `items` 是非空数组 | 数组校验 |
| 每个 item 有 `codetext` 和 `codevalue` | 必填字段 |
| `codevalue` 字符串不重复（同级别下） | 唯一性校验 |
| `ordernumber` 为非负整数 | 类型校验 |

## 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| `type: code` | 渲染器不识别 | 改为 `type: codeitem` |
| `codevalue: 0`（无引号） | 解析为整数，引用对不上 | 改为 `codevalue: "0"` |
| `name: 审核状态` 但文件名是 `auditstatus.yml` | 引用查找失败 | 文件名改为 `审核状态.codeitem.yml` |
| 漏掉 `items:` 字段 | 空代码项无法使用 | 至少给一个示例子项 |

## 快速生成脚本

```bash
python3 scripts/add_codeitem.py \
  --app-root <应用根目录绝对路径> \
  --name 审核状态 \
  --description "审核状态字典" \
  --items-json '[
    {"codetext": "草稿", "codevalue": "0", "ordernumber": 5},
    {"codetext": "待审核", "codevalue": "1", "ordernumber": 2},
    {"codetext": "审核通过", "codevalue": "2", "ordernumber": 3}
  ]'
```

脚本会：
1. 复制 `assets/templates/codeitem.yml` 模板
2. 填入 name/description/items
3. 写到 `<app-root>/codeitem/<name>.codeitem.yml`
4. 跑一次静态校验
