# 场景一：多层级数据接收与插入（Push模式）

## 业务需求

接收第三方推送的采购立项信息，包含项目、标段、行项目三层嵌套结构，验证后批量插入数据库。

## 典型应用

- 采购立项信息推送
- 订单信息同步
- 多层级表单提交
- 复杂业务数据接收

## 数据结构

```json
{
  "projectinfo": {
    "projectno": "PRJ001",
    "projectname": "示例项目",
    "guominjingjifenlei": "A类",
    "zijinlaiyuan": "财政资金",
    "jianshedanweiguid": "xxx-guid",
    "jianshedanwei": "建设单位名称",
    "biaoduaninfo": [
      {
        "biaoduanno": "BD001",
        "biaoduanname": "标段1",
        "touzigusuan": 1000000,
        "lineiteminfo": [
          {
            "lineitemno": "L001",
            "itemno": "I001",
            "productcategory": "物资",
            "unit": "台",
            "num": 10,
            "unitprice": 5000,
            "totalprice": 50000
          }
        ]
      }
    ]
  }
}
```

## 工作流设计

```
1. Webhook 触发接收数据
   ↓
2. 条件判断：检查项目编号是否为空
   ↓ True（为空）           ↓ False（不为空）
   返回"项目编号不能为空"    继续
   ↓
3. 查询项目是否已存在（根据projectno）
   ↓
4. 条件判断：项目是否已存在
   ↓ True（已存在）         ↓ False（不存在）
   返回"项目已存在"         继续
   ↓
5. 插入项目主表（CG_ProjectInfo）
   ↓
6. 迭代标段数组（biaoduaninfo）
   ↓
   6.1 插入标段表（CG_BiaoDuanInfo）
       - 关联项目外键
   ↓
   6.2 嵌套迭代行项目数组（lineiteminfo）
       ↓
       6.2.1 插入行项目表（PR_PRLineItem）
             - 关联标段外键
   ↓
7. 返回成功信息（包含插入的项目ID）
```

## 核心设计要点

1. **参数验证**：接收数据后立即验证必填字段，提前返回错误
2. **重复检查**：插入前查询数据是否已存在，避免重复插入
3. **嵌套迭代**：处理多层级数据结构（项目→标段→行项目）
4. **外键关联**：子表插入时引用父表主键，确保数据完整性
5. **事务性**：整体流程应具备原子性，建议配合错误处理机制

## 详细配置

### 步骤 1：Webhook 触发节点

```yaml
- data:
    variables: []
    actionData:
      panelPath: "frame-webhook/frame-webhook"
      action: "webhookdetail"
      category: "webHook"
      formData:
      - name: "webHookUrl"
        valueMode: "fixed"
        value: "http://localhost:8080/EpointFrame/rest/dynamicapi/huoqucaigoulixiangxinxi"
      - name: "identification"
        valueMode: "fixed"
        value: "huoqucaigoulixiangxinxi"
      - name: "request"
        valueMode: "fixed"
        value:
          requestHeaders:
          - defaultValue: "application/json;charset=utf-8;"
            name: "Content-Type"
          requestBody:
          - UID: "root"
            name: "根节点"
            type: "OBJECT"
            children:
            - name: "projectinfo"
              type: "OBJECT"
              required: true
              children:
              - name: "projectno"
                type: "STRING"
                required: true
              - name: "projectname"
                type: "STRING"
                required: true
              - name: "biaoduaninfo"
                type: "ARRAY"
                required: true
                children:
                - name: "items"
                  type: "OBJECT"
                  children:
                  - name: "biaoduanno"
                    type: "STRING"
                    required: true
                  - name: "biaoduanname"
                    type: "STRING"
                    required: true
                  - name: "lineiteminfo"
                    type: "ARRAY"
                    required: true
    type: "start"
    title: "接收采购立项信息"
  id: "webhook_node"
```

### 步骤 2：验证项目编号

```yaml
- data:
    cases:
    - logical_operator: "and"
      case_id: "true"
      conditions:
      - varType: "string"
        variable_selector:
        - "webhook_node"
        - "body"
        - "projectinfo"
        - "projectno"
        comparison_operator: "empty"
    type: "if-else"
    title: "条件判断：项目编号是否为空"
  id: "check_projectno"
```

