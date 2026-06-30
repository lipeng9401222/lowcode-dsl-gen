---
name: lowcode-gen-mis
description: Epoint 低代码 MIS 数据模型原子生成器。根据 lowcode-dsl-gen IR 的 mis asset 生成或维护 mis/*.mis.yml，负责表名、中文说明、字段、字段类型、长度、必填、唯一和 codeitem 绑定；字段不完整时只回写 open_questions。
---

# lowcode-gen-mis

只处理 `assets[type=mis]`。

## Input 输入

```yaml
spec:
  tableName: "purchaseproject"
  tableChineseName: "采购立项"
  primaryKey: "rowguid"
  fields:
    - fieldName: "audit_status"
      fieldType: "nvarchar"
      length: 50
      chineseName: "审核状态"
      mustfill: false
      datasourceCodename: "审核状态"
```

## References 参考文档

- `../../references/mis/数据模型/index.md`
- `../../references/conventions.md`

## Grill Gate 追问门禁

生成前必须确认以下关键事实，未确认的不得用模型猜测静默补齐。

### 必问事实

| 事实 | 说明 | 禁止猜测 |
|-----|------|---------|
| `tableName` 表名 | 小写英文，不含下划线 | ❌ |
| `tableChineseName` 表中文名 | 中文描述 | ❌ |
| 字段列表 | 每个字段的 `fieldName`、`fieldType`、`length` | ❌ |
| 字段中文名 | 每个字段的 `chineseName` | ❌ |

### 可推断 / 安全默认

| 事实 | 来源 | 默认值 |
|-----|------|-------|
| `primaryKey` | 统一主键 | `rowguid`（`safe_default`） |
| `mustfill` | 默认非必填 | `false`（`safe_default`） |
| `isunique` | 默认不唯一 | `false`（`safe_default`） |
| 字段 `ordernum` | 按列表顺序递增 | `safe_default` |

### 可选追问（影响生成但有安全默认）

- `mustfill` 必填性：需用户逐字段确认
- `isunique` 唯一性：影响数据完整性，建议确认
- `datasourceCodename` codeitem 绑定：需确认引用的代码项是否存在
- `length` 字段长度：不同类型有默认值，但特殊场景需确认

### 禁止猜测

- **字段名称（fieldName）**：不得从表名臆造字段
- **字段类型（fieldType）**：不同类型影响存储和查询，必须确认
- **codeitem 绑定**：`datasourceCodename` 引用的代码项必须真实存在

### 确认矩阵

| 确认项 | 必须 | 说明 |
|-------|------|------|
| 表名和中文名 | ✅ | 关键身份标识 |
| 字段列表（名称+类型+长度） | ✅ | 核心数据结构 |
| 字段中文名 | ✅ | UI 显示 |
| 必填/唯一约束 | 有约束时 ✅ | 影响数据完整性 |
| codeitem 绑定 | 有绑定时 ✅ | 跨资产引用 |

## Steps 执行步骤

1. 校验表名、表中文说明和字段。
2. 确认被引用的 codeitem 在 IR 或现有应用清单中存在。
3. 写入/更新 `.lowcode-plans/<apptag>/mis/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 先 `--dry-run` 预览并把内容展示给用户，逐项确认后再加 `--confirm` 落盘：新表调用 `../../scripts/add_mis_field.py --create`，已有表用追加模式。不加 `--confirm` 脚本会拒绝写文件；禁止写批处理脚本一次落多个。
5. 运行 `../../scripts/validate_yml.py <target-file>`；用到 codeitem 引用时在应用级别加 `--check-refs`。

## Boundaries 边界约束

- 不生成页面、模块、workflow 或 event。
- 除非用户明确要求空模型，否则不使用 `--allow-empty-fields`。
