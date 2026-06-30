# 目录结构规范

低代码线下应用的工程目录是有严格规范的。**任何 yml 落盘前都必须先确认目录结构正确**，否则线上设计器和运行时无法识别。

> ⛔ **结构红线（spec v2，每次落盘必查）**：应用资产**直接挂在 `<apptag>/` 下**。任何形如 `<apptag>/metadata/<asset>/...` 的路径都是老结构，spec v2 已废弃，新生成不允许出现。脚本（`scaffold_app.py` / `add_workflow.py` / `path_resolver.py`）会在传入路径含 `/metadata/` 段时直接 fail-fast 退出。
>
> 老应用迁移命令：
> ```bash
> mv <apptag>/metadata/* <apptag>/ && rmdir <apptag>/metadata
> ```

## 完整结构图（新结构 — 应用资产直接挂在 `<apptag>/` 下，不再有 `<apptag>/` 层）

```
<外层组件工程>（如 ztb-qy-businessprocess、epoint-ipd-parent）
├── <action 子工程>（如 ztb-qy-businessprocess-action、epoint-ipd-action）
│   └── src/main/
│       ├── java/com/epoint(开发商)/
│       │   └── [<租户>/]
│       │       └── [<独立单位>/]
│       │           └── <apptag>/
│       │               └── controller/<XxxFrontController>.java
│       └── resources/
│           ├── <kit>_com.properties        ← 组件化配置（套件标识等）
│           └── META-INF/resources/
│               └── epoint(开发商)/
│                   ├── [<tenantguid>/]
│                   │   └── [<baseouguid>/]
│                   │       ├── [<分类...>/]   ← 中间可加多层应用分类
│                   │       │   └── <apptag>/  ← 应用根目录
│                   │       │       ├── appinfo.lowcode.yml
│                   │       │       ├── appref.lowcode.yml
│                   │       │       ├── event/
│                   │       │       ├── api/
│                   │       │       ├── mis/
│                   │       │       ├── module/
│                   │       │       ├── workflow/
│                   │       │       ├── codeitem/
│                   │       │       └── pagedesigne/
├── <vue 子工程>（如 ztb-qy-businessprocess-vue）
│   └── src/views/epoint/[<tenant>/][<baseou>/]<apptag>/<apptag>_list.vue
├── <api 子工程> ← Java 实体
└── <service 子工程> ← Java 服务
```

> ⚠️ **结构调整提醒**：旧结构 `<apptag>/<asset>/...` 仍可被脚本读取（兼容），但 skill 一律按新结构生成；老结构会触发 warn 提示迁移。

## 应用根目录详解

```
<apptag>/
├── appinfo.lowcode.yml              ← 应用配置文件（必备，每个应用 1 份）
├── appref.lowcode.yml               ← 引用配置文件（可选，引用其他应用资产时）
├── codeitem/                        ← 代码项目录（可多个 yml）
│   ├── 审核状态.codeitem.yml         （新建强制双扩展；历史 审核状态.codeitem.yml 仅兼容读取）
│   └── 类型.codeitem.yml
├── mis/                             ← 数据表/数据模型目录
│   └── customerinfo.mis.yml
├── module/                          ← 模块目录
│   └── 采购立项模块.module.yml
├── event/                           ← 动作流目录
│   ├── 获取列表数据.event.yml
│   └── 保存采购项目.event.yml
├── api/                             ← API 接口元数据（少用，主要给 Java 高码注解关联）
│   └── batchQueryPermission.api.yml
├── workflow/                        ← 工作流目录
│   └── 采购立项流程模板.workflow.yml
└── page/                            ← 页面设计器目录
    ├── 采购立项列表.json
    └── 采购立项表单.json
```

## 路径计算规则（重要！）

给定用户提供的字段，计算应用根目录绝对路径的算法：