### 步骤 3：查询项目是否存在

```yaml
- data:
    type: "biz-action"
    title: "查询项目信息"
    actionData:
      panelPath: "frame-datasource/data-query-detail"
      action: "misfindaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_ProjectInfo"
      - name: "conditions"
        valueMode: "fixed"
        value:
          conditionData:
            name: "and"
            type: "group"
            items:
            - opt: "=="
              left:
              - dataType: "string"
                label: "项目编号"
                type: "tableField"
                value: "projectno"
              right:
              - dataType: "string"
                label: "Webhook触发.body.projectinfo.projectno"
                type: "field"
                value: "swebhook_nodeContext.data.body.projectinfo.projectno"
          sqlData:
            name: ""
            value: []
          type: "simple"
      - name: "queryFields"
        valueMode: "fixed"
        value:
        - name: "rowguid"
          tableId: 201000          # ⚠️ 必填：数据表ID（从query_table获取）
          label: "项目GUID"
          type: "string"
  id: "query_project"
```

### 步骤 4：判断项目是否已存在

```yaml
- data:
    cases:
    - logical_operator: "and"
      case_id: "true"
      conditions:
      - varType: "object"
        variable_selector:
        - "query_project"
        - "CG_ProjectInfo"
        comparison_operator: "not empty"
    type: "if-else"
    title: "条件判断：项目是否已存在"
  id: "check_exists"
```

### 步骤 5：插入项目主表

```yaml
- data:
    type: "biz-action"
    title: "插入项目信息"
    actionData:
      panelPath: "frame-datasource/data-insert"
      action: "misaddaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_ProjectInfo"
      - name: "entities"
        valueMode: "fixed"
        value:
        - name: "rowguid"
          valueMode: "formula"
          formula:
            expression: "StringFunctionRule.getUUID(StringFunctionRule_instance)"
            text: "getUUID()"
            value:
            - fun: "getUUID"
            - "()"
        - name: "projectno"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(swebhook_nodeContext,\"data.body.projectinfo.projectno\")"
            text: "Webhook触发.body.projectinfo.projectno"
        - name: "projectname"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(swebhook_nodeContext,\"data.body.projectinfo.projectname\")"
            text: "Webhook触发.body.projectinfo.projectname"
        - name: "jianshedanweiguid"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(swebhook_nodeContext,\"data.body.projectinfo.jianshedanweiguid\")"
            text: "Webhook触发.body.projectinfo.jianshedanweiguid"
        - name: "createtime"
          valueMode: "formula"
          formula:
            expression: "DateFunctionRule.now(DateFunctionRule_instance)"
            text: "now()"
  id: "insert_project"
```

### 步骤 6：迭代标段数组

**⚠️ 迭代节点配置说明**：
- 必须包含 `output_selector`、`width`、`height`、`parallel_nums`、`resultType`、`zIndex` 等完整字段
- 迭代节点需要配套的迭代开始节点（`custom-iteration-start`）
- 详细配置规范请参考[迭代节点文档](../节点/逻辑节点/迭代.md)

```yaml
# 迭代节点主体
- data:
    output_selector: []              # 输出选择器（必填）
    error_handle_mode: "terminated"  # 错误处理模式
    iterator_selector:               # 迭代数据源
    - "webhook_node"
    - "body"
    - "projectinfo"
    - "biaoduaninfo"
    width: 909                       # 节点宽度（必填）
    start_node_id: "iteration_section_start"  # 开始节点ID
    type: "iteration"
    title: "迭代标段信息"
    is_parallel: false
    parallel_nums: 10                # 并行数量（必填）
    height: 346                      # 节点高度（必填）
    resultType: 0                    # 结果类型（必填）
  id: "iteration_section"
  zIndex: -9999                      # 层级索引（必填，负值显示在下层）

# 迭代开始节点（必需配套节点）
- data:
    isInIteration: true              # 标识在迭代中
    title: ""
    type: "iteration-start"
  selectable: false                  # 不可选择
  sourcePosition: "right"
  type: "custom-iteration-start"
  parentId: "iteration_section"      # 指向父迭代节点
  draggable: false                   # 不可拖动
  targetPosition: "left"
  width: 44
  id: "iteration_section_start"
  zIndex: 1002                       # 高层级显示
  height: 48
```

