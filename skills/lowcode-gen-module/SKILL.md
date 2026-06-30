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

## Grill Gate 追问门禁

生成前必须确认以下关键事实，未确认的不得用模型猜测静默补齐。

### 必问事实

| 事实 | 说明 | 禁止猜测 |
|-----|------|---------|
| `name` 模块名称 | 中文名称，UI 显示 | ❌ |
| `code` 模块编码 | 4-8 位数字字符串，需确认工程编码规则 | ❌ |
| 是否有子模块 | 列出所有子菜单的名称、code、路由地址 | ❌ |

### 可推断 / 安全默认

| 事实 | 来源 | 默认值 |
|-----|------|-------|
| `guid` | 自动生成 UUIDv4 | `safe_default` |
| `isVue` | 新方案统一 Vue | `1`（`safe_default`） |
| `isUse` | 默认启用 | `1`（`safe_default`） |
| `parentGuid` | 根模块为空，子模块自动指向父 | `safe_default` |
| `createTime/updateTime` | 当前时间 | `safe_default` |

### 可选追问（影响生成但有安全默认）

- `url` / `routePath`：模块路由地址，根模块一般为空，子模块需对应 pagetag
- `orderNumber`：排序号，影响菜单显示顺序
- `auth` 权限配置：授权对象 GUID、授权类型（默认 `Role`）；不需要可说"暂不配置"

### 确认矩阵

生成前需确认以下项目，每项标记 `confirmed / not_required / pending`：

| 确认项 | 必须 | 说明 |
|-------|------|------|
| 模块名称和编码 | ✅ | 关键身份标识 |
| 子模块结构 | ✅ | 树结构和编码规则 |
| 模块路由 | 有子模块时 ✅ | 路由地址需对应实际页面 |
| 权限配置 | ❌ | 可后续在线上配置 |

## Steps 执行步骤

1. 校验 `name` 和 `code`。
2. 仅当模块需要打开页面时才确认 URL。
3. 写入/更新 `.lowcode-plans/<apptag>/module/<asset-id>-plan.md`，包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。不要只留一个仅含状态的占位计划。
4. 先 `--dry-run` 预览并把内容展示给用户，确认后再加 `--confirm` 落盘：调用 `../../scripts/add_module.py`。不加 `--confirm` 脚本会拒绝写文件。
5. 运行 `../../scripts/validate_yml.py <target-file>`。

## Boundaries 边界约束

- 不生成 pagedesigne 资产。
- 当用户或计划要求固定编码规则时，不臆造模块 code；通过 open_questions 追问。