```python
# 输入
action_root = "<action 子工程绝对路径>"  # 如 /xxx/epoint-ipd-action
developerstag = "epoint"                # 必填
tenantguid = "" or "tenant_xxx"         # 可选，默认空
baseouguid = "" or "epoint"             # 可选，默认空；仅用户明确要求时填 epoint 或其他值
categories = [] or ["trade", "tradeprocess"]  # 可选，多层
apptag = "purchaseproject"              # 必填

# 输出（新结构：直接到 <apptag>/，不再追加 metadata）
parts = [action_root, "src/main/resources/META-INF/resources", developerstag]
if tenantguid: parts.append(tenantguid)
if baseouguid: parts.append(baseouguid)
parts.extend(categories)
parts.append(apptag)

app_root = "/".join(parts)
```

> **该算法已实现**于 `scripts/path_resolver.py` 的 `compute_app_root()`，**不要在对话里手算**。

## 目录命名规则

| 层级 | 命名规则 | 示例 |
|------|---------|------|
| 开发商目录 | 小写英文，固定 `epoint` 居多 | `epoint` |
| 租户目录 | 小写 + 数字，可空 | `tenant001` 或省略 |
| 独立单位目录 | 小写 + 数字，可空 | `epoint` 或省略 |
| 分类目录 | 小写英文，可多层 | `trade/`、`fenlei1/` |
| 应用目录(apptag) | 全小写英文，**全局唯一**，无短横线 | `purchaseproject`、`xmlx` |
| 资产子目录 | **固定的 7 个名字**，不可变 | `codeitem/`、`mis/`、`module/`、`event/`、`api/`、`workflow/`、`pagedesigne/` |

## 文件命名规则

| 类型 | 文件名规则 | 示例 |
|------|----------|------|
| `appinfo` | 固定文件名 | `appinfo.lowcode.yml` |
| `appref` | 固定文件名 | `appref.lowcode.yml` |
| `codeitem` | `<中文/英文名>.codeitem.yml`（历史 `<名>.yml` 只兼容读取） | `审核状态.codeitem.yml`、`orderstatus.codeitem.yml` |
| `mis` | `<英文表名>.mis.yml`，英文表名小写英文数字、不能有下划线 | `customerinfo.mis.yml` |
| `module` | `<中文/英文名>.module.yml` | `采购立项模块.module.yml` |
| `event` | `<功能名/接口名>.event.yml` | `获取列表数据.event.yml`、`getDataGridModel.event.yml` |
| `workflow` | `<流程名>.workflow.yml` | `采购立项流程.workflow.yml` |
| `pagedesigne` | `<页面名>.json` | `采购立项列表.json` |

> **关于双扩展名**：新建资产必须使用 `名字.类型.yml`。历史单扩展 `.yml` 只作为兼容读取，不再作为新建默认风格。

## 现有工程实例（本仓库 epoint-ipd-action）

```
epoint-ipd-action/src/main/resources/META-INF/resources/
└── epoint/                          ← 开发商
    └── fenlei1/                     ← 应用分类（一层）
        └── xmlx/                    ← 应用 apptag（直接挂资产子目录，无 metadata/）
            ├── appinfo.lowcode.yml
            ├── codeitem/
            │   ├── 审核状态.codeitem.yml
            │   └── 类型.codeitem.yml
            ├── mis/
            │   └── customerinfo.mis.yml
            ├── event/
            │   └── purchaseproject_getDataGridModel.event.yml
            └── page/                ← 页面设计器 JSON 目录
                ├── requirement_list.json
                └── requirement_form.json
```

> **注意**：`page/` 目录只放页面设计器 JSON；不要再生成 `.epage` 或 `.pagedesigne.yml`。

## 快速校验

判断一个 应用根目录是否合法：

1. 必有 `appinfo.lowcode.yml`，且文件里 `apptag` 字段值与目录名一致
2. 子目录只能是固定的 7 个名字之一
3. 每个 yml 文件第一行（appinfo/appref 除外）必须是 `type: <对应标识>`
4. 文件名不能有特殊字符；中文名允许用于 codeitem、module、workflow、pagedesigne；mis 英文表名必须小写英文数字且不能有下划线

调用 `python3 scripts/validate_yml.py <app-root>` 执行上述校验。

## 运行时计划文档与追溯

