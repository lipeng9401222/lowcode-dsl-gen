# 引用配置：appref.lowcode.yml

## 1. 资产定位与边界

- 本资产解决：声明本应用引用了**其他应用**的资产（代码项、数据表、模块、动作流、工作流、页面），让多个应用之间可以**共享**这些资产。
- 不在本资产范围内的事：资产本身的定义与生成（由各自的 codeitem/mis/module/workflow/event/pagedesigne 资产负责）。
- 与 metadata 目录的对应关系：`metadata/<apptag>/appref.lowcode.yml`

### 文件位置

```
<metadata>/appref.lowcode.yml
```

可选文件，没有引用关系时不需要。

### 与 appinfo 内联 refs 的区别

`appinfo.lowcode.yml` 的 `refs:` 字段也能写引用关系。两者**等价**，但实践上：

| 写法 | 推荐场景 |
|-----|---------|
| `appinfo.lowcode.yml` 内联 `refs:` | 引用项 ≤ 5 个，简单应用 |
| 单独 `appref.lowcode.yml` | 引用项较多，或团队习惯解耦 |

> 同一应用**不要两个地方都写**，会导致重复或冲突。

### 完整字段表

文件本身是一个**对象数组**，每项代表一组对某类型资产的引用：

```yaml
- engineguid: <资产类型>
  name: [<资产名1>, <资产名2>, ...]
  sourceAppTag: <被引用应用的 apptag>     # 可选
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `engineguid` | string | ✅ | 资产类型；取值见下表 |
| `name` | array of string | ✅ | 资产名称数组 |
| `sourceAppTag` | string | ❌ | 被引用资产所在应用的 apptag；不填表示从平台公共应用引用 |

#### `engineguid` 取值表

| engineguid | 引用什么 | name 数组里写什么 |
|-----------|---------|------------------|
| `codeitem` | 代码项 | 代码项 name（如 `审核状态`） |
| `mis` | 数据表 | mis 的 tableName（英文表名，如 `customerinfo`） |
| `module` | 模块 | module 的 name 或 guid |
| `event` | 动作流 | 动作流 sign 或文件名 |
| `workflow` | 工作流 | 流程 processName 或 processGuid |
| `pagedesigne` | 页面 | 页面 id 或文件名 |

### 标准示例（来自 `01-vue方案.md`）

```yaml
- engineguid: codeitem
  name: [行政区划, 审核状态, 采购类型]

- engineguid: mis
  name: [项目信息表, 供应商信息表, 合同信息表]
```

### 跨应用引用示例

引用 `common` 公共应用下的代码项：

```yaml
- engineguid: codeitem
  name: [行政区划]
  sourceAppTag: common

- engineguid: codeitem
  name: [审核状态]
  sourceAppTag: common

- engineguid: mis
  name: [projectinfo, supplierinfo]
  sourceAppTag: common
```

### 应用内联示例（appinfo 里写）

如果选择内联到 `appinfo.lowcode.yml`：

```yaml
developerstag: epoint
applicationname: 采购立项
apptag: purchaseproject
kitid: businessprocess
baseouguid: ""
refs:
  - engineguid: codeitem
    name: [行政区划]
    sourceAppTag: common
  - engineguid: mis
    name: [supplierinfo]
    sourceAppTag: common
```

格式与独立文件完全相同，只是位置不同。

## 2. 文档导航

> 本资产为 R6.3 例外（195 行，内容量小），无平级子文档。

| 文档 | 用途 | 何时读 |
|------|------|--------|
| （无子文档） | — | — |

## 3. 生成与修改对话速查

### 对话脚本（添加引用）

```
你想引用什么类型的资产？
1. 代码项（codeitem，如 审核状态、行政区划）
2. 数据表（mis）
3. 模块（module）
4. 动作流（event）
5. 工作流（workflow）
6. 页面（pagedesigne）

选 1 后：
  → 列出哪些代码项？（可多个，逗号分隔）
  → 这些代码项来自哪个应用的？[默认: common 公共应用]
```

每加一组都用自然语言复述来源应用和资产清单，再问用户是否还要继续补充。不要使用快速是/否确认，可以让用户直接说"继续加代码项"、"再加一个模块引用"或"这些就够了"。

### 修改已有 appref 的对话脚本

```
当前引用关系：
  - codeitem: [行政区划]  ← 来自 common
  - mis: [customerinfo]  ← 来自 common

你要：
1. 增加新引用
2. 删除某个引用（哪个？）
3. 修改某项的来源应用（如 sourceAppTag 从 common 改为 xxx）
```

### 校验规则

| 校验项 | 校验方式 |
|-------|---------|
| 整个文件是 yaml 数组 | 顶层结构 |
| 每项有 `engineguid` 和 `name` | 必填字段 |
| `engineguid` 取值在白名单内 | 枚举校验 |
| `name` 是非空数组 | 数组校验 |
| `name` 中每个值是非空字符串 | 元素校验 |
| 引用的资产实际存在（高级校验） | 解析 sourceAppTag 应用，查找资产 |

> 高级校验需要扫描整个工程，调用 `python scripts/validate_yml.py --check-refs <metadata 路径>`。

### 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| `engineguid` 拼成 `codeitems`（多了 s） | 引用失败 | 改回 `codeitem` |
| `name: 行政区划`（不是数组） | 解析报错 | 改为 `name: [行政区划]` |
| `sourceAppTag: Common`（大写） | 解析失败 | 改为全小写 `common` |
| 文件名拼错 `appref.yml`（少 `.lowcode`） | 不会被加载 | 改为 `appref.lowcode.yml` |

## 4. 与其他资产的引用关系

- 引用其他资产：通过 `engineguid` 字段引用 codeitem / mis / module / workflow / event / pagedesigne 六类资产。
- 被其他资产引用：无（appref 是单向声明文件）。
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs`

### 与 appinfo 互斥规则

- 同一应用**不要同时**在 `appinfo.lowcode.yml` 的 `refs:` 和 `appref.lowcode.yml` 里写引用
- 修改时若发现两个地方都有，**优先合并到 `appref.lowcode.yml`**，并清空 `appinfo` 里的 `refs:`
