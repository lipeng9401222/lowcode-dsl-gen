# 场景二：多表联查数据输出（Pull模式）

## 业务需求

接收第三方查询请求，根据标段编号和时间范围查询评标结果信息，包括标段信息、中标公示、投标单位、中标单位等多表数据，组合后返回。

## 典型应用

- 评标结果查询接口
- 业务数据对外输出
- 多表关联查询场景
- 数据权限控制查询

## 数据结构

**请求参数：**

```json
{
  "token": "xxxxx",
  "biaoduanno": "BD001",
  "fromdate": "2024-01-01",
  "enddate": "2024-12-31"
}
```

**返回数据：**

```json
{
  "code": "1",
  "msg": {
    "biaoduaninfo": {
      "biaoduanguid": "xxx-guid",
      "biaoduanno": "BD001",
      "biaoduanname": "标段1",
      "projectno": "PRJ001",
      "projectname": "项目名称"
    },
    "zhongbiaodanwei": {
      "danweiguid": "xxx-guid",
      "danweiname": "中标单位",
      "zhongbiaoprice": 1000000,
      "pmname": "项目经理"
    },
    "bidder": [
      {
        "danweiname": "投标单位1",
        "kaibiaoprice": 1050000,
        "huizongmark": 85.5
      },
      {
        "danweiname": "投标单位2",
        "kaibiaoprice": 1020000,
        "huizongmark": 83.2
      }
    ]
  }
}
```

## 工作流设计

```
1. Webhook 接收查询请求
   ↓
2. 条件判断：参数验证（biaoduanno、时间）
   ↓ 不通过                    ↓ 通过
   返回错误信息                继续
   ↓
3. 条件判断：时间范围验证（fromdate <= enddate）
   ↓ 不通过                    ↓ 通过
   返回"时间范围错误"           继续
   ↓
4. 查询标段信息表（根据biaoduanno）
   ↓
5. 条件判断：标段是否存在
   ↓ 不存在                    ↓ 存在
   返回"标段不存在"            继续
   ↓
6. 查询中标公示关联表（根据biaoduanguid）
   ↓
7. 查询中标公示主表（根据GongGaoGuid + 审核状态）
   ↓
8. 条件判断：中标公示是否存在
   ↓ 不存在                    ↓ 存在
   返回"中标公示未发布"         继续
   ↓
9. 查询投标单位列表（根据biaoduanguid）
   ↓
10. 查询中标单位详情（根据biaoduanguid + IsZhongBiao=1）
   ↓
11. 返回组合结果
```

## 核心设计要点

1. **多层参数验证**：按优先级验证参数，提前返回错误，减少无效查询
2. **关联查询**：通过外键逐层查询相关数据
3. **业务状态验证**：查询时加入业务状态条件（如审核通过）
4. **数据组合输出**：将多个查询结果组合成业务需要的数据结构
5. **空值处理**：对不存在的数据返回明确的错误信息

## 详细配置

### 步骤 1：Webhook 接收查询请求

```yaml
- data:
    actionData:
      panelPath: "frame-webhook/frame-webhook"
      action: "webhookdetail"
      category: "webHook"
      formData:
      - name: "request"
        value:
          requestBody:
          - UID: "root"
            name: "根节点"
            type: "OBJECT"
            children:
            - name: "token"
              type: "STRING"
              required: true
            - name: "biaoduanno"
              type: "STRING"
              required: true
            - name: "fromdate"
              type: "DATE"
              required: true
            - name: "enddate"
              type: "DATE"
              required: true
    type: "start"
    title: "Webhook触发"
  id: "webhook_node"
```

### 步骤 2：验证必填参数

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
        - "biaoduanno"
        comparison_operator: "empty"
    - logical_operator: "or"
      case_id: "case2"
      conditions:
      - varType: "date"
        variable_selector:
        - "webhook_node"
        - "body"
        - "fromdate"
        comparison_operator: "empty"
      - varType: "date"
        variable_selector:
        - "webhook_node"
        - "body"
        - "enddate"
        comparison_operator: "empty"
    type: "if-else"
    title: "条件分支：参数验证"
  id: "check_params"
```

### 步骤 3：验证时间范围（高级条件判断）

```yaml
- data:
    type: "if-else-vue"
    title: "条件分支(高级)：时间范围验证"
    actionData:
      panelPath: "common/if-else"
      formData:
      - name: "IF"
        value:
          name: "and"
          type: "group"
          items:
          - opt: ">="
            left:
            - dataType: "date"
              label: "Webhook触发.body.fromdate"
              type: "field"
              value: "swebhook_nodeContext.data.body.fromdate"
            right:
            - dataType: "date"
              label: "Webhook触发.body.enddate"
              type: "field"
              value: "swebhook_nodeContext.data.body.enddate"
  id: "check_daterange"