所有触发模式都必须从第一轮开始维护 `<工程根>/.lowcode-plans/<apptag>-plan.md`（apptag 未定时先用 `<任务简称>-plan.md`），并把它当作全过程审计台账：

- 如果工程根尚未定位，第一轮只问工程根/action 子工程定位问题；定位成功后，把这轮定位问题、选项和用户回复补录进计划文档。
- 提问前追加 `对话确认记录`：阶段、问题、选项、推荐项说明、提问方式、状态 `awaiting_user`。
- 用户回复后回填同一条记录：用户原文、解析结果、确认状态、对阶段状态的影响。
- 确认 apptag 后，把临时计划迁移为 `<apptag>-plan.md`，不得丢失早期问答。
- 使用 Plan Mode / 结构化问答时，也要把问题、选项、选择结果和自由文本同步写入计划文档。
- 全部阶段确认后，只是把计划文档里的 `生成计划` 章节整理成最终版；不是到最后才创建计划文档。

## 触发模式细节

### 模式 A：从零创建应用（Greenfield）

#### A.1 渐进式收集核心信息

按自然语言渐进式收集；每轮最多问 3 个问题，已给出的字段直接吸收并继续追问缺失项。

| # | 字段 | 默认值 | 必填 | 备注 |
|---|------|--------|------|------|
| 1 | 开发商标识 `developerstag` | `epoint` | ✅ | 一般不改 |
| 2 | 租户标识 `tenantguid` | 空 | ❌ | 多租户场景才填 |
| 3 | 独立单位标识 `baseouguid` | 空 | ❌ | 看本工程示例约定 |
| 4 | 应用分类（多层，目录形式） | 空 | ❌ | 例如 `trade/tradeprocess` |
| 5 | 应用标识 `apptag` | — | ✅ | 全局唯一，小写英文，如 `purchaseproject` |
| 6 | 应用名称 `applicationname` | — | ✅ | 中文，如 `采购立项` |
| 7 | 套件标识 `kitid` | `businessprocess` | ❌ | 多套件嵌套时填全路径，如 `frame.user` |
| 8 | 是否引用其他应用资产 | 否 | ❌ | 是则进入 `appref.lowcode.yml` 子流程 |
| 9 | 是否需要动作流 `event` / 接口元数据 `api` | 否 | ✅ | **必须显式确认一次**：动作流=接口编排/状态联动/Webhook/定时/推送/回调；默认都不创建，推荐「否」。答「是」才建对应目录 |

> **默认值规则**：新建应用 `baseouguid` 默认为空；历史应用可能存在 `baseouguid: epoint`，只作为兼容示例，不作为新建默认值。

#### A.2 整理生成计划 + 明确批准

核心信息收齐后，把已经持续维护的计划文档整理成一次创建计划并展示。此阶段除 `.lowcode-plans/<apptag>-plan.md` 外不要写任何文件、不要调用 `scripts/scaffold_app.py`：

```
我准备按下面的计划创建应用：

- 应用名称：<applicationname>
- 应用标识：<apptag>
- 开发商/租户/独立单位：<developerstag>/<tenantguid>/<baseouguid>
- 分类目录：<分类... 或 不分类>
- 套件标识：<kitid>
- 引用其他应用资产：<是/否，若是列出引用>
- 需要动作流 event：<是/否，默认否>
- 需要 api 接口元数据：<是/否，默认否>
- 计划文档：.lowcode-plans/<apptag>-plan.md
- 对话追溯：已记录每轮问题、选项、用户回复和确认结果
- 将创建的目录（路径以工程根为基准）：
<action子工程>/src/main/resources/META-INF/resources/epoint/[<租户>/][<独立单位>/]<分类...>/<apptag>/
├── codeitem/                 ← 仅保留目录，用户要求代码项后再生成 yml
├── mis/                      ← 仅保留目录，用户确认字段后再生成 yml
├── module/
├── workflow/
├── pagedesigne/
├── event/                    ← 仅当上面"需要动作流"确认为是时才创建（--with-event）
├── api/                      ← 仅当上面"需要 api"确认为是时才创建（--with-api）
├── appinfo.lowcode.yml      ← 批准后生成
└── appref.lowcode.yml       ← 批准后仅当声明引用时生成

请回复"批准创建"后我再写文件；也可以直接说要调整哪一项。
```

