# SQL查询节点

## 节点类型

- **data.type**: `sqlquery`
- **title**: `"SQL查询"`
- **连线类型(sourceType/targetType)**: `sqlquery`

## 概述

SQL查询节点允许直接编写 SQL 语句查询数据，适用于所有查询场景（简单查询、多表联查、聚合统计等）。需要分页查询时，使用数据表查询列表资产代替。

## 节点结构

```yaml
- data:
    sqlstring: "select * from frame_user"    # SQL 语句（必填）
    sql_return_type: "列表"                   # 返回类型："列表" 或 "单条"
    is_datasource_formula: "固定值"           # SQL来源："固定值" 或 "公式"
    datasource: ""                            # 数据源（留空使用默认）
    sql_output: []                            # 输出字段定义（自动生成）
    variables: []
    type: "sqlquery"
    title: "SQL查询"
    vision:
      enabled: false
    context:
      variable_selector: []
      enabled: false
    model:
      mode: "chat"
      completion_params:
        temperature: 0.7
      provider: ""
      name: ""
    selected: false
    desc: ""
    prompt_template:
    - role: "system"
      text: ""
  targetPosition: "left"
  width: 244
  sourcePosition: "right"
  positionAbsolute:
    x: 384
    y: 282
  id: "{节点ID}"
  position:
    x: 384
    y: 282
  type: "custom"
  height: 54
```

## 核心字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sqlstring` | string | ✅ | SQL 查询语句，如 `"select * from frame_user"` |
| `sql_return_type` | string | ✅ | 返回类型：`"列表"` 返回数组，`"单条"` 返回单条对象 |
| `is_datasource_formula` | string | ❌ | SQL 来源方式：`"固定值"` 直接写 SQL，`"公式"` 通过公式动态生成 |
| `datasource` | string | ❌ | 数据源标识，留空使用默认数据源 |
| `sql_output` | array | ❌ | 输出字段定义（由系统根据 SQL 结果自动生成，无需手动填写） |

## sql_output 字段结构

`sql_output` 定义 SQL 查询的返回字段，通常由系统根据 SQL 执行结果自动生成：

```yaml
sql_output:
- variable: "result"           # 输出变量名
  type: "array[object]"        # 返回类型：列表时为 array[object]，单条时为 object
  desc: "执行结果"              # 描述
  children:                    # 字段列表
  - variable: "userguid"       # 字段名
    description: "userguid"    # 字段描述
    type: "string"             # 字段类型：string / int / datetime 等
  - variable: "displayname"
    description: "displayname"
    type: "string"
```

**常用字段类型**：

| 类型 | 说明 |
|------|------|
| `string` | 字符串 |
| `int` | 整数 |
| `datetime` | 日期时间 |

## 返回类型

| sql_return_type | 说明 | 输出变量类型 | 输出路径 |
|----------------|------|-------------|---------|
| `"列表"` | 返回多条记录 | `array[object]` | `s{节点ID}Context.data.result` |
| `"单条"` | 返回单条记录 | `object` | `s{节点ID}Context.data.result` |

## 使用场景

### 场景一：简单全表查询

```yaml
sqlstring: "select * from frame_user"
sql_return_type: "列表"
```

### 场景二：条件查询

```yaml
sqlstring: "select * from frame_user where isenabled = 1"
sql_return_type: "列表"
```

### 场景三：多表联查

```yaml
sqlstring: "select u.displayname, u.loginid, o.ouname from frame_user u left join frame_ou o on u.ouguid = o.ouguid"
sql_return_type: "列表"
```

### 场景四：聚合统计

```yaml
sqlstring: "select ouguid, count(*) as usercount from frame_user group by ouguid"
sql_return_type: "列表"
```

### 场景五：查询单条记录

```yaml
sqlstring: "select * from frame_user where userguid = '${userguid}'"
sql_return_type: "单条"
```

## 结束节点引用 SQL 查询结果

在结束节点的 `responseParams` 中引用 SQL 查询结果：

```yaml
- UID: "root"
  showName: "根节点"
  children: []
  defaultValue:
    formula:
      expression: "RuleParamUtil.parserParam(s1779191173884Context,\"data.result\")"
      header: ""
      text: "SQL查询.result"
      value:
      - name: "SQL查询.result"
        id: "47d1af42-323e-4ed6-a004-7c85c3bbefe8;s1779191173884Context.data.result"
        value: "s1779191173884Context.data.result"
    valueMode: "formula"
    value: ""
  name: "根节点"
  ParentTaskUID: -1
  type: "OBJECT"
  required: true
```

**引用格式**：`s{SQL查询节点ID}Context.data.result`

## 与数据表查询节点的区别

| 对比项 | SQL查询节点 | 数据表查询列表节点 |
|--------|-----------|----------------|
| 查询方式 | 直接写 SQL | 通过表名+条件+字段配置 |
| 多表联查 | ✅ 支持 | ❌ 不支持 |
| 聚合统计 | ✅ 支持 | ❌ 不支持 |
| 复杂条件 | ✅ 灵活 | 仅支持简单条件或 SQL WHERE 片段 |
| 分页查询 | ❌ 不支持 | ✅ 支持（pageIndex/pageSize） |
| 安全性 | 需注意 SQL 注入 | 更安全，参数化查询 |
| 适用场景 | 所有查询（不分页） | 需要分页的查询 |

## 注意事项

1. **SQL 注入风险**：使用变量拼接 SQL 时注意防范注入，优先使用参数化方式
2. **表名大小写**：部分数据库对表名大小写敏感，建议使用实际表名
3. **性能考虑**：避免查询大量数据不分页，大数据量场景建议加 `LIMIT` 或分页条件
4. **sql_output**：生成 DSL 时可先留空 `[]`，导入后系统会根据 SQL 自动填充字段定义
5. **连线类型**：SQL 查询节点的 `sourceType` 和 `targetType` 均为 `sqlquery`

## 相关文档

- [数据表查询列表](../数据表/查询列表.md)
- [数据表查询详情](../数据表/查询详情.md)
- [通用节点说明](../../通用节点说明.md)
