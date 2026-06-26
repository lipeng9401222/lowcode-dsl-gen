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

## Steps 执行步骤

1. 校验表名、表中文说明和字段。
2. 确认被引用的 codeitem 在 IR 或现有应用清单中存在。
3. 写入/更新 `.lowcode-plans/<apptag>/mis/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 批准后：新表调用 `../../scripts/add_mis_field.py --create`，已有表用追加模式。
5. 运行 `../../scripts/validate_yml.py <target-file>`；用到 codeitem 引用时在应用级别加 `--check-refs`。

## Boundaries 边界约束

- 不生成页面、模块、workflow 或 event。
- 除非用户明确要求空模型，否则不使用 `--allow-empty-fields`。