只有用户明确回复"批准创建 / 可以创建 / 按这个创建"等批准语义时，才把计划文档的 `approval_status` 改为 `approved`，再调用 `scripts/scaffold_app.py` 一次性建好骨架。模糊回复（"嗯"、"好像可以"、"你看着办"）**不算批准**，继续追问。

#### A.3 询问继续添加哪些资产

骨架建好后，问：「应用骨架已建好，要现在生成哪些资产？」让用户选：

- 代码项 codeitem（数据字典）→ 读 `references/codeitem/代码项/index.md`
- 数据表 mis（业务表/模型）→ 读 `references/mis/数据模型/index.md`
- 模块 module（菜单）→ 读 `references/module/模块/index.md`
- 动作流 event（接口业务编排）→ 读 `references/event/动作流/index.md`
- 工作流 workflow（审批流）→ 读 `references/workflow/工作流/index.md`
- 页面设计器 pagedesigne（前端页面 schema）→ 读 `references/pagedesigne/页面设计器/index.md`

**用户每选一项**，只去读那一项对应的 references 文档，按里面的对话流程继续推进。

### 模式 B：修改/补充已有应用

#### B.1 定位应用

让用户提供以下任一信息：

- apptag（如 `purchaseproject`、`xmlx`）
- 已有的 `appinfo.lowcode.yml` 文件路径
- 直接说"在 xxx 应用下面加一个 yyy"，从语境识别

定位后调用 `scripts/path_resolver.py --apptag <tag>` 算出 应用根目录绝对路径，并列出现有资产清单。

定位过程中如果需要追问 apptag / appinfo 路径 / action 子工程，也要先在计划文档里记录问题与选项；确认应用后把临时计划迁移到 `.lowcode-plans/<apptag>-plan.md`。

#### B.2 询问操作意图

```
应用 <applicationname> (apptag=<apptag>) 现有资产：
- codeitem: 审核状态.codeitem.yml, 类型.codeitem.yml
- mis: customerinfo.mis.yml
- event: purchaseproject_getDataGridModel.event.yml
- module: 无
- workflow: 无
- pagedesigne: 无

你要做什么？
1. 新增资产
2. 修改已有资产（哪个？）
3. 删除资产
4. 调整 appinfo（应用基础信息）
5. 调整 appref（引用关系）
```

#### B.3 跳到对应 references 文档执行

每一类资产都有对应的 references 子文档，文档里详细描述了"新增/修改/删除"三种操作的字段清单和对话脚本。

### 模式 C：资产级快速通道

当用户语句直接表达资产级意图（例如"给采购立项加个'审核状态'代码项"、"在 xmlx 下新增 mis 表 supplierinfo"、"生成请假工作流/审批流"），**跳过完整 8 步对话**，直接：

1. 解析出 `apptag` + 资产类型 + 资产名称
2. 如果缺少 `apptag` 或目标应用，第一问只确认：加到已有应用、新建完整应用、仅生成计划；不得默认降级为新建整应用
3. 调 `scripts/path_resolver.py` 验证目标 apptag 存在；用户明确选择新建完整应用时才进入模式 D 或模式 A
4. 直接读对应资产类型的 `references/<asset>/<中文目录>/index.md`，按文档走专属流程
5. 如有缺信息，逐项追问
6. 信息齐全后**仍需更新** `.lowcode-plans/<apptag>-plan.md` 和 `.lowcode-plans/<apptag>/<asset-type>/<asset-id>-plan.md`，补齐对话确认记录、来源追踪和生成计划，并等待明确批准，不能直接调用脚本

### 模式 D：需求材料/自然语言整应用生成

当用户给出需求文档、会议纪要、自然语言描述，或说"帮我生成整个低代码应用"时，先读 `references/whole-app-workflow.md`，按下面顺序推进：