```

### 步骤 4：查询标段信息

```yaml
- data:
    type: "biz-action"
    title: "查询标段信息"
    actionData:
      panelPath: "frame-datasource/data-query-detail"
      action: "misfindaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_BiaoDuanInfo"
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
                label: "标段(包)编号"
                type: "tableField"
                value: "BIAODUANNO"
              right:
              - dataType: "string"
                label: "Webhook触发.body.biaoduanno"
                type: "field"
                value: "swebhook_nodeContext.data.body.biaoduanno"
          type: "simple"
      - name: "queryFields"
        valueMode: "fixed"
        value:
        - name: "biaoduanguid"
          tableId: 201004          # ⚠️ 必填：数据表ID（从query_table获取）
          label: "标段唯一标识"
          type: "string"
        - name: "BIAODUANNO"
          tableId: 201004
          label: "标段(包)编号"
          type: "string"
        - name: "BIAODUANNAME"
          tableId: 201004
          label: "标段(包)名称"
          type: "string"
        - name: "projectno"
          tableId: 201004
          label: "项目编号"
          type: "string"
        - name: "projectname"
          tableId: 201004
          label: "项目名称"
          type: "string"
        - name: "TOUZIGUSUAN"
          tableId: 201004
          label: "合同预算价(万元)"
          type: "int"
  id: "query_biaoduaninfo"
```

### 步骤 5：判断标段是否存在

```yaml
- data:
    cases:
    - logical_operator: "and"
      case_id: "true"
      conditions:
      - varType: "object"
        variable_selector:
        - "query_biaoduaninfo"
        - "CG_BiaoDuanInfo"
        comparison_operator: "empty"
    type: "if-else"
    title: "条件判断：标段是否存在"
  id: "check_biaoduan_exists"
```

### 步骤 6：查询中标公示唯一标识

```yaml
- data:
    type: "biz-action"
    title: "查询中标公示唯一标识"
    actionData:
      panelPath: "frame-datasource/data-query-detail"
      action: "misfindaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_ZBGSAndBD"
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
                label: "标段唯一标识"
                type: "tableField"
                value: "BiaoDuanGuid"
              right:
              - dataType: "string"
                label: "查询标段信息.CG_BiaoDuanInfo.标段唯一标识"
                type: "field"
                value: "squery_biaoduaninfoContext.data.CG_BiaoDuanInfo.biaoduanguid"
          type: "simple"
      - name: "queryFields"
        valueMode: "fixed"
        value:
        - name: "GongGaoGuid"
          tableId: 201062          # ⚠️ 必填：数据表ID（从query_table获取）
          label: "中标公示唯一标识"
          type: "string"
  id: "query_zbgs_guid"
```

### 步骤 7：查询中标公示信息（含审核状态验证）

```yaml
- data:
    type: "biz-action"
    title: "查询中标公示信息"
    actionData:
      panelPath: "frame-datasource/data-query-detail"
      action: "misfindaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_ZhongBiaoGS"
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
                label: "默认主键字段"
                type: "tableField"
                value: "RowGuid"
              right:
              - dataType: "string"
                label: "查询中标公示唯一标识.CG_ZBGSAndBD.GongGaoGuid"
                type: "field"
                value: "squery_zbgs_guidContext.data.CG_ZBGSAndBD.GongGaoGuid"
            - opt: "=="
              left:
              - dataType: "string"
                label: "是否审核通过"
                type: "tableField"
                value: "AuditStatus"
              right:
              - dataType: ""
                label: "固定值"
                type: "fix"
                value: "3"              # 审核通过状态
          type: "simple"
      - name: "queryFields"
        valueMode: "fixed"
        value:
        - name: "RowGuid"
          tableId: 201061          # ⚠️ 必填：数据表ID（从query_table获取）
          label: "默认主键字段"
          type: "string"
        - name: "GSFromDate"
          tableId: 201061
          label: "公示开始日期"
          type: "datetime"
        - name: "GSToDate"
          tableId: 201061
          label: "公示结束时间"
          type: "datetime"
        - name: "DingBiaoDate"
          tableId: 201061
          label: "定标日期"
          type: "datetime"
  id: "query_zbgs_info"
```

### 步骤 8：判断中标公示是否存在

```yaml
- data:
    cases:
    - logical_operator: "and"
      case_id: "true"
      conditions:
      - varType: "object"
        variable_selector:
        - "query_zbgs_info"
        - "CG_ZhongBiaoGS"
        comparison_operator: "empty"
    type: "if-else"
    title: "条件分支：中标公示是否存在"
  id: "check_zbgs_exists"
