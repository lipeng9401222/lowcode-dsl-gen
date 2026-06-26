# LLM 节点 (llm)

## 概述

LLM 节点用于调用大语言模型进行文本生成、对话、推理等任务。支持标准模式和流式处理模式,可配置模型参数、提示模板、重试策略等。

## 节点配置

### 标准版本

```yaml
data:
  variables: []
  memoryreduction: false          # 内存缩减
  type: "llm"                     # 节点类型
  title: "LLM"                    # 节点标题
  retry_config:                   # 重试配置
    max_retries: 8                # 最大重试次数
    retry_enabled: false          # 是否启用重试
    retry_interval: 1000          # 重试间隔(毫秒)
  tokenstatistics: false          # 令牌统计
  vision:                         # 视觉配置
    enabled: false                # 是否启用视觉
  context:                        # 上下文配置
    variable_selector: []         # 变量选择器
    enabled: false                # 是否启用上下文
  model:                          # 模型配置
    mode: "chat"                  # 模式：chat/completion
    completion_params:            # 完成参数
      history_times: 20           # 历史记录次数
      temperature: 0.7            # 温度参数
    provider: ""                  # 模型提供者
    name: ""                      # 模型名称
  is_model_formula: "固定值"       # 模型公式类型
  selected: false                 # 是否选中
  desc: ""                        # 节点描述
  prompt_template:                # 提示模板
  - role: "system"                # 角色：system/user/assistant
    text: ""                      # 提示文本
```

### 流式处理版本

```yaml
data:
  variables: []
  json_check: false               # JSON检查
  type: "llm"                     # 节点类型
  title: "LLM"                    # 节点标题
  retry_config:                   # 重试配置
    max_retries: 8                # 最大重试次数
    retry_enabled: false          # 是否启用重试
    retry_interval: 1000          # 重试间隔(毫秒)
  vision:                         # 视觉配置
    enabled: false                # 是否启用视觉
  is_flow: true                   # 是否启用流式处理
  context:                        # 上下文配置
    variable_selector: []         # 变量选择器
    enabled: false                # 是否启用上下文
  model:                          # 模型配置
    completion_params:            # 完成参数
      history_times: 20           # 历史记录次数
      temperature: 0.7            # 温度参数
    provider: "langgenius/..."    # 模型提供者
    name: "千问2.5-代理"           # 模型名称
  is_model_formula: "固定值"       # 模型公式类型
  selected: false                 # 是否选中
  desc: ""                        # 节点描述
  prompt_template:                # 提示模板
    edition_type: "basic"         # 编辑类型
    text: "任务：请在不改变原文意思的基础上，对以下文章进行缩写..."  # 提示文本
```

## 字段说明

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 节点类型，固定为 "llm" |
| title | string | 节点显示标题 |
| is_flow | boolean | 是否启用流式处理（流式版本特有） |
| json_check | boolean | 是否检查JSON格式（流式版本） |
| memoryreduction | boolean | 是否启用内存缩减（标准版本） |
| tokenstatistics | boolean | 是否统计令牌使用（标准版本） |

### 重试配置 (retry_config)

```yaml
retry_config:
  max_retries: 8          # 最大重试次数
  retry_enabled: false    # 是否启用重试
  retry_interval: 1000    # 重试间隔(毫秒)
```

| 字段 | 类型 | 说明 | 推荐值 |
|------|------|------|--------|
| retry_enabled | boolean | 是否启用重试 | true（生产环境） |
| max_retries | number | 最大重试次数 | 3-8 次 |
| retry_interval | number | 重试间隔（毫秒） | 1000-5000 |

### 模型配置 (model)

```yaml
model:
  mode: "chat"                    # 模式
  provider: "langgenius/..."      # 提供者
  name: "千问2.5-代理"             # 模型名称
  completion_params:              # 完成参数
    history_times: 20             # 历史记录次数
    temperature: 0.7              # 温度参数
```