1. 先形成"主体架构/应用蓝图"，只确认业务目标、边界、是否新建或补充、以及页面/流程的大方向；推断值标记为建议。
2. 再形成"基本信息草案"，确认 appinfo 所需的名称、apptag、分类、套件、目录归属。
3. 然后按 `codeitem → mis → module → pagedesigne → workflow` 的顺序分轮确认资产，每轮只问当前阶段。`event`（动作流）、`api`（接口元数据）默认不纳入，但**必须在资产规划阶段显式确认一次**：明确问用户「是否需要动作流（接口编排/状态联动/Webhook/定时/推送/回调）或 api 接口元数据？默认都不创建」，推荐「否」；用户答「是」才追加对应资产并继续逐资产确认，答「否」则不建目录、不生成。确认结果记入计划 `对话确认记录`。
4. 从第一轮起持续维护 `.lowcode-plans/<apptag>-plan.md`；每个阶段确认后都更新对话确认记录、阶段确认结果和资产拆分表；全部阶段确认后再整理完整"生成计划"章节。
5. 用户明确批准计划后才开始落盘，且**必须分阶段逐资产落盘，禁止一次性批量全落盘**：按 `codeitem → mis → module → pagedesigne → workflow` 顺序（`event`/`api` 仅当用户明确要求时才纳入），每个资产先 `--dry-run` → 展示该资产 dry-run 结果与关键字段 → 用户确认（“继续/调整”）→ 落盘该资产 → `validate_yml.py`；用户每确认一个才落一个，可随时叫停或纠偏。`whole-app` 落盘前还须通过 `python3 scripts/validate_plan.py .lowcode-plans/<apptag>-plan.md`。全部资产落盘后，**交付前最终校验**统一执行 `python3 scripts/validate_yml.py --strict --check-refs <app-root>`（spec v2 严格模式：旧驼峰键 / `tableid` 残留 / `metadata/` 老结构 一律升级为 error）。

缺少页面信息时，把用户说的 `pagedesign` 统一映射到页面设计器资产 `pagedesigne`，落盘到 `page/*.json`，并优先调用 `scripts/add_page.py`。

#### 模式 D 中间产物（应用蓝图最小字段）

```yaml
task:
  mode: whole-app
  requestedAssetTypes: [app-shell, codeitem, mis, module, pagedesigne, workflow]
  sources:
    mode: user_confirmed
application:
  applicationname: <中文名>
  apptag: <英文标识或建议值>
  developerstag: epoint
  kitid: businessprocess
  baseouguid: ""
  categories: []
  sources:
    developerstag: user_confirmed
    kitid: user_confirmed
    baseouguid: safe_default
    tenantguid: safe_default
    categories: user_confirmed
assets:
  codeitem: []
  mis: []
  module: []
  event: []
  workflow: []
  pagedesigne: []
open_questions: []
```

生成计划必须用业务语言解释每个资产为什么需要，不要只给用户一组命令。

## 脚本调用 cheatsheet

每个脚本都内置 `--help`，参数缺失会自报使用方法。这里给出**完整调用示例**，供查阅时复制：

> ⚠️ **以下示例为简洁省略了 `--dry-run` / `--confirm`。实际落盘必须两步走**：先 `add_*.py ... --dry-run` 预览内容并展示给用户 → 用户逐项确认 → 再 `add_*.py ... --confirm` 落盘。不加 `--confirm` 脚本会拒绝写文件。