```

### 步骤 9：查询投标单位列表

```yaml
- data:
    type: "biz-action"
    title: "查询投标单位数据"
    actionData:
      panelPath: "frame-datasource/data-query-list"
      action: "misfindlistaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_TouBiaoDanWei"
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
                label: "标段标识"
                type: "tableField"
                value: "BiaoDuanGuid"
              right:
              - dataType: "string"
                label: "查询标段信息.CG_BiaoDuanInfo.标段唯一标识"
                type: "field"
                value: "squery_biaoduaninfoContext.data.CG_BiaoDuanInfo.biaoduanguid"
          type: "simple"
      - name: "queryFields"
        valueMode: "fixed"
        value:
        - name: "DanWeiName"
          tableId: 201014          # ⚠️ 必填：数据表ID（从query_table获取）
          label: "单位名称"
          type: "string"
        - name: "kaibiaoprice"
          tableId: 201014
          label: "开标报价"
          type: "string"
        - name: "HuiZongMark"
          tableId: 201014
          label: "汇总分"
          type: "int"
        - name: "IsFeiBiao"
          tableId: 201014
          label: "是否废标"
          type: "string"
      - name: "pageIndex"
        valueMode: "fixed"
        value: 1
      - name: "pageSize"
        valueMode: "fixed"
        value: 0                    # 0表示查询全部
  id: "query_bidder_list"
```

### 步骤 10：查询中标单位详情

```yaml
- data:
    type: "biz-action"
    title: "查询中标单位数据"
    actionData:
      panelPath: "frame-datasource/data-query-detail"
      action: "misfindaction"
      formData:
      - name: "sqlTableName"
        valueMode: "fixed"
        value: "CG_TouBiaoDanWei"
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
                label: "标段标识"
                type: "tableField"
                value: "BiaoDuanGuid"
              right:
              - dataType: "string"
                label: "查询标段信息.CG_BiaoDuanInfo.标段唯一标识"
                type: "field"
                value: "squery_biaoduaninfoContext.data.CG_BiaoDuanInfo.biaoduanguid"
            - opt: "=="
              left:
              - dataType: "string"
                label: "是否中标"
                type: "tableField"
                value: "IsZhongBiao"
              right:
              - dataType: ""
                label: "固定值"
                type: "fix"
                value: "1"              # 中标状态
          type: "simple"
      - name: "queryFields"
        valueMode: "fixed"
        value:
        - name: "DanWeiGuid"
          tableId: 201014          # ⚠️ 必填：数据表ID（从query_table获取）
          label: "单位唯一编号"
          type: "string"
        - name: "DanWeiName"
          tableId: 201014
          label: "单位名称"
          type: "string"
        - name: "zhongbiaoprice"
          tableId: 201014
          label: "中标价格"
          type: "int"
        - name: "PMName"
          tableId: 201014
          label: "项目经理姓名"
          type: "string"
        - name: "GongQi"
          tableId: 201014
          label: "工期"
          type: "int"
  id: "query_winner"
```

### 步骤 11：返回组合结果

```yaml
- data:
    type: "end-vue"
    title: "正常结束"
    actionData:
      panelPath: "common/end"
      action: "end"
      formData:
      - name: "trigerType"
        valueMode: "fixed"
        value: "webhook"
      - name: "responseParams"
        valueMode: "fixed"
        value:
        - UID: "root"
          name: "根节点"
          type: "OBJECT"
          children:
          - name: "code"
            type: "STRING"
            defaultValue:
              valueMode: "fixed"
              value: "1"
          - name: "msg"
            type: "OBJECT"
            children:
            - name: "biaoduaninfo"
              type: "STRING"
              defaultValue:
                valueMode: "formula"
                formula:
                  expression: "RuleParamUtil.parserParam(squery_biaoduaninfoContext,\"data.CG_BiaoDuanInfo\")"
                  text: "查询标段信息.CG_BiaoDuanInfo"
            - name: "zhongbiaodanwei"
              type: "STRING"
              defaultValue:
                valueMode: "formula"
                formula:
                  expression: "RuleParamUtil.parserParam(squery_winnerContext,\"data.CG_TouBiaoDanWei\")"
                  text: "查询中标单位数据.CG_TouBiaoDanWei"
            - name: "bidder"
              type: "STRING"
              defaultValue:
                valueMode: "formula"
                formula:
                  expression: "RuleParamUtil.parserParam(squery_bidder_listContext,\"data.CG_TouBiaoDanWei\")"
                  text: "查询投标单位数据.CG_TouBiaoDanWei"
  id: "end_success"
```

## 关键技术点

1. **多层条件验证模式**
   - 第一层：必填参数验证（为空即返回）
   - 第二层：业务逻辑验证（时间范围）
   - 第三层：数据存在性验证（标段、公示）

2. **关联查询链**
   ```
   标段编号 → 标段GUID → 公示关联表 → 公示GUID → 中标公示详情
                    ↓
                投标单位列表、中标单位
   ```

3. **业务状态过滤**
   - 查询中标公示时加入 `AuditStatus = 3`（审核通过）
   - 查询中标单位时加入 `IsZhongBiao = 1`（中标状态）

4. **数据组合输出**
   - 将多个查询结果组合成一个业务对象
   - 使用formula引用不同节点的查询结果