| 字段 | 类型 | 说明 | 可选值 |
|------|------|------|--------|
| mode | string | 模型模式 | "chat"（对话）/ "completion"（补全） |
| provider | string | 模型提供者 | 根据实际配置 |
| name | string | 模型名称 | 根据提供者支持的模型 |

### 完成参数 (completion_params)

| 字段 | 类型 | 说明 | 范围 |
|------|------|------|------|
| temperature | number | 温度参数，控制生成的随机性 | 0.0-2.0 |
| history_times | number | 保留的历史对话轮数 | 1-50 |

**温度参数说明**：
- `0.0-0.3`：更确定性，适合事实性任务
- `0.4-0.7`：平衡创造性和准确性
- `0.8-1.0`：更有创造性，适合写作任务
- `1.0+`：高度随机，很少使用

### 视觉配置 (vision)

```yaml
vision:
  enabled: false          # 是否启用视觉功能
```

启用后可以处理图片输入，需要模型支持多模态能力。

### 上下文配置 (context)

```yaml
context:
  enabled: false          # 是否启用上下文
  variable_selector: []   # 上下文变量选择器
```

用于引入知识库检索结果或其他上下文信息。

### 提示模板 (prompt_template)

#### 标准版本（多角色）

```yaml
prompt_template:
- role: "system"
  text: "你是一个专业的AI助手"
- role: "user"
  text: "{{#1768549737010.body.text#}}"
```

#### 流式版本（单文本）

```yaml
prompt_template:
  edition_type: "basic"   # 编辑类型
  text: "任务：{{#1768549737010.body.text#}}"
```

**角色类型**：
| 角色 | 说明 | 用途 |
|------|------|------|
| system | 系统消息 | 定义AI的行为和角色 |
| user | 用户消息 | 用户输入或任务描述 |
| assistant | 助手消息 | AI的历史回复（多轮对话） |

## 变量引用

### 在提示词中引用前置节点

```yaml
# 引用 Webhook 节点的输入
text: "请处理以下内容：{{#1768549737010.body.text#}}"

# 引用知识检索结果
text: "基于以下知识：{{#1768549749730.result#}}\n回答问题：{{#1768549737010.body.question#}}"

# 引用代码节点输出
text: "数据处理结果：{{#1768549742985.result#}}"
```

### 引用 LLM 节点输出

后续节点引用 LLM 输出：

```yaml
# 标准引用
{{#LLM节点ID.text#}}

# 在代码中引用
variables:
- variable: "llm_result"
  value_selector: "{{#1768549740849.text#}}"
```

## 配置示例

### 场景一：文本缩写

```yaml
data:
  type: "llm"
  title: "文本缩写"
  is_flow: true                   # 启用流式处理
  model:
    provider: "langgenius/qwen"
    name: "千问2.5-代理"
    completion_params:
      temperature: 0.3            # 低温度，保证准确性
      history_times: 5
  prompt_template:
    edition_type: "basic"
    text: |
      任务：请在不改变原文意思的基础上，对以下文章进行缩写，将字数压缩到原来的50%。
      
      原文：
      {{#1768549737010.body.text#}}
      
      要求：
      1. 保留核心观点和关键信息
      2. 删除冗余和次要内容
      3. 保持逻辑连贯
```

### 场景二：知识库问答

```yaml
data:
  type: "llm"
  title: "知识库问答"
  retry_config:
    retry_enabled: true           # 启用重试
    max_retries: 3
  context:
    enabled: true                 # 启用上下文
    variable_selector:
    - "{{#知识检索节点ID.result#}}"
  model:
    mode: "chat"
    name: "gpt-4"
    completion_params:
      temperature: 0.5
      history_times: 10
  prompt_template:
  - role: "system"
    text: "你是一个专业的客服助手，基于提供的知识库内容回答用户问题。"
  - role: "user"
    text: |
      知识库内容：
      {{#1768549749730.result#}}
      
      用户问题：
      {{#1768549737010.body.question#}}
      
      请基于知识库内容准确回答问题，如果知识库中没有相关信息，请明确告知。
```