```bash
# 1. 新建应用骨架（建目录 + appinfo + 可选 appref）
#    默认只建 5 个核心目录：codeitem/mis/module/workflow/page
#    event / api 默认不建，需要时分别加 --with-event / --with-api
python3 scripts/scaffold_app.py \
  --apptag xmlx \
  --name 项目立项 \
  --action-root /path/to/epoint-ipd-action

# 2. 给定 apptag 算应用根目录绝对路径
python3 scripts/path_resolver.py \
  --apptag xmlx \
  --workspace /path/to/workspace

# 3. 在指定 应用根目录追加一个代码项
python3 scripts/add_codeitem.py \
  --app-root /path/to \
  --name 审核状态 \
  --items-json '[{"codetext":"草稿","codevalue":"0"},{"codetext":"待审","codevalue":"1"}]'

# 4. 新建 mis 表或追加字段（--create 表示新建）
python3 scripts/add_mis_field.py \
  --app-root /path/to \
  --table customerinfo \
  --create \
  --fields-json '[{"name":"customer_name","description":"客户名称","type":"nvarchar","length":100}]'

# 5. 新建模块/菜单 yml
python3 scripts/add_module.py \
  --app-root /path/to \
  --name 采购立项 \
  --code 9544 \
  --url /purchase/list

# 6. 新建标准动作流 yml
python3 scripts/add_event.py \
  --app-root /path/to \
  --name 获取列表 \
  --sign getDataGridModel \
  --apptag purchaseproject \
  --biz-action Xxx_getDataGridModel \
  --context-class com.epoint.xxx.Context

# 7. 新建工作流（自动生成 5 类节点：开始/申请/审批/结束/浏览 + workflowConfig + workflowPvMisTableSet）
python3 scripts/add_workflow.py \
  --app-root /path/to/<apptag> \
  --name 采购立项审核流程 \
  --approvers 部门审核,主管审核 \
  --material 采购立项申请表 \
  [--sql-tablename formtable20260112164507245]

# 8. 新建页面设计器 Core Schema json
python3 scripts/add_page.py \
  --app-root /path/to \
  --type list \
  --title 采购立项列表 \
  --endpoint /api/purchaseproject \
  --fields-json '[{"name":"project_name","label":"项目名称"}]'

# 9. 列出现有应用资产清单
python3 scripts/inventory_metadata.py \
  --app-root /path/to

# 10. 静态校验某个文件或整个 应用根目录（含跨引用校验）
python3 scripts/validate_yml.py --check-refs /path/to/<apptag>

# 10b. spec v2 严格校验（推荐用于交付前最终校验）
#      已废弃字段（旧驼峰 / tableid / fromMisTableId / fromFieldId）、metadata 残留 → 升级为 error
python3 scripts/validate_yml.py --strict --check-refs /path/to/<apptag>
```

### 资产层硬约束（fail-fast）

- **落盘前确认红线（所有 add_*/update_ 脚本）**：必须先 `--dry-run` 预览内容并展示给用户，用户逐项确认后再加 `--confirm` 落盘；**不加 `--confirm` 一律拒绝写文件**。严禁写批处理循环脚本一次性落多个资产，也严禁手写 YAML/JSON 绕过脚本。
- **超长/中文 JSON 用文件传参**：`--items-file` / `--fields-file` / `--sub-modules-file` / `--query-file`，避免超长内联 JSON 把命令行撑爆导致执行环境挂起。
- `add_codeitem.py` 在新建模式下若未提供 `--items` 或 `--items-json`/`--items-file`，**直接报错退出**。要先建空骨架（不推荐）必须显式加 `--allow-empty`。
- `add_mis_field.py --create` 若未提供至少 1 条业务字段（`--fields-json`/`--fields-file`，主键 rowguid 不计入业务字段），**直接报错退出**。要先建只含主键的骨架（不推荐）必须显式加 `--allow-empty-fields`。
- 这两个 allow 开关默认**禁用**，仅作兜底。AI 不应主动使用，必须先把子项/字段问清楚再调脚本。

### 工作流生成 5 条重点检查（参考 `references/workflow/工作流/index.md`）

1. yaml 结构完整性（顶层 9 个必要元素齐全）
2. 各节点必填项 + 必空字段
3. 节点间关联关系闭合（processversionguid 一致 / transition 引用 / 退回 ↔ workflowConfig / 材料 ↔ 表映射 / vmlid 唯一）
4. 设计红线（节点拆分 / 5 类节点齐全 / 名称固定 / **流转顺序禁止跳过申请节点** / 退回闭环）
5. 必过引擎校验 `python3 scripts/validate_yml.py <yml>`，错误数 = 0 才算交付

任意 1 条不达标不交付：必须先修复或回到对话脚本补全信息，再做下一步。
