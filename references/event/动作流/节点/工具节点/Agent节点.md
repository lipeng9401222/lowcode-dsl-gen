# Agent 节点 (agent)

## 概述

Agent 节点是一个智能代理节点，能够根据任务需求自主选择和调用工具、执行多步推理、完成复杂任务。与普通 LLM 节点不同，Agent 具有规划、决策和工具使用能力。

## 节点配置

```yaml
data:
  agent_parameters: {}        # Agent 参数配置
  type: "agent"              # 节点类型
  title: "Agent"             # 节点标题
  selected: false            # 是否选中
  desc: ""                   # 节点描述
```

## 字段说明

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 节点类型，固定为 "agent" |
| title | string | 节点显示标题 |
| agent_parameters | object | Agent 参数配置 |
| desc | string | 节点描述 |

### Agent 参数配置 (agent_parameters)

```yaml
agent_parameters:
  tools: []                          # 可用工具列表
  model:                             # 使用的模型
    provider: "openai"               # 模型提供者
    name: "gpt-4"                    # 模型名称
  max_iterations: 10                 # 最大迭代次数
  strategy: "react"                  # Agent 策略
  memory:                            # 记忆配置
    enabled: true                    # 是否启用记忆
    type: "buffer"                   # 记忆类型
  prompt:                            # 系统提示
    prefix: ""                       # 前置提示
    suffix: ""                       # 后置提示
```

#### 工具配置 (tools)

```yaml
tools:
- type: "calculator"                 # 工具类型
  name: "计算器"                     # 工具名称
  description: "执行数学计算"        # 工具描述
  config: {}                         # 工具配置
- type: "web_search"
  name: "网络搜索"
  description: "搜索互联网信息"
  config:
    api_key: ""
    max_results: 5
- type: "database_query"
  name: "数据库查询"
  description: "查询数据库"
  config:
    connection: "db-connection-id"
```

#### Agent 策略 (strategy)

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `react` | ReAct (Reasoning + Acting) 模式 | 需要推理和行动的任务 |
| `plan-and-execute` | 先规划再执行 | 复杂的多步骤任务 |
| `reflection` | 自我反思模式 | 需要自我改进的任务 |
| `function-calling` | 函数调用模式 | 简单的工具调用 |

#### 记忆配置 (memory)

```yaml
memory:
  enabled: true                      # 是否启用记忆
  type: "buffer"                     # 记忆类型
  max_tokens: 2000                   # 最大令牌数
  window_size: 5                     # 窗口大小（对话轮数）
```

**记忆类型**：
| 类型 | 说明 |
|------|------|
| `buffer` | 缓冲记忆，保留最近的对话 |
| `summary` | 摘要记忆，对历史进行摘要 |
| `entity` | 实体记忆，记住关键实体信息 |
| `knowledge_graph` | 知识图谱记忆 |

## 变量引用

### 引用 Agent 输出

```yaml
# 标准引用格式
{{#Agent节点ID.result#}}

# 引用具体字段
{{#Agent节点ID.result.answer#}}
{{#Agent节点ID.result.steps#}}
{{#Agent节点ID.result.tools_used#}}

# 在 LLM 节点中使用
prompt_template:
  text: "Agent的分析结果是：{{#1768549742985.result#}}"

# 在代码节点中使用
variables:
- variable: "agent_result"
  value_selector: "{{#1768549742985.result#}}"
```

### 上下文引用

```groovy
// 在代码节点中访问
s1768549742985Context.data.result
s1768549742985Context.data.steps
```

## Agent 输出格式

Agent 节点的输出通常包含以下信息：

```json
{
  "result": {
    "answer": "最终答案",
    "steps": [
      {
        "step": 1,
        "thought": "我需要先搜索相关信息",
        "action": "web_search",
        "action_input": "搜索关键词",
        "observation": "搜索结果..."
      },
      {
        "step": 2,
        "thought": "基于搜索结果，我需要计算",
        "action": "calculator",
        "action_input": "1234 * 5678",
        "observation": "7006652"
      }
    ],
    "tools_used": ["web_search", "calculator"],
    "iterations": 2,
    "final_thought": "综合分析得出结论"
  }
}
```

## 配置示例

### 场景一：简单 Agent（基础配置）

```yaml
data:
  type: "agent"
  title: "智能助手"
  agent_parameters:
    model:
      provider: "openai"
      name: "gpt-4"
    max_iterations: 5
    strategy: "function-calling"
    tools:
    - type: "calculator"
      name: "计算器"
      description: "执行数学计算，支持加减乘除等基本运算"
    memory:
      enabled: false              # 单次任务不需要记忆
```

**工作流示例**：

```
Webhook触发(接收问题)
    ↓
Agent(智能处理)
    ↓
结束(返回结果)
```

### 场景二：ReAct 模式 Agent

```yaml
data:
  type: "agent"
  title: "研究助手"
  agent_parameters:
    model:
      provider: "openai"
      name: "gpt-4"
    max_iterations: 10            # 允许多次迭代
    strategy: "react"             # ReAct 策略
    tools:
    - type: "web_search"
      name: "网络搜索"
      description: "搜索互联网获取最新信息"
      config:
        search_engine: "google"
        max_results: 5
    - type: "calculator"
      name: "计算器"
      description: "执行数学和统计计算"
    - type: "web_scraper"
      name: "网页抓取"
      description: "抓取指定网页的内容"
    memory:
      enabled: true
      type: "buffer"
      window_size: 5
    prompt:
      prefix: |
        你是一个专业的研究助手。你的任务是：
        1. 理解用户的问题
        2. 制定研究计划
        3. 使用工具收集信息
        4. 分析和综合信息
        5. 给出详细的答案
      suffix: |
        请始终展示你的推理过程。
```

### 场景三：规划执行模式 Agent

```yaml
data:
  type: "agent"
  title: "项目规划助手"
  agent_parameters:
    model:
      provider: "openai"
      name: "gpt-4"
    max_iterations: 15
    strategy: "plan-and-execute"   # 先规划再执行
    tools:
    - type: "database_query"
      name: "数据库查询"
      description: "查询项目数据库"
      config:
        connection: "project-db"
    - type: "api_call"
      name: "API调用"
      description: "调用项目管理API"
      config:
        base_url: "https://api.example.com"
    - type: "code_executor"
      name: "代码执行"
      description: "执行数据分析代码"
    memory:
      enabled: true
      type: "summary"               # 使用摘要记忆
      max_tokens: 2000
    prompt:
      prefix: |
        你是一个项目规划专家。
        对于复杂的任务，你应该：
        1. 首先制定详细的执行计划
        2. 列出所有需要的步骤
        3. 按计划逐步执行
        4. 在执行过程中调整计划
        5. 最后提供完整的分析报告
```

### 场景四：多工具协作 Agent

```yaml
data:
  type: "agent"
  title: "综合分析助手"
  agent_parameters:
    model:
      provider: "anthropic"
      name: "claude-3-opus"
    max_iterations: 20
    strategy: "react"
    tools:
    - type: "knowledge_retrieval"
      name: "知识库检索"
      description: "检索内部知识库"
      config:
        dataset_ids: ["kb-001", "kb-002"]
    - type: "database_query"
      name: "SQL查询"
      description: "查询业务数据库"
      config:
        connection: "business-db"
    - type: "api_call"
      name: "外部API"
      description: "调用第三方数据API"
    - type: "data_analysis"
      name: "数据分析"
      description: "执行数据分析和可视化"
    - type: "report_generator"
      name: "报告生成"
      description: "生成分析报告"
    memory:
      enabled: true
      type: "entity"                # 实体记忆
      max_tokens: 3000
```

### 场景五：对话式 Agent

```yaml
data:
  type: "agent"
  title: "客服Agent"
  agent_parameters:
    model:
      provider: "openai"
      name: "gpt-4-turbo"
    max_iterations: 8
    strategy: "function-calling"
    tools:
    - type: "knowledge_retrieval"
      name: "FAQ检索"
      description: "检索常见问题库"
      config:
        dataset_ids: ["faq-kb"]
    - type: "order_query"
      name: "订单查询"
      description: "查询用户订单信息"
    - type: "ticket_create"
      name: "创建工单"
      description: "创建客服工单"
    - type: "product_info"
      name: "产品信息"
      description: "查询产品详情"
    memory:
      enabled: true
      type: "buffer"
      window_size: 10               # 保留10轮对话
    prompt:
      prefix: |
        你是一个专业、友好的客服助手。
        你的职责：
        1. 理解客户的问题和需求
        2. 使用工具查询相关信息
        3. 提供准确、有帮助的答复
        4. 必要时创建工单跟进
      suffix: |
        请始终保持礼貌和专业。
```

### 场景六：反思模式 Agent

```yaml
data:
  type: "agent"
  title: "代码审查Agent"
  agent_parameters:
    model:
      provider: "openai"
      name: "gpt-4"
    max_iterations: 12
    strategy: "reflection"          # 反思模式
    tools:
    - type: "code_analyzer"
      name: "代码分析"
      description: "分析代码质量和潜在问题"
    - type: "test_runner"
      name: "测试运行"
      description: "运行单元测试"
    - type: "security_scan"
      name: "安全扫描"
      description: "扫描安全漏洞"
    - type: "performance_check"
      name: "性能检查"
      description: "检查性能问题"
    memory:
      enabled: true
      type: "summary"
    prompt:
      prefix: |
        你是一个资深的代码审查专家。
        审查流程：
        1. 分析代码结构和逻辑
        2. 运行测试和扫描
        3. 识别问题和改进点
        4. 反思你的分析是否全面
        5. 补充遗漏的检查
        6. 生成详细的审查报告
      suffix: |
        请对你的审查结果进行反思，确保没有遗漏重要问题。
```

## 工作流集成

### 与其他节点配合

#### 1. Agent + 知识检索

```
Webhook触发
    ↓
知识检索(检索背景信息)
    ↓
Agent(基于背景信息处理任务)
    ↓
结束
```

#### 2. Agent + 条件分支

```
Webhook触发
    ↓
Agent(分析任务)
    ↓
条件分支(根据Agent判断)
    ↓ 简单任务        ↓ 复杂任务
直接返回          进一步处理
```

#### 3. Agent + 迭代

```
Webhook触发
    ↓
迭代(遍历任务列表)
    ↓
Agent(处理每个任务)
    ↓
汇总结果
```

#### 4. 多 Agent 协作

```
Webhook触发
    ↓
Agent1(任务分解)
    ↓
并行分支
    ↓ 分支1                ↓ 分支2
Agent2(子任务1)        Agent3(子任务2)
    ↓                      ↓
        汇总节点
            ↓
        Agent4(综合分析)
            ↓
          结束
```

## 最佳实践

### 1. 工具设计原则

- **单一职责**：每个工具专注于一个明确的功能
- **清晰描述**：提供准确的工具描述，帮助 Agent 选择
- **输入验证**：确保工具输入参数的有效性
- **错误处理**：工具应该能够处理错误并返回有用信息

```yaml
tools:
- type: "custom_tool"
  name: "用户查询"
  description: |
    查询用户信息。
    输入：用户ID（字符串）
    输出：用户详细信息（JSON对象）
    使用场景：需要获取用户的个人信息、订单历史等
  config:
    connection: "user-db"
```

### 2. 提示词设计

```yaml
prompt:
  prefix: |
    你是 [角色定义]。
    
    你的能力：
    - [能力1]
    - [能力2]
    
    你的限制：
    - [限制1]
    - [限制2]
    
    工作流程：
    1. [步骤1]
    2. [步骤2]
    3. [步骤3]
  
  suffix: |
    重要提醒：
    - [提醒1]
    - [提醒2]
```

### 3. 迭代次数控制

| 任务复杂度 | 推荐迭代次数 | 说明 |
|-----------|-------------|------|
| 简单任务 | 3-5 | 单步或少量步骤 |
| 中等任务 | 5-10 | 需要多次工具调用 |
| 复杂任务 | 10-20 | 多步推理和规划 |

```yaml
agent_parameters:
  max_iterations: 10          # 根据任务复杂度设置
```

### 4. 记忆策略选择

| 场景 | 推荐记忆类型 | 原因 |
|------|-------------|------|
| 单次任务 | 禁用记忆 | 节省成本 |
| 对话式交互 | buffer | 保留完整上下文 |
| 长对话 | summary | 控制令牌消耗 |
| 实体追踪 | entity | 记住关键信息 |

### 5. 错误处理

```yaml
# 在 Agent 后添加条件分支
data:
  type: "if-else"
  title: "检查Agent结果"
  conditions:
  - variable: "{{#Agent节点ID.result.success#}}"
    operator: "equals"
    value: true
```

### 6. 监控和日志

```groovy
// 使用代码节点记录 Agent 执行情况
def main(agent_result) {
    def log = [
        timestamp: new Date(),
        iterations: agent_result.iterations,
        tools_used: agent_result.tools_used,
        success: agent_result.success,
        answer: agent_result.answer
    ]
    
    // 记录日志
    logService.record(log)
    
    return [result: agent_result]
}
```

## 常见问题

### 1. Agent 超出最大迭代次数

**原因**：
- 任务过于复杂
- 工具调用失败导致反复重试
- Agent 陷入思考循环

**解决**：
```yaml
# 增加迭代次数
agent_parameters:
  max_iterations: 15          # 从10增加到15

# 或简化任务
# 将复杂任务拆分为多个 Agent 处理
```

### 2. Agent 选择错误的工具

**原因**：工具描述不清晰

**解决**：
```yaml
tools:
- type: "query_users"
  name: "用户查询"
  description: |
    查询用户信息工具。
    
    适用场景：
    - 需要获取用户的基本信息（姓名、邮箱、电话等）
    - 需要查看用户的注册时间和状态
    
    不适用场景：
    - 查询用户订单（请使用"订单查询"工具）
    - 查询用户行为日志（请使用"日志查询"工具）
    
    输入：用户ID（必须是有效的UUID格式）
    输出：用户详细信息的JSON对象
```

### 3. Agent 响应时间过长

**原因**：
- 迭代次数过多
- 工具响应慢
- 模型选择不当

**解决**：
```yaml
# 1. 减少迭代次数
agent_parameters:
  max_iterations: 5           # 减少迭代

# 2. 使用更快的模型
model:
  provider: "openai"
  name: "gpt-3.5-turbo"       # 使用更快的模型

# 3. 优化工具性能
# - 添加缓存
# - 优化数据库查询
# - 使用异步调用
```

### 4. Agent 输出不稳定

**原因**：模型温度参数过高

**解决**：
```yaml
agent_parameters:
  model:
    provider: "openai"
    name: "gpt-4"
    temperature: 0.3          # 降低温度提高稳定性
```

### 5. 记忆占用过多 Token

**原因**：记忆配置不当

**解决**：
```yaml
memory:
  enabled: true
  type: "summary"             # 使用摘要记忆
  max_tokens: 1000            # 限制最大Token数
  window_size: 5              # 只保留最近5轮
```

## 高级特性

### 1. 自定义工具

创建自定义工具以扩展 Agent 能力：

```yaml
tools:
- type: "custom"
  name: "业务规则引擎"
  description: "执行复杂的业务规则判断"
  implementation: "groovy"
  code: |
    def execute(input) {
        // 自定义工具逻辑
        def result = businessRuleEngine.evaluate(input)
        return result
    }
```

### 2. 工具链组合

```yaml
tools:
- type: "tool_chain"
  name: "数据分析链"
  description: "执行完整的数据分析流程"
  chain:
  - tool: "data_query"
  - tool: "data_clean"
  - tool: "data_analyze"
  - tool: "report_generate"
```

### 3. 条件工具选择

```yaml
agent_parameters:
  tool_selection:
    mode: "conditional"
    rules:
    - condition: "question contains '订单'"
      tools: ["order_query", "order_update"]
    - condition: "question contains '用户'"
      tools: ["user_query", "user_update"]
```

## 性能优化

1. **并行工具调用**：允许 Agent 同时调用多个独立工具
2. **工具结果缓存**：缓存常用工具的调用结果
3. **渐进式响应**：流式返回 Agent 的思考过程
4. **预加载上下文**：提前加载常用的背景信息

## 注意事项

1. **成本控制**：Agent 的迭代调用会产生较高的 Token 消耗
2. **工具安全**：确保工具调用的安全性，避免恶意输入
3. **超时处理**：设置合理的超时时间，避免 Agent 长时间运行
4. **结果验证**：对 Agent 的输出进行必要的验证
5. **监控告警**：监控 Agent 的执行情况，及时发现异常

## 与 LLM 节点的对比

| 特性 | LLM 节点 | Agent 节点 |
|------|---------|-----------|
| 功能 | 文本生成 | 推理+工具使用 |
| 复杂度 | 简单 | 复杂 |
| 成本 | 低 | 高（多次调用）|
| 适用场景 | 文本任务 | 需要多步推理的任务 |
| 工具使用 | 不支持 | 支持 |
| 自主规划 | 不支持 | 支持 |

## 相关文档

- [LLM节点](LLM节点.md) - 基础的语言模型节点
- [知识检索节点](知识检索节点.md) - 可作为 Agent 的工具使用
- [代码节点](../转换节点/代码执行.md) - 自定义工具实现
- [条件分支](../逻辑节点/条件分支.md) - Agent 结果判断