### 步骤 6.1：插入标段表

```yaml
- data:
    type: "biz-action"
    title: "插入标段信息"
    isInIteration: true
    iteration_id: "iteration_section"
    actionData:
      panelPath: "frame-datasource/data-insert"
      action: "misaddaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_BiaoDuanInfo"
      - name: "entities"
        valueMode: "fixed"
        value:
        - name: "biaoduanguid"
          valueMode: "formula"
          formula:
            expression: "StringFunctionRule.getUUID(StringFunctionRule_instance)"
            text: "getUUID()"
        - name: "projectguid"              # 外键关联：引用项目主键
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(sinsert_projectContext,\"data.CG_ProjectInfo.rowguid\")"
            text: "插入项目信息.CG_ProjectInfo.rowguid"
        - name: "biaoduanno"              # 当前迭代项字段
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_sectionContext,\"data.item.biaoduanno\")"
            text: "当前迭代.item.biaoduanno"
        - name: "biaoduanname"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_sectionContext,\"data.item.biaoduanname\")"
            text: "当前迭代.item.biaoduanname"
        - name: "touzigusuan"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_sectionContext,\"data.item.touzigusuan\")"
            text: "当前迭代.item.touzigusuan"
  id: "insert_section"
  parentId: "iteration_section"
```

### 步骤 6.2：嵌套迭代行项目数组

**⚠️ 嵌套迭代配置说明**：
- 嵌套迭代必须设置 `isInIteration: true` 和 `iteration_id`（指向父迭代节点ID）
- 必须设置 `parentId` 指向父迭代节点ID
- 其他必需字段与普通迭代节点相同

```yaml
# 嵌套迭代节点主体
- data:
    error_handle_mode: "terminated"
    isInIteration: true              # 标识在父迭代中（必填）
    start_node_id: "iteration_lineitem_start"
    type: "iteration"
    title: "迭代行项目信息"
    iteration_id: "iteration_section"  # 父迭代节点ID（必填）
    output_selector: []
    iterator_selector:
    - "iteration_section"           # 引用父迭代节点
    - "item"                        # 当前迭代项
    - "lineiteminfo"                # 子数组字段
    width: 425
    is_parallel: false
    parallel_nums: 10
    isInLoop: false                  # 注意：嵌套迭代内部为false
    height: 152
    resultType: 0
  id: "iteration_lineitem"
  parentId: "iteration_section"      # 指向父迭代节点（必填）
  zIndex: -12998                     # 层级索引

# 嵌套迭代开始节点
- data:
    isInIteration: true
    title: ""
    type: "iteration-start"
  selectable: false
  sourcePosition: "right"
  type: "custom-iteration-start"
  parentId: "iteration_lineitem"    # 指向当前迭代节点
  draggable: false
  targetPosition: "left"
  width: 44
  id: "iteration_lineitem_start"
  zIndex: 1002
  height: 48
```

### 步骤 6.2.1：插入行项目表

```yaml
- data:
    type: "biz-action"
    title: "插入行项目信息"
    isInIteration: true
    iteration_id: "iteration_lineitem"
    actionData:
      panelPath: "frame-datasource/data-insert"
      action: "misaddaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "PR_PRLineItem"
      - name: "entities"
        valueMode: "fixed"
        value:
        - name: "lineitemguid"
          valueMode: "formula"
          formula:
            expression: "StringFunctionRule.getUUID(StringFunctionRule_instance)"
            text: "getUUID()"
        - name: "biaoduanguid"          # 外键关联：引用标段主键
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(sinsert_sectionContext,\"data.CG_BiaoDuanInfo.biaoduanguid\")"
            text: "插入标段信息.CG_BiaoDuanInfo.biaoduanguid"
        - name: "lineitemno"            # 当前迭代项字段
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_lineitemContext,\"data.item.lineitemno\")"
            text: "当前迭代.item.lineitemno"
        - name: "itemno"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_lineitemContext,\"data.item.itemno\")"
        - name: "num"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_lineitemContext,\"data.item.num\")"
        - name: "unitprice"
          valueMode: "formula"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_lineitemContext,\"data.item.unitprice\")"
  id: "insert_lineitem"
  parentId: "iteration_lineitem"
```

