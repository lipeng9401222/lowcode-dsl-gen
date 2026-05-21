# 场景三：定时数据同步与资产创建（Schedule模式）

## 业务需求

每月最后一天自动执行，从第三方系统获取增量的部门和用户数据，批量同步到我方系统的组织架构中。

## 典型应用

- 组织架构数据同步
- 用户信息定时同步
- 第三方系统数据集成
- 增量数据定时导入

## 工作流设计

```
1. 定时任务触发（每月最后一天）
   ↓
2. 获取当前日期 → 环境变量 nowdate
   ↓
3. 计算前一天日期 → 环境变量 fromdate
   ↓
4. 调用接口：获取增量部门数据（fromdate ~ nowdate）
   ↓
5. 条件判断：接口返回状态
   ↓ code != 200            ↓ code == 200
   返回失败信息             继续
   ↓
6. 迭代部门列表
   ↓
   6.1 新增部门（OuServiceImpl_addFrameOu）
   ↓
7. 调用接口：获取增量用户数据（fromdate ~ nowdate）
   ↓
8. 条件判断：接口返回状态
   ↓ code != 200            ↓ code == 200
   返回失败信息             继续
   ↓
9. 迭代用户列表
   ↓
   9.1 新增用户（UserServiceImpl_addFrameUser）
   ↓
10. 清除用户缓存（CacheMonitorUtil.clearByCacheName）
    ↓
11. 返回成功信息
```

## 核心设计要点

1. **定时触发配置**：使用定时任务节点,支持按月/周/日执行
2. **时间范围计算**：使用公式函数动态计算时间范围
3. **增量数据同步**：通过时间范围参数获取增量数据
4. **接口状态验证**：调用接口后验证返回状态,失败时终止流程
5. **批量资产创建**：使用迭代节点批量调用系统服务创建资产
6. **缓存管理**：批量操作后清除相关缓存,保证数据一致性

## 详细配置

### 步骤 1：定时任务触发

```yaml
- data:
    variables: []
    actionData:
      panelPath: "simple-timer/simple-timer"
      action: "simpleTimer"
      formData:
      - name: "frequency"
        valueMode: "fixed"
        value: 5                    # 5表示按月
      - name: "startTime"
        valueMode: "fixed"
        value: "2025-12-17 02:33"   # 开始时间
      - name: "frequencyData"
        valueMode: "fixed"
        value:
          monthWeek: []
          monthCheck: ["last"]      # 每月最后一天
          monthWeekDay: []
          monthType: 1
          lastWeek: []
      - name: "endTime"
        valueMode: "fixed"
        value: "2026-12-24 00:00"   # 结束时间
      - name: "month"
        valueMode: "fixed"
        value: []
      category: "timerOrSchedule"
    type: "start"
    title: "定时或指定时间触发"
  id: "timer_trigger"
```

### 步骤 2：获取当前日期

```yaml
- data:
    epoint_formula:
      "4d868a36-1156-41d8-a1ca-3024dce7854f":
        expression: "EpointDateUtil.getCurrentDate()"
        header: "use com.epoint.core.utils.date.EpointDateUtil;\r\n"
        text: "EpointDateUtil_getCurrentDate()"
        value:
        - fun: "EpointDateUtil_getCurrentDate"
        - "()"
    type: "assigner"
    title: "变量赋值 - 获取当前日期"
    version: "2"
    items:
    - write_mode: "over-write"
      variable_selector:
      - "env"
      - "nowdate"
      input_type: "variable"
      value: "{{@4d868a36-1156-41d8-a1ca-3024dce7854f@}}"
      operation: "over-write"
  id: "assign_nowdate"
```

### 步骤 3：计算前一天日期

