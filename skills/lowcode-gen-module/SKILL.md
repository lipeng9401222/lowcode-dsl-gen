---
name: lowcode-gen-module
description: Epoint 低代码模块菜单原子生成器。根据 lowcode-dsl-gen IR 的 module asset 生成 module/*.module.yml，负责模块名称、编码、URL、子模块和菜单层级；不负责页面 schema 或权限实现。
---

# lowcode-gen-module

只处理 `assets[type=module]`。

## Input 输入

```yaml
spec:
  name: "采购管理"
  code: "9544"
  url: ""
  subModules: []
```

## References 参考文档

- `../../references/module/模块/index.md`
- `../../references/directory-structure.md`

## Steps 执行步骤

1. 校验 `name` 和 `code`。
2. 仅当模块需要打开页面时才确认 URL。
3. 写入/更新 `.lowcode-plans/<apptag>/module/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 批准后调用 `../../scripts/add_module.py`。
5. 运行 `../../scripts/validate_yml.py <target-file>`。

## Boundaries 边界约束

- 不生成 pagedesigne 资产。
- 当用户或计划要求固定编码规则时，不臆造模块 code；通过 open_questions 追问。
