# MCP 工具使用说明

**本文档说明如何使用 Lowcode MCP 工具查询资产和文档信息。**

> 本文档从 `event/动作流/index.md` 拆分而来，便于按需加载。

---

## 可用的 MCP 工具

| 工具名称 | 用途 | 使用示例 |
|---------|------|----------|
| `read_document` | 查询项目文档（markdown 文件） | `read_document(path="动作流/节点/业务动作/通用节点说明.md")` |
| `query_action` | 查询业务动作（资产） | `query_action(query="部门服务")` 或 `query_action(query="用户")` |
| `query_table` | 查询 MIS 表结构（数据字典） | `query_table(query="Frame_Ou")` 或 `query_table(query="部门")` |
| `query_rest` | 查询 REST API 接口 | `query_rest(query="部门接口")` |
| `query_tool_function` | 查询工具函数 | `query_tool_function(query="UUID生成", methodName="")` |

## 使用场景

1. **查询基础结构和节点**
   - 使用 `read_document` 查询：
     - `动作流/基础结构/app配置.md`
     - `动作流/基础结构/workflow配置.md`
     - `动作流/基础结构/graph结构.md`
     - `动作流/节点/触发节点/webhook触发.md`
     - `动作流/节点/逻辑节点/条件分支.md`
     - 等等...

2. **查询业务动作（资产）**
   - 使用 `query_action` 查询业务专有资产：
     - `query_action(query="部门")` - 查询部门相关的业务动作
     - `query_action(query="用户")` - 查询用户相关的业务动作
     - `query_action(query="新增")` - 查询新增操作相关的业务动作
   - **查询结果格式**：
     ```json
     [
       {
         "methodName": "新增部门",
         "inparam": [
           {
             "name": "ou",
             "type": "object",
             "desc": "ou 部门对象 FrameOu",
             "children": [
               {"name": "ouname", "type": "string", "desc": "部门名称 String"},
               {"name": "ouguid", "type": "string", "desc": "部门标识 String"}
             ]
           }
         ],
         "outparam": "void"
       }
     ]
     ```
   - **如何使用查询结果**：
     - `methodName` - 资产的中文名称，用于配置节点的 `tool_name` 和 `actionData.action`
     - `inparam` - 输入参数列表，用于配置节点的 `actionData.formData`
     - `outparam` - 输出参数结构，用于理解资产的返回值

3. **查询数据表结构（MIS 表数据字典）**
   - 使用 `query_table` 查询 MIS 表结构（数据字典）：
     - `query_table(query="Frame_Ou")` - 查询部门表结构
     - `query_table(query="Frame_User")` - 查询用户表结构
     - `query_table(query="部门")` - 查询所有包含"部门"的表
     - `query_table(query="用户")` - 查询所有包含"用户"的表
   - **查询返回格式**：
     ```json
     [
       {
         "tableName": "FRAME_OU",
         "tableCName": "统一部门表",
         "description": "表描述",
         "columns": [
           {
             "name": "ouguid",
             "cname": "ouguid",
             "type": "nvarchar",
             "length": 100,
             "isPrimaryKey": true,
             "required": true
           },
           {
             "name": "ouname",
             "cname": "ouname",
             "type": "nvarchar",
             "length": 100,
             "isPrimaryKey": false,
             "required": false
           }
         ]
       }
     ]
     ```
   - **如何使用查询结果**：
     - `tableName` - 表的英文名称（用于配置通用数据表资产的 `tableName` 参数）
     - `tableCName` - 表的中文名称（帮助理解表的业务含义）
     - `columns[].name` - 字段英文名（用于数据映射的字段名）
     - `columns[].cname` - 字段中文名（帮助理解字段含义）
     - `columns[].type` - 字段数据类型（帮助理解数据格式）
     - `columns[].isPrimaryKey` - 是否主键（主键字段通常需要生成 UUID）
     - `columns[].required` - 是否必填（必填字段不能为空）

4. **查询场景示例**
   - 使用 `read_document` 查询：
     - `动作流/场景示例/Push模式-接收数据-多层级插入.md`
     - `动作流/场景示例/Pull模式-输出数据-多表联查.md`
     - `动作流/场景示例/Schedule模式-定时同步-组织架构.md`

## 文档路径说明

使用 `read_document` 时，路径格式为：`动作流/目录/文件名.md`