```yaml
- data:
    epoint_formula:
      "f58b270b-8782-440e-ab8e-e984f4538f88":
        expression: "EpointDateUtil.convertDate2String(EpointDateUtil.addDay(EpointDateUtil.convertString2Date(RuleParamUtil.parserParam(nowdate,\"\"),\"yyyy-MM-dd\"),-1),\"yyyy-MM-dd\")"
        header: "use com.epoint.core.utils.date.EpointDateUtil;\r\n"
        text: "EpointDateUtil_convertDate2String(addDay(EpointDateUtil_convertString2Date(ENVIRONMENT.env.nowdate,'yyyy-MM-dd'),-1),'yyyy-MM-dd')"
        value:
        - fun: "EpointDateUtil_convertDate2String"
        - "("
        - fun: "addDay"
        - "("
        - fun: "EpointDateUtil_convertString2Date"
        - "("
        - name: "ENVIRONMENT.env.nowdate"
          id: "4e34e8c1-78ef-43fe-9bab-a2f308f89e61;senvContext.data.env.nowdate"
          value: "senvContext.data.env.nowdate"
        - "'yyyy-MM-dd'),-1),'yyyy-MM-dd')"
    type: "assigner"
    title: "变量赋值 - 计算前一天"
    version: "2"
    items:
    - write_mode: "over-write"
      variable_selector:
      - "env"
      - "fromdate"
      input_type: "variable"
      value: "{{@f58b270b-8782-440e-ab8e-e984f4538f88@}}"
      operation: "over-write"
  id: "assign_fromdate"
```

### 步骤 4：调用接口获取增量部门数据

```yaml
- data:
    type: "biz-action"
    title: "同步部门信息"
    actionData:
      panelPath: "frame-api/frame-api"
      action: "callapi"
      formData:
      - name: "url"
        valueMode: "fixed"
        value: "http://localhost:8080/EpointFrame/rest/dynamicapi/mockOuData"
      - name: "response"
        valueMode: "fixed"
        value:
          responseParams:
          - UID: "root"
            name: "根节点"
            type: "OBJECT"
            children:
            - name: "code"
              type: "STRING"
              defaultValue: "200"
            - name: "msg"
              type: "ARRAY"
              children:
              - name: "items"
                type: "OBJECT"
                children:
                - name: "ouguid"
                  type: "STRING"
                - name: "ouname"
                  type: "STRING"
                - name: "oushortname"
                  type: "STRING"
                - name: "parentouguid"
                  type: "STRING"
      - name: "request"
        valueMode: "fixed"
        value:
          requestHeaders:
          - defaultValue:
              valueMode: "fixed"
              value: "application/x-www-form-urlencoded; charset=UTF-8;"
            name: "Content-Type"
            type: "STRING"
          requestBody:
          - defaultValue:
              valueMode: "fixed"
              value: ""
            name: "type"
            type: "STRING"
            required: true
          - defaultValue:
              valueMode: "variable"
              value: "{{#env.fromdate#}}"   # 引用环境变量
            name: "fromdate"
            type: "STRING"
            required: true
          - defaultValue:
              valueMode: "variable"
              value: "{{#env.nowdate#}}"    # 引用环境变量
            name: "enddate"
            type: "STRING"
            required: true
          requestBodyType: "application/x-www-form-urlencoded"
      - name: "authType"
        valueMode: "fixed"
        value: "DEFAULTTOKENCONFIG"
      - name: "method"
        valueMode: "fixed"
        value: "POST"
      - name: "name"
        valueMode: "fixed"
        value: "三方接口模拟增量部门数据"
      - name: "identification"
        valueMode: "fixed"
        value: "mockOuData"
      category: "biz_action"
  id: "call_ou_api"
```

### 步骤 5：判断部门接口返回状态

```yaml
- data:
    cases:
    - logical_operator: "and"
      case_id: "true"
      conditions:
      - varType: "string"
        variable_selector:
        - "call_ou_api"
        - "response"
        - "body"
        - "code"
        comparison_operator: "is"
        value: "200"
    type: "if-else"
    title: "条件分支：检查部门接口状态"
  id: "check_ou_api"
```

