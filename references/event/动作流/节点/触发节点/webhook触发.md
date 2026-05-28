# Webhook 触发节点 (start)

## 概述

Webhook 触发节点是工作流的入口节点，用于接收外部 HTTP 请求触发工作流执行。

## 节点配置

```yaml
data:
  variables: []
  actionData:              # 动作数据
    panelPath: "frame-webhook/frame-webhook"  # 面板路径
    action: "webhookdetail"  # 动作名称
    formData:               # 表单数据
    - name: "webHookUrl"     # Webhook URL
      valueMode: "fixed"     # 值模式
      value: "http://127.0.0.1:8080/..."
    - name: "identification"  # 标识符
      valueMode: "fixed"
      value: "liushichuli"
    - name: "request"        # 请求配置
      valueMode: "fixed"
      value:
        requestHeaders: []   # 请求头
        requestBody:         # 请求体
        - UID: "..."
          showName: ""
          defaultValue: ""
          name: "text"
          ParentTaskUID: -1
          type: "STRING"
          required: true
        requestBodyType: "application/x-www-form-urlencoded"  # 请求体类型
    category: "webHook"      # 类别
  type: "start"             # 节点类型
  title: "Webhook触发"       # 节点标题
  isAction: true            # 是否为动作节点
  selected: false
  desc: ""
```

## 字段说明

### actionData 配置

| 字段 | 类型 | 说明 |
|------|------|------|
| panelPath | string | 面板路径，固定为 "frame-webhook/frame-webhook" |
| action | string | 动作名称，固定为 "webhookdetail" |
| category | string | 类别，固定为 "webHook" |

### formData 配置

#### 1. webHookUrl

Webhook 的完整 URL 地址。

```yaml
- name: "webHookUrl"
  valueMode: "fixed"
  value: "http://127.0.0.1:8080/api/workflow/trigger"
```

#### 2. identification

Webhook 的唯一标识符，用于识别不同的 Webhook。

```yaml
- name: "identification"
  valueMode: "fixed"
  value: "my_webhook_001"
```

#### 3. request

请求配置，包括请求头和请求体定义。

```yaml
- name: "request"
  valueMode: "fixed"
  value:
    requestHeaders: []     # 请求头配置
    requestBody: []        # 请求体字段定义
    requestBodyType: "application/x-www-form-urlencoded"  # 请求体类型
```

## 请求配置详解

### 请求头 (requestHeaders)

定义 Webhook 需要接收的 HTTP 请求头。

```yaml
requestHeaders:
- name: "Authorization"
  type: "STRING"
  required: true
  defaultValue: ""
- name: "Content-Type"
  type: "STRING"
  required: true
  defaultValue: "application/json"
```

### 请求体 (requestBody)

定义 Webhook 需要接收的请求体参数。

```yaml
requestBody:
- UID: "uuid-001"
  showName: "用户ID"
  defaultValue: ""
  name: "userId"
  ParentTaskUID: -1
  type: "STRING"
  required: true
- UID: "uuid-002"
  showName: "消息内容"
  defaultValue: ""
  name: "message"
  ParentTaskUID: -1
  type: "STRING"
  required: false
```

#### 请求体字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| UID | string | 字段唯一标识符 |
| name | string | 字段名称（用于变量引用） |
| showName | string | 字段显示名称 |
| type | string | 字段数据类型：STRING、NUMBER、BOOLEAN、OBJECT、ARRAY |
| required | boolean | 是否必填 |
| defaultValue | string | 默认值 |
| ParentTaskUID | number | 父任务ID，-1 表示根级字段 |

### 请求体类型 (requestBodyType)

| 类型 | 说明 |
|------|------|
| `application/json` | JSON 格式 |
| `application/x-www-form-urlencoded` | 表单格式 |
| `multipart/form-data` | 文件上传格式 |

## 变量引用

Webhook 触发节点的输出可以在后续节点中引用：

### 引用请求体参数

```yaml
# 格式
{{#节点ID.body.参数名#}}

# 示例
{{#1753410057316.body.text#}}
{{#1753410057316.body.userId#}}
```

### 在上下文中引用

```yaml
# 格式
s{节点ID}Context.data.body.{参数名}

# 示例
s1753410057316Context.data.body.text
s1753410057316Context.data.body.userId
```

### 引用请求头

```yaml
# 格式
s{节点ID}Context.data.headers.{请求头名称}

# 示例
s1753410057316Context.data.headers.Authorization
```

## 配置示例

### 场景一：简单文本接收

```yaml
requestBody:
- name: "text"
  type: "STRING"
  required: true
  showName: "文本内容"
requestBodyType: "application/x-www-form-urlencoded"
```

**调用示例**：
```bash
curl -X POST http://your-webhook-url \
  -d "text=Hello World"
```

### 场景二：JSON 对象接收

```yaml
requestBody:
- name: "user"
  type: "OBJECT"
  required: true
  showName: "用户信息"
- name: "userId"
  type: "STRING"
  required: true
  ParentTaskUID: "{user的UID}"
- name: "userName"
  type: "STRING"
  required: true
  ParentTaskUID: "{user的UID}"
requestBodyType: "application/json"
```

**调用示例**：
```bash
curl -X POST http://your-webhook-url \
  -H "Content-Type: application/json" \
  -d '{"user": {"userId": "123", "userName": "张三"}}'
```

### 场景三：数组数据接收

```yaml
requestBody:
- name: "items"
  type: "ARRAY"
  required: true
  showName: "数据列表"
requestBodyType: "application/json"
```

**调用示例**：
```bash
curl -X POST http://your-webhook-url \
  -H "Content-Type: application/json" \
  -d '{"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}'
```

## 最佳实践

1. **明确定义参数**：清晰定义所有需要接收的参数及其类型
2. **设置必填字段**：对关键参数设置 required: true
3. **使用合适的请求体类型**：
   - 简单表单数据：使用 `application/x-www-form-urlencoded`
   - 复杂对象/数组：使用 `application/json`
   - 文件上传：使用 `multipart/form-data`
4. **安全考虑**：
   - 使用请求头验证身份（如 Authorization）
   - 验证必填参数
   - 对敏感数据进行加密传输
5. **错误处理**：配置后续节点处理参数缺失或格式错误的情况

## 注意事项

1. Webhook 触发节点必须是工作流的第一个节点
2. 节点 ID 是唯一的，用于后续节点引用
3. 请求体字段的 UID 必须唯一
4. ParentTaskUID 用于构建嵌套结构，根级字段使用 -1

## 相关文档

- [条件判断节点](../控制节点/条件判断节点.md) - 验证 Webhook 参数
- [变量引用规范](../进阶指南/变量引用规范.md) - 变量引用详解