### 场景三：JSON 生成

```yaml
data:
  type: "llm"
  title: "JSON生成"
  json_check: true                # 启用JSON检查
  model:
    name: "gpt-4"
    completion_params:
      temperature: 0.2            # 低温度确保格式稳定
      history_times: 1
  prompt_template:
  - role: "system"
    text: "你是一个JSON生成器，只返回有效的JSON格式数据，不要添加任何其他文字。"
  - role: "user"
    text: |
      将以下信息转换为JSON格式：
      {{#1768549737010.body.data#}}
      
      要求的JSON结构：
      {
        "name": "姓名",
        "age": 年龄（数字）,
        "email": "邮箱",
        "address": "地址"
      }
```

### 场景四：多轮对话

```yaml
data:
  type: "llm"
  title: "智能客服"
  model:
    mode: "chat"
    name: "gpt-3.5-turbo"
    completion_params:
      temperature: 0.7
      history_times: 20           # 保留20轮对话历史
  prompt_template:
  - role: "system"
    text: "你是一个友好、专业的客服助手。"
  - role: "user"
    text: "{{#1768549737010.body.message#}}"
```

### 场景五：代码生成

```yaml
data:
  type: "llm"
  title: "代码生成"
  model:
    name: "gpt-4"
    completion_params:
      temperature: 0.4
      history_times: 3
  prompt_template:
  - role: "system"
    text: |
      你是一个专业的程序员，精通多种编程语言。
      生成的代码要求：
      1. 清晰的注释
      2. 良好的代码风格
      3. 考虑错误处理
  - role: "user"
    text: |
      编程语言：{{#1768549737010.body.language#}}
      需求描述：{{#1768549737010.body.requirement#}}
      
      请生成满足需求的代码。
```

### 场景六：流式输出处理

```yaml
# LLM节点配置
data:
  type: "llm"
  title: "流式生成"
  is_flow: true                   # 启用流式处理
  model:
    name: "qwen-turbo"
    completion_params:
      temperature: 0.7
  prompt_template:
    edition_type: "basic"
    text: "{{#1768549737010.body.prompt#}}"

# 后续代码节点处理流式输出
---
data:
  type: "code"
  title: "流式输出拼接"
  code_language: "groovy"
  variables:
  - variable: "stream_output"
    value_selector: "{{#LLM节点ID.text#}}"
  code: |
    import com.epoint.rule.action.StreamingIterator
    
    def main(stream_output) {
        def list = []
        
        def chgline = { line ->
            list << line
            return line
        }
        
        def ret = new StreamingIterator(stream_output, chgline)
        ret.each { }
        
        return [
            result: list.join()
        ]
    }
```

## 流式处理

### 启用流式处理

设置 `is_flow: true` 启用流式处理模式：

```yaml
data:
  type: "llm"
  is_flow: true           # 启用流式处理
  # ... 其他配置
```

### 流式输出格式

流式输出以增量方式返回，每次返回一个片段：

```json
{"result": {"content": "这是"}}
{"result": {"content": "第一"}}
{"result": {"content": "段内容"}}
```

### 处理流式输出

使用代码节点的 `StreamingIterator` 处理：

```groovy
import com.epoint.rule.action.StreamingIterator
import groovy.json.JsonSlurper

def main(arg1) {
    def slurper = new JsonSlurper()
    
    // 解析每个JSON片段
    def chunks = arg1.collect { slurper.parseText(it) }
    
    // 拼接content
    def fullText = chunks
        .collect { it.result?.content }
        .findAll { it }
        .join()
    
    return [result: fullText]
}
```

## 最佳实践

### 1. 提示词设计

