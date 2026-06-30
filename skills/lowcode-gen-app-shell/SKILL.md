---
name: lowcode-gen-app-shell
description: Epoint 低代码应用壳原子生成器。根据 lowcode-dsl-gen IR 的 app-shell asset 和 application 信息创建应用根目录、标准资产目录、appinfo.lowcode.yml 和可选 appref.lowcode.yml。用于新建应用外壳、初始化目录、维护 appinfo/appref；不负责 codeitem/mis/module/pagedesigne/workflow/event 业务资产。
---

# lowcode-gen-app-shell

接收 dispatcher 提供的 IR application 和 `assets[type=app-shell].spec`，只生成应用外壳。

## Input 输入

```yaml
application:
  apptag: ""
  applicationname: ""
  developerstag: "epoint"
  kitid: "businessprocess"
  tenantguid: ""
  baseouguid: ""
  categories: []
  sources:
    developerstag: "user_confirmed"
    kitid: "user_confirmed"
    tenantguid: "safe_default"
    baseouguid: "safe_default"
    categories: "user_confirmed"
asset:
  id: "asset-001"
  type: "app-shell"
  spec:
    # createDirs 默认只含 5 个核心目录；event / api 默认不建，
    # 仅当用户明确需要动作流 / 接口元数据时，才把它们加入 createDirs
    createDirs: ["codeitem", "mis", "module", "pagedesigne", "workflow"]
    appref:
      enabled: false
      refs: []
    sources:
      appref: "user_confirmed"
```

## References 参考文档

- `../../references/directory-structure.md`
- `../../references/appinfo/应用配置/index.md`
- `../../references/appref/引用配置/index.md` 仅当 `spec.appref.enabled=true` 时才读

## Grill Gate 追问门禁

生成前必须确认以下关键事实，未确认的不得用模型猜测静默补齐。

### 必问事实

| 事实 | 说明 | 禁止猜测 |
|-----|------|---------|
| `apptag` 应用标签 | 英文标识，决定目录路径和隔离空间 | ❌ |
| `applicationname` 应用名称 | 中文名称 | ❌ |
| `developerstag` 开发者标签 | 如 `epoint`，但不是无痕默认值 | ❌ |
| `kitid` 套件 ID | 如 `businessprocess`，但不是无痕默认值 | ❌ |

### 可推断 / 安全默认

| 事实 | 来源 | 默认值 |
|-----|------|-------|
| `tenantguid` | 单租户场景 | 空字符串（`safe_default`，reason: 单租户） |
| `baseouguid` | 单机构场景 | 空字符串（`safe_default`，reason: 单机构） |
| `createDirs` | 5 个核心目录 | `[codeitem, mis, module, pagedesigne, workflow]`（`safe_default`） |

### 可选追问

- `categories` 应用分类：空数组需标记为"用户确认不分类"或从仓库推断
- `appref` 引用配置：是否需要跨应用引用
- 是否需要 event/api 目录：默认不建，需用户明确

### 禁止猜测

- **`apptag`**：影响所有资产路径，不得从应用名称翻译臆造
- **`developerstag`**：`epoint` 只是推荐值，不是无痕默认值，必须确认
- **`kitid`**：`businessprocess` 只是推荐值，不是无痕默认值，必须确认

### 确认矩阵

| 确认项 | 必须 | 说明 |
|-------|------|------|
| apptag | ✅ | 核心身份标识 |
| 应用名称 | ✅ | UI 显示 |
| developerstag | ✅ | 开发者标识 |
| kitid | ✅ | 套件类型 |
| categories | ✅ | 即使为空也需确认 |
| 是否需要 event/api | ✅ | 按需门禁 |

## Steps 执行步骤

1. 用 `../../scripts/path_resolver.py` 计算应用根目录，禁止手写 `metadata/` 路径。
2. 拒绝静默默认值：`developerstag`、`kitid`、`categories`、`tenantguid`、`baseouguid`、`appref` 都必须在 IR 中带有 `user_confirmed`、`repo_inferred` 或允许的 `safe_default` 来源。
3. 校验来源证据：`user_confirmed` 需有 `questionId/interactionId`，`repo_inferred` 需有 `repoEvidence`，`safe_default` 需有 `reason`。
4. 批准前只允许写 dispatcher 计划包和 `.lowcode-plans/<apptag>/app-shell/<asset-id>-plan.md`；子计划必须包含输入 IR 摘要、确认/来源表、dry-run 命令与结果、校验命令与结果。
5. 批准后用 application 字段调用 `../../scripts/scaffold_app.py`。
   - 默认只建 5 个核心目录（codeitem/mis/module/workflow/page）。
   - 仅当用户明确需要动作流时加 `--with-event`；明确需要接口元数据时加 `--with-api`。
6. 用 `../../scripts/validate_yml.py --check-refs <app-root>` 校验应用根目录。

## Boundaries 边界约束

- 不生成业务资产。
- 不为 CRUD 生成 event（动作流）。
- 除非 IR 或用户显式提供，否则不推断 tenant / baseou / category。
- `developerstag=epoint`、`kitid=businessprocess` 只是推荐默认值，不等于已确认。
- `event`（动作流）、`api`（接口元数据）默认不创建目录，需用户明确要求后再加对应开关。