### 步骤 7：返回成功结果

**⚠️ 结束节点配置说明**：
- `responseParams` 的根元素必须包含 `showName`、`ParentTaskUID: -1`、`required: true`
- 每个子元素必须包含 `UID`、`showName`、`ParentTaskUID`、`required`
- Webhook触发模式必须配置 `trigerType: "webhook"`
- 详细配置规范请参考[结束节点文档](../节点/结束节点/结束.md)

```yaml
- data:
    type: "end-vue"
    title: "返回成功"
    actionData:
      panelPath: "common/end"
      action: "end"
      formData:
      - name: "trigerType"          # 触发类型（必填）
        valueMode: "fixed"
        value: "webhook"
      - name: "responseParams"      # 响应参数（必填）
        valueMode: "fixed"
        value:
        - UID: "root"              # 根节点UID（必填）
          showName: "根节点"        # 根节点显示名称（必填）
          children:
          - UID: "C71934F9-A705-4675-9617-66359F6680F2"  # 子节点UID
            showName: ""           # 子节点显示名称
            name: "code"
            ParentTaskUID: "root"  # 父节点UID（必填）
            type: "STRING"
            required: true          # 是否必填（必填）
            defaultValue:
              valueMode: "fixed"
              value: "1"
          - UID: "BE7DA050-6D98-4C9F-B320-895D3DA9A671"
            showName: ""
            name: "msg"
            ParentTaskUID: "root"
            type: "STRING"
            required: true
            defaultValue:
              valueMode: "fixed"
              value: "采购立项信息插入成功"
          - UID: "A6127C4E-F88B-4E54-9645-09866A45382F"
            showName: ""
            name: "projectguid"
            ParentTaskUID: "root"
            type: "STRING"
            required: true
            defaultValue:
              valueMode: "formula"
              formula:
                expression: "RuleParamUtil.parserParam(sinsert_projectContext,\"data.CG_ProjectInfo.rowguid\")"
                text: "插入项目信息.CG_ProjectInfo.rowguid"
          defaultValue:              # 根节点默认值配置（必填）
            valueMode: "formula"
            value: ""
          name: "根节点"             # 根节点名称（必填）
          ParentTaskUID: -1         # 根节点父ID固定为-1（必填）
          type: "OBJECT"
          required: true             # 根节点必填标识（必填）
  id: "end_success"
```

## 关键技术点

1. **嵌套迭代的数据引用**
   - 父迭代节点ID：`iteration_section`
   - 子迭代数据路径：`iteration_section.item.lineiteminfo`
   - 子迭代中访问父迭代数据：通过`iteration_section.item`访问父级当前项

2. **外键关联的实现**
   - 项目→标段：`insert_project.CG_ProjectInfo.rowguid` → `biaoduanguid`
   - 标段→行项目：`insert_section.CG_BiaoDuanInfo.biaoduanguid` → `biaoduanguid`

3. **变量引用路径**
   - Webhook数据：`swebhook_nodeContext.data.body.projectinfo.xxx`
   - 迭代当前项：`siteration_sectionContext.data.item.xxx`
   - 插入结果：`sinsert_projectContext.data.CG_ProjectInfo.xxx`

4. **迭代节点连线配置**（重要）
   - **主迭代连线**（迭代节点 → 后续节点）：
     - `sourceHandle: "source"`（注意：不是 `"true"`）
     - `data.isInLoop: true`
     - `data.loop_id: "迭代节点ID"`
   - **迭代开始连线**（迭代开始节点 → 首个内部节点）：
     - `sourceHandle: "source"`
     - `data.isInLoop: false`（特殊！注意与主迭代连线不同）
     - `data.isInIteration: true`
     - `data.iteration_id: "迭代节点ID"`
     - `zIndex: 1003`
   - **迭代内部连线**（内部节点 → 内部节点）：
     - `data.isInLoop: true`
     - `data.isInIteration: true`
     - `data.iteration_id: "迭代节点ID"`
     - `data.loop_id: "迭代节点ID"`
   - 详细连线规范请参考[迭代节点文档](../节点/逻辑节点/迭代.md#连线配置)