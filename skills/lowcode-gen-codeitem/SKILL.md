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

## Steps 执行步骤

1. 校验 `name` 和非空的 `items`。
2. 若任何 `codetext` 或 `codevalue` 缺失，停止并写入 open questions。
3. 写入/更新 `.lowcode-plans/<apptag>/codeitem/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 批准后调用 `../../scripts/add_codeitem.py`。
5. 运行 `../../scripts/validate_yml.py <target-file>`。

## Boundaries 边界约束

- 不在此生成 MIS 字段；只说明 MIS 可能通过 `datasourceCodename` 引用本代码项。
- 不臆造代码项的取值（code value）。