**常用文档路径**：
- 基础结构：`动作流/基础结构/app配置.md`、`动作流/基础结构/workflow配置.md`、`动作流/基础结构/graph结构.md`
- 触发节点：`动作流/节点/触发节点/webhook触发.md`、`动作流/节点/触发节点/定时任务触发.md`
- 逻辑节点：`动作流/节点/逻辑节点/条件分支.md`、`动作流/节点/逻辑节点/迭代.md`
- 转换节点：`动作流/节点/转换节点/代码执行.md`、`动作流/节点/转换节点/变量赋值.md`
- 结束节点：`动作流/节点/结束节点/结束.md`
- 业务动作：`动作流/节点/业务动作/通用节点说明.md`
- 面板配置（当查询资产包含panelPath时使用）：
  - 数据表面板：`动作流/节点/业务动作/基础支撑/数据表/面板配置说明.md`
- 场景示例：`动作流/场景示例/Push模式-接收数据-多层级插入.md`

## 查询示例

**示例1：查询部门相关资产**
```
调用：query_action(query="部门")
返回：12个业务动作，包括"新增部门"、"新增部门信息"、"查询部门基本信息"、"查询部门集合"等
使用：选择合适的 methodName，如需新增部门，使用 "新增部门"
```

**示例2：查询用户相关资产**
```
调用：query_action(query="用户")
返回：10个业务动作，包括"新增用户"、"新增用户（不包含照片）"、"根据用户字段查询出用户"等
使用：选择合适的 methodName，如需新增用户，使用 "新增用户"
```

**示例3：查询通用数据操作资产**
```
调用：query_action(query="新增数据")
返回：包含 methodName: "新增数据"，inparam: [{"name":"tableName",...}, {"name":"appGuid",...}]
使用：当业务专有资产不存在时，使用此通用资产
```

**示例4：查询 MIS 表结构（数据字典）**
```
调用：query_table(query="Frame_Ou")
返回：{
  "tableName": "FRAME_OU",
  "tableCName": "统一部门表",
  "columns": [
    {"name": "ouguid", "cname": "ouguid", "type": "nvarchar", "isPrimaryKey": true, "required": true},
    {"name": "ouname", "cname": "ouname", "type": "nvarchar", "isPrimaryKey": false, "required": false},
    {"name": "oucode", "cname": "oucode", "type": "nvarchar", "isPrimaryKey": false, "required": false},
    ...
  ]
}
使用：了解表结构，用于配置通用数据表资产的参数或理解字段含义
```

**示例5：查询包含关键词的所有表**
```
调用：query_table(query="部门")
返回：多个包含"部门"的表，如 FRAME_OU（统一部门表）、cg_purchasebudgetandou（采购预算关联部门表）等
使用：发现业务相关的所有数据表
```

**示例6：根据 panelPath 查询面板配置**
```
场景：query_action 返回的资产包含 panelPath: "frame-datasource/data-query-list"
调用：read_document(path="动作流/节点/业务动作/基础支撑/数据表/面板配置说明.md")
返回：查询列表面板配置，包括 action: "misfindlistaction"，formData 需要 5 个参数
使用：根据面板配置生成完整的数据表查询列表节点
```

**补充：数据表面板必填字段（仅适用于基础支撑-数据表）**
- 详见：`动作流/节点/业务动作/基础支撑/数据表/面板配置说明.md`
- actionData 下：`category` 固定为 `biz_action`

## 最佳实践

1. **优先使用 MCP 工具**：不要假设或猜测资产信息，始终使用 `query_action` 查询
2. **组合使用工具**：
   - 先用 `query_action` 查询资产列表
   - 使用通用资产前，用 `query_table` 查询表结构
   - 辅助使用 `read_document` 查询详细文档说明
3. **精确查询**：使用具体的关键词进行查询，提高查询准确性
4. **验证存在性**：
   - 使用资产前，必须先用 `query_action` 验证其存在
   - 使用表名前，必须先用 `query_table` 验证表结构
5. **文档路径规范**：使用 `read_document` 时，确保路径格式正确，使用正斜杠 `/` 分隔
6. **使用实际名称**：
   - 资产：始终使用查询返回的实际 `methodName`
   - 表名：始终使用查询返回的实际 `tableName`
   - 字段：始终使用查询返回的实际 `columns[].name`
7. **参数严格匹配**：
   - 资产参数必须与 `query_action` 返回的 `inparam` 严格匹配
   - 表字段必须与 `query_table` 返回的 `columns` 严格匹配
8. **注意数据类型和约束**：
   - 关注字段的 `type`、`length` 限制
   - 主键字段（`isPrimaryKey: true`）通常需要生成 UUID
   - 必填字段（`required: true`）不能为空或缺失
9. **查询资产包含 panelPath 时**：
   - 根据 `panelPath` 值查询对应的面板配置文档
   - 按照面板配置的要求生成节点（包括正确的 `action`、`tool_name` 和 `formData` 参数）