### 步骤 6：迭代部门列表

```yaml
- data:
    iterator_selector:
    - "call_ou_api"
    - "response"
    - "body"
    - "msg"
    start_node_id: "iteration_ou_start"
    type: "iteration"
    title: "迭代部门列表"
    is_parallel: false
    error_handle_mode: "terminated"
  id: "iteration_ou"
```

### 步骤 6.1：新增部门（资产节点）

```yaml
- data:
    type: "biz-action"
    title: "新增部门"
    isInIteration: true
    iteration_id: "iteration_ou"
    actionData:
      panelPath: "common/biz-action"
      action: "OuServiceImpl_addFrameOu"    # 系统服务：新增部门
      formData:
      - name: "ou"
        valueMode: "fixed"
        value:
        - name: "ouguid"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_ouContext,\"data.item.ouguid\")"
            text: "当前迭代.item.ouguid"
            value:
            - name: "当前迭代.item"
              value: "siteration_ouContext.data.item"
            - ".ouguid"
          valueMode: "formula"
        - name: "ouname"
          formula:
            expression: "RuleParamUtil.parserParam(siteration_ouContext,\"data.item.ouname\")"
            text: "当前迭代.item.ouname"
          valueMode: "formula"
        - name: "parentouguid"
          valueMode: "fixed"
          value: ""
        - name: "oushortname"
          valueMode: "fixed"
          value: ""
      - name: "frameOuExtendInfo"
        valueMode: "fixed"
        value:
        - name: "ouguid"
          formula:
            text: "当前迭代.item.ouguid"
            value:
            - name: "当前迭代.item"
              value: "siteration_ouContext.data.item"
            - ".ouguid"
          valueMode: "formula"
      category: "biz_action"
  id: "add_ou"
  parentId: "iteration_ou"
```

### 步骤 7-9：同步用户数据（同部门逻辑）

```yaml
# 步骤 7：调用用户接口（类似步骤4）
- data:
    type: "biz-action"
    title: "同步用户信息"
    actionData:
      panelPath: "frame-api/frame-api"
      action: "callapi"
      formData:
      # ... 配置同步骤4，URL改为mockUserData
      - name: "url"
        value: "http://localhost:8080/EpointFrame/rest/dynamicapi/mockUserData"
      - name: "response"
        value:
          responseParams:
          - UID: "root"
            children:
            - name: "code"
              type: "STRING"
            - name: "msg"
              type: "ARRAY"
              children:
              - name: "items"
                type: "OBJECT"
                children:
                - name: "userguid"
                  type: "STRING"
                - name: "loginid"
                  type: "STRING"
                - name: "displayname"
                  type: "STRING"
                - name: "ouguid"
                  type: "STRING"
                - name: "mobile"
                  type: "STRING"
  id: "call_user_api"

# 步骤 8：判断用户接口状态（同步骤5）
- data:
    cases:
    - logical_operator: "and"
      case_id: "true"
      conditions:
      - varType: "string"
        variable_selector:
        - "call_user_api"
        - "response"
        - "body"
        - "code"
        comparison_operator: "is"
        value: "200"
    type: "if-else"
    title: "条件分支：检查用户接口状态"
  id: "check_user_api"

# 步骤 9：迭代用户列表
- data:
    iterator_selector:
    - "call_user_api"
    - "response"
    - "body"
    - "msg"
    start_node_id: "iteration_user_start"
    type: "iteration"
    title: "迭代用户列表"
    is_parallel: false
    error_handle_mode: "terminated"
  id: "iteration_user"

# 步骤 9.1：新增用户
- data:
    type: "biz-action"
    title: "新增用户"
    isInIteration: true
    iteration_id: "iteration_user"
    actionData:
      panelPath: "common/biz-action"
      action: "UserServiceImpl_addFrameUser"   # 系统服务：新增用户
      formData:
      - name: "user"
        valueMode: "fixed"
        value:
        - name: "userguid"
          formula:
            text: "当前迭代.item.userguid"
            value:
            - name: "当前迭代.item"
              value: "siteration_userContext.data.item"
            - ".userguid"
          valueMode: "formula"
        - name: "loginid"
          formula:
            text: "当前迭代.item.loginid"
            value:
            - name: "当前迭代.item"
              value: "siteration_userContext.data.item"
            - ".loginid"
          valueMode: "formula"
        - name: "displayname"
          formula:
            text: "当前迭代.item.displayname"
          valueMode: "formula"
        - name: "ouguid"
          formula:
            text: "当前迭代.item.ouguid"
          valueMode: "formula"
        - name: "mobile"
          formula:
            text: "当前迭代.item.mobile"
          valueMode: "formula"
        - name: "isenabled"
          valueMode: "fixed"
          value: "1"
      - name: "frameUserExtendInfo"
        valueMode: "fixed"
        value:
        - name: "userguid"
          formula:
            text: "当前迭代.item.userguid"
          valueMode: "formula"
      category: "biz_action"
  id: "add_user"
  parentId: "iteration_user"
```