- **明确角色**：在 system 消息中明确定义 AI 的角色和能力边界
- **结构化输出**：使用清晰的格式要求（如 JSON、Markdown）
- **提供示例**：在提示词中包含期望的输出示例
- **分步指导**：将复杂任务分解为清晰的步骤

### 2. 模型选择

| 任务类型 | 推荐模型 | 温度参数 |
|----------|----------|----------|
| 事实查询、数据提取 | GPT-4, 千问 | 0.0-0.3 |
| 内容生成、总结 | GPT-3.5/4, 千问 | 0.3-0.7 |
| 创意写作、头脑风暴 | GPT-4, Claude | 0.7-1.0 |
| 代码生成 | GPT-4, Claude | 0.2-0.5 |

### 3. 重试策略

```yaml
# 生产环境推荐配置
retry_config:
  retry_enabled: true
  max_retries: 3              # 3次重试通常足够
  retry_interval: 2000        # 2秒间隔避免频繁请求
```

### 4. 上下文管理

```yaml
# 合理设置历史记录数
completion_params:
  history_times: 10           # 10轮对话足够保持上下文
  # 过多会增加token消耗和响应时间
```

### 5. 成本优化

- **选择合适的模型**：不是所有任务都需要 GPT-4
- **控制历史记录**：减少不必要的历史对话
- **优化提示词**：简洁明确，避免冗余
- **使用流式处理**：改善用户体验，不增加成本

### 6. 性能优化

- **启用流式处理**：对于长文本生成任务
- **并行调用**：多个独立的LLM任务可以并行执行
- **缓存结果**：对于相同的输入可以缓存输出

## 常见问题

### 1. 输出格式不稳定

**原因**：温度参数过高或提示词不够明确

**解决**：
- 降低 temperature 到 0.2-0.3
- 在提示词中明确输出格式
- 提供输出示例
- 启用 json_check（JSON输出场景）

### 2. Token 超限

**原因**：输入内容过长或历史记录过多

**解决**：
```yaml
# 减少历史记录
completion_params:
  history_times: 5            # 从20减少到5

# 或启用内存缩减
memoryreduction: true
```

### 3. 响应超时

**原因**：模型响应慢或网络问题

**解决**：
```yaml
# 启用重试
retry_config:
  retry_enabled: true
  max_retries: 3
  retry_interval: 3000        # 增加重试间隔

# 或使用更快的模型
model:
  name: "gpt-3.5-turbo"       # 代替 gpt-4
```

### 4. 输出质量不佳

**原因**：提示词设计问题或模型选择不当

**解决**：
- 优化提示词，提供更多上下文
- 使用更强大的模型
- 提供输出示例
- 分步骤拆解复杂任务

### 5. 流式输出处理失败

**原因**：未正确处理流式数据格式

**解决**：
```groovy
// 使用 StreamingIterator 正确处理
import com.epoint.rule.action.StreamingIterator

def main(stream_data) {
    def list = []
    
    def chgline = { line ->
        list << line
        return line
    }
    
    def ret = new StreamingIterator(stream_data, chgline)
    ret.each { }  // 触发处理
    
    return [result: list.join()]
}
```

## 注意事项

1. **API密钥安全**：确保模型提供者的API密钥安全存储
2. **成本控制**：监控token使用量，避免意外的高额费用
3. **内容审核**：对用户输入和AI输出进行必要的内容审核
4. **错误处理**：配置重试策略，处理模型服务不可用情况
5. **提示词注入**：防止用户输入中包含恶意提示词
6. **输出验证**：对关键业务逻辑，验证AI输出的正确性

## 相关文档

- [知识检索节点](知识检索节点.md) - 与LLM配合使用的知识库检索
- [代码节点](../转换节点/代码执行.md) - 处理LLM输出
- [流式处理配置](../基础结构/workflow配置.md) - 流式处理详解
- [变量引用规范](../基础结构/graph结构.md) - 变量引用方法
