# Workflow 配置详解

## 配置结构

```yaml
workflow:
  conversation_variables: []  # 对话变量
  environment_variables: []   # 环境变量
  name: "采购立项管理"         # 工作流名称（与 app.name 一致）
  sign: "caigoulixiangguanli"  # 动作流标识（与 app.sign 一致，位于 name 之后）
  features: {}                # 功能配置
  graph: {}                   # 图结构
  dependencies: []            # 依赖项
```

## Dependencies (依赖项)

```yaml
workflow:
  dependencies: []     # 工作流依赖的插件或服务
```

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| dependencies | array | 工作流依赖的外部插件或服务列表 | `["plugin_id_1", "plugin_id_2"]` |

## Features (功能配置)

### 完整配置示例

```yaml
workflow:
  features:
    text_to_speech:           # 文本转语音
      voice: ""               # 语音ID
      language: ""            # 语言代码
      enabled: false          # 是否启用
    speech_to_text:           # 语音转文本
      enabled: false          # 是否启用
    suggested_questions: []   # 建议问题
    retriever_resource:       # 知识库检索
      enabled: true           # 是否启用
    opening_statement: ""     # 开场白
    suggested_questions_after_answer:
      enabled: false          # 回答后建议问题
    sensitive_word_avoidance: # 敏感词过滤
      enabled: false          # 是否启用
    file_upload:              # 文件上传配置
      image:                  # 图片上传配置
        number_limits: 3      # 图片数量限制
        transfer_methods:     # 传输方式
        - "local_file"
        - "remote_url"
        enabled: false        # 是否启用图片上传
      allowed_file_types:     # 允许的文件类型
      - "image"
      number_limits: 3        # 文件数量限制
      allowed_file_extensions: # 允许的文件扩展名
      - ".JPG"
      - ".JPEG"
      - ".PNG"
      - ".GIF"
      - ".WEBP"
      - ".SVG"
      allowed_file_upload_methods: # 允许的文件上传方式
      - "local_file"
      - "remote_url"
      enabled: false          # 是否启用文件上传
```

### 功能配置说明

#### 1. 文本转语音 (text_to_speech)

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否启用文本转语音功能 |
| voice | string | 语音ID，指定使用的语音模型 |
| language | string | 语言代码，如 "zh-CN"、"en-US" |

#### 2. 语音转文本 (speech_to_text)

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否启用语音转文本功能 |

#### 3. 建议问题 (suggested_questions)

- 类型：数组
- 说明：在对话开始时显示的建议问题列表
- 示例：`["如何使用？", "有什么功能？"]`

#### 4. 知识库检索 (retriever_resource)

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否启用知识库检索功能 |

#### 5. 开场白 (opening_statement)

- 类型：字符串
- 说明：对话开始时的欢迎语
- 示例：`"您好！我是您的智能助手，有什么可以帮您？"`

#### 6. 回答后建议问题 (suggested_questions_after_answer)

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否在回答后显示建议问题 |

#### 7. 敏感词过滤 (sensitive_word_avoidance)

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否启用敏感词过滤功能 |

#### 8. 文件上传 (file_upload)

**图片上传配置 (image)**

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否启用图片上传 |
| number_limits | number | 图片数量限制 |
| transfer_methods | array | 传输方式：`local_file`(本地上传)、`remote_url`(远程URL) |

**文件上传配置**

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 是否启用文件上传 |
| number_limits | number | 文件数量限制 |
| allowed_file_types | array | 允许的文件类型：`image`、`document`、`video` 等 |
| allowed_file_extensions | array | 允许的文件扩展名列表 |
| allowed_file_upload_methods | array | 允许的上传方式 |

## 对话变量 (conversation_variables)

用于在对话过程中存储和传递数据。

```yaml
conversation_variables:
  - name: "user_name"
    type: "string"
    description: "用户名称"
```

## 环境变量 (environment_variables)

用于配置工作流运行时的环境参数。

```yaml
environment_variables:
  - name: "API_KEY"
    value: "your_api_key"
    description: "API密钥"
```

## 配置建议

1. **按需启用功能**：只启用实际需要的功能，避免不必要的资源消耗
2. **合理设置限制**：文件上传数量和大小要根据实际需求设置
3. **配置开场白**：提供友好的用户引导
4. **使用环境变量**：敏感信息使用环境变量管理，不要硬编码

## 相关文档

- [App 配置](./app配置.md)
- [Graph 结构](./graph结构.md)
- [三段式骨架](./三段式骨架.md)
- [字段约定](./字段约定.md)

## 顶层结构中 workflow 段的位置

在动作流 yml 的顶层结构中，`workflow` 段位于 `dependencies` 之后（参见 `assets/templates/event.yml` 权威模板）：

```yaml
type: event
app: { ... }
kind: "app"
version: "3.0"
dependencies: []
workflow:                    # ← workflow 段在此
  conversation_variables: []
  environment_variables: []
  features: { ... }
  graph:
    nodes: []
    edges: []
    viewport: { x: 0, y: 0, zoom: 0.7 }
```

### workflow 段完整字段总表

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| `conversation_variables` | array | ✅ | 对话变量（通常为空数组，**必须在第一位**） | `[]` |
| `environment_variables` | array | ✅ | 环境变量（通常为空数组，**必须在第二位**） | `[]` |
| `features` | object | ✅ | 流程级功能开关（详见上方 Features 配置） | `{ ... }` |
| `graph` | object | ✅ | 图结构（含 nodes / edges / viewport） | `{ nodes: [], edges: [], viewport: {} }` |

> ⚠️ `conversation_variables` 必须在 workflow 下第一位，`environment_variables` 必须在第二位。这是结构检查清单的硬约束。