### 步骤 10：清除缓存

```yaml
- data:
    epoint_formula:
      "727078be-389d-4d7d-952b-fb702a5d82f5":
        expression: "CacheMonitorUtil.clearByCacheName(\"frameuserservice\")"
        header: "use com.epoint.frame.cache.monitor.utils.CacheMonitorUtil;\r\n"
        text: "CacheMonitorUtil_clearByCacheName(\"frameuserservice\",null)"
        value:
        - fun: "CacheMonitorUtil_clearByCacheName"
        - "(\"frameuserservice\",null)"
    type: "assigner"
    title: "清除用户缓存"
    version: "2"
    items:
    - write_mode: "over-write"
      variable_selector:
      - "env"
      - "ouinfo"
      input_type: "variable"
      value: ""
      operation: "over-write"
  id: "clear_cache"
```

### 步骤 11：返回成功结果

```yaml
- data:
    type: "end-vue"
    title: "结束"
    actionData:
      panelPath: "common/end"
      action: "end"
      formData:
      - name: "trigerType"
        valueMode: "fixed"
        value: "biz"
      - name: "status"
        valueMode: "fixed"
        value: "success"
      - name: "reminderType"
        valueMode: "fixed"
        value: "none"
      - name: "reminderContent"
        valueMode: "fixed"
        value: ""
      - name: "block"
        valueMode: "fixed"
        value: "0"
  id: "end_success"
```

## 关键技术点

1. **定时触发配置**
   - `frequency: 5` - 按月执行
   - `monthCheck: ["last"]` - 每月最后一天
   - 支持设置开始/结束时间

2. **时间范围计算**
   ```groovy
   // 获取当前日期
   EpointDateUtil.getCurrentDate()
   
   // 计算前一天
   EpointDateUtil.convertDate2String(
     EpointDateUtil.addDay(
       EpointDateUtil.convertString2Date(nowdate, "yyyy-MM-dd"),
       -1
     ),
     "yyyy-MM-dd"
   )
   ```

3. **环境变量使用**
   - 存储：`variable_selector: ["env", "nowdate"]`
   - 引用：`{{#env.nowdate#}}`

4. **资产节点调用**
   - 新增部门：`OuServiceImpl_addFrameOu`
   - 新增用户：`UserServiceImpl_addFrameUser`
   - 这些是系统内置的服务接口

5. **缓存清除**
   ```groovy
   CacheMonitorUtil.clearByCacheName("frameuserservice")
   ```
   批量操作后必须清除相关缓存

6. **错误处理**
   - 接口调用后立即验证返回状态
   - 失败时终止流程并返回错误信息
   - 迭代节点的error_handle_mode设为terminated