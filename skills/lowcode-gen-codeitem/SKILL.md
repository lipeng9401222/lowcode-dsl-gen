---
name: lowcode-gen-codeitem
description: Epoint 低代码代码项原子生成器。根据 lowcode-dsl-gen IR 的 codeitem asset 生成或维护 codeitem/*.codeitem.yml，要求名称和所有 codetext/codevalue 子项完整；缺少子项时只回写 open_questions，不调用生成脚本。
---

# lowcode-gen-codeitem

只处理 `assets[type=codeitem]`。

## Input 输入

```yaml
spec:
  name: "审核状态"
  description: ""
  items:
    - codetext: "待提交"
      codevalue: "0"
      ordernum: 1
```

## References 参考文档

- `../../references/codeitem/代码项/index.md`
- 命名 / 默认值不明确时读 `../../references/conventions.md`

## Grill Gate 追问门禁

生成前必须确认以下关键事实，未确认的不得用模型猜测静默补齐。

### 必问事实

| 事实 | 说明 | 禁止猜测 |
|-----|------|---------|
| `name` 代码项名称 | 中文名称，需用户明确 | ❌ |
| `items` 所有子项 | 每个子项的 `codetext`（显示文本）和 `codevalue`（存储值） | ❌ |
| 子项完整性 | 缺少任何一个 codetext/codevalue 必须停止并追问 | ❌ |

### 可推断 / 安全默认

| 事实 | 来源 | 默认值 |
|-----|------|-------|
| `ordernum` | 按列表顺序自动递增 | `safe_default`（从 1 开始） |
| `description` | 可为空 | `safe_default`（空字符串） |
| `codeguid` | 自动生成 UUIDv4 | `safe_default` |

### 可选追问

- `description` 代码项描述：不影响生成，可省略
- 排序规则：默认按列表顺序，如有特殊排序需求需确认
- 关联 MIS 字段：提示哪些 MIS 字段通过 `datasourceCodename` 引用本代码项

### 禁止猜测

- **子项取值（codevalue）**：如"待审核=1、已审核=2"必须用户确认，不得模型推断
- **代码项命名**：不得臆造代码项的名称
- **子项数量和内容**：用户说"审核状态"不代表模型知道具体有哪些状态值

## Steps 执行步骤

1. 校验 `name` 和非空的 `items`。
2. 若任何 `codetext` 或 `codevalue` 缺失，停止并写入 open questions。
3. 写入/更新 `.lowcode-plans/<apptag>/codeitem/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 先 `--dry-run` 预览并把内容展示给用户，逐项确认后再加 `--confirm` 落盘：调用 `../../scripts/add_codeitem.py`。不加 `--confirm` 脚本会拒绝写文件；禁止写批处理脚本一次落多个。
5. 运行 `../../scripts/validate_yml.py <target-file>`。

## Boundaries 边界约束

- 不在此生成 MIS 字段；只说明 MIS 可能通过 `datasourceCodename` 引用本代码项。
- 不臆造代码项的取值（code value）。
