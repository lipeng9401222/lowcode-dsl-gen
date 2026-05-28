# 模块：module yml

## 1. 资产定位与边界

`module` 即"**菜单/模块定义**"，对应平台上左侧导航树/顶部菜单的某一个节点。一个 module yml 描述一个**根模块 + 子模块树**，支持多级 `items` 嵌套。

- 与 应用根目录的对应关系：`<apptag>/module/<模块名>.module.yml`
- 不在本资产范围内的事：
  - 模块所指向的页面（`url`/`routePath`）由前端工程或 `pagedesigne` 提供
  - 跨应用挂载/引用模块属于 `appref`，详见 `references/appref/引用配置/index.md`
  - 应用级元信息（apptag、版本号）属于 `appinfo`，详见 `references/appinfo/应用配置/index.md`

## 2. 文档导航

> 本资产的所有内容均承载于本 index.md（R6.3 例外为 appinfo/appref；其他资产若超 600 行需拆出平级文档）。
> 章节速查：
> - § 文件位置与命名：见下文「[文件位置与命名](#文件位置与命名)」
> - § 完整字段表（根模块 / auth / items 子模块）：见下文「[完整字段表](#完整字段表)」
> - § 标准示例 + 简化最小示例：见下文「[标准示例（两层嵌套）](#标准示例两层嵌套)」「[简化最小示例](#简化最小示例)」
> - § 字段填充策略（必问 / 推荐 / 自动生成 / 可省略）：见下文「[字段填充策略](#字段填充策略)」
> - § 字段细节（code 编码规则 / isVue 与 routePath / auth）：见下文「[字段细节](#字段细节)」
> - § 校验规则与常见错误：见下文「[校验规则](#校验规则)」「[常见错误](#常见错误)」

## 3. 生成与修改对话速查

> 详细对话脚本：见下文「[对话脚本（创建新模块）](#对话脚本创建新模块)」「[修改已有模块](#修改已有模块)」与脚本 cheatsheet `references/directory-structure.md`。

## 4. 与其他资产的引用关系

- 引用其他资产：
  - `url` / `routePath` 指向前端页面（不强约束 yml 资产，但通常对应 `pagedesigne` 或自定义 vue）
- 被其他资产引用：
  - `appref` 通过 `engineguid: module` + 模块 `guid` / `name` 引用模块（实现跨应用菜单挂载）
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs <app-root>`

---

`module` 即"菜单/模块定义"，对应平台上左侧导航树/顶部菜单的某一个节点。一个 module yml 描述一个**根模块 + 子模块树**，支持多级 `items` 嵌套。

## 文件位置与命名

```
<app-root>/module/<模块名>.module.yml
```

推荐中文文件名（如 `主体管理.module.yml`）。

## 完整字段表

### 根模块字段（顶层）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定 `module` |
| `code` | string | ✅ | 模块编码（4-8 位字符串） |
| `name` | string | ✅ | 模块名称（中文，UI 显示） |
| `guid` | string | ✅ | 模块标识 UUIDv4 |
| `intro` | string | ❌ | 模块介绍 |
| `menuName` | string | ❌ | 菜单名称（如与 name 不同） |
| `url` | string | ❌ | 模块地址（前端页面路径） |
| `orderNumber` | int | ❌ | 排序号 |
| `isDisable` | int | ❌ | 是否禁用 (0/1) |
| `isBlank` | int | ❌ | 是否新窗口打开 (0/1) |
| `bigIconAddress` | string | ❌ | 大图标 URL |
| `smallIconAddress` | string | ❌ | 小图标 URL |
| `moduleType` | string | ❌ | 模块类型 |
| `isAddOu` | int | ❌ | 是否增加独立单位 (0/1) |
| `parentGuid` | string | ❌ | 父模块标识（根模块为空） |
| `isFromSoa` | int | ❌ | 是否来源于 SOA (0/1) |
| `isUse` | int | ❌ | 是否启用 (0/1) |
| `i18nKey` | string | ❌ | 国际化 key |
| `isReserved` | int | ❌ | 是否保留 (0/1) |
| `whitelist` | string | ❌ | 白名单 |
| `tenantGuid` | string | ❌ | 租户标识 |
| `moduleSource` | string | ❌ | 模块来源 |
| `isSwitchApp` | int | ❌ | 是否切换应用 (0/1) |
| `showInHomepage` | string | ❌ | 是否首页显示 |
| `moduleSystem` | string | ❌ | 模块所属系统 |
| `newBigIconAddress` | string | ❌ | 新版大图标 |
| `isKeepAlive` | int | ❌ | 是否缓存 (0/1) |
| `isOnlyInRoute` | int | ❌ | 是否仅在路由中显示 (0/1) |
| `routePath` | string | ❌ | 路由路径 |
| `routePathName` | string | ❌ | 路由名称 |
| `isVue` | int | ❌ | 是否 VUE 模块 (0/1) |
| `isOpenToTenant` | string | ❌ | 是否开放给租户 |
| `description` | string | ❌ | 模块描述 |
| `applicationGuid` | string | ❌ | 应用标识 |
| `applicationAppGuid` | string | ❌ | 应用 App 标识 |
| `createTime` | string | ❌ | 创建时间 |
| `updateTime` | string | ❌ | 更新时间 |
| `useDescription` | string | ❌ | 使用说明 |
| `referenceModuleGuid` | string | ❌ | 引用模块标识 |
| `importance` | int | ❌ | 重要程度 |
| `isTopMenu` | int | ❌ | 是否顶部菜单 (0/1) |
| `isQuickCreate` | int | ❌ | 是否快捷创建 (0/1) |
| `iconType` | string | ❌ | 图标类型 |
| `shortPath` | string | ❌ | 短路径 |
| `auth` | object | ❌ | 模块授权（见下） |
| `items` | array | ❌ | 子模块数组（结构与根相同） |

### auth 子对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `moduleGuid` | string | 模块标识（=根 guid 或 items 中模块的 guid） |
| `allowTo` | string | 授权对象（角色/用户 GUID） |
| `allowType` | string | 授权类型（如 `Role`） |
| `isFromOa` | int | 是否来源 OA (0/1) |
| `isFromSoa` | int | 是否来源 SOA (0/1) |
| `rightType` | string | 权限类型 |
| `moduleRightMode` | string | 模块权限模式 |
| `tenantGuid` | string | 租户标识 |

### items 子项字段

`items` 中每项就是一个子模块，**字段结构与根模块完全相同**，靠 `parentGuid` 字段指向父模块的 `guid` 来构建树结构。

## 标准示例（两层嵌套）

```yaml
# 固定标识
type: module

# 模块code
code: "9544"
# 模块介绍
intro: ""
# 模块名称
name: "主体管理"
# 模块标识
guid: "83d5faef-403c-4fd0-ab08-12549318d7fb"
# 菜单名称
menuName: ""
# 模块地址
url: ""
# 排序号
orderNumber: 0
# 是否禁用
isDisable: 0
# 是否新窗口打开
isBlank: 0
bigIconAddress: ""
smallIconAddress: ""
moduleType: ""
isAddOu: 0
parentGuid: ""
isFromSoa: 0
isUse: 0
i18nKey: ""
isReserved: 0
whitelist: ""
tenantGuid: ""
moduleSource: ""
isSwitchApp: 0
showInHomepage: ""
moduleSystem: ""
newBigIconAddress: ""
isKeepAlive: 0
isOnlyInRoute: 0
routePath: ""
routePathName: ""
isVue: 0
isOpenToTenant: ""
description: ""
applicationGuid: ""
applicationAppGuid: ""
createTime: ""
updateTime: ""
useDescription: ""
referenceModuleGuid: ""
importance: 0
isTopMenu: 0
isQuickCreate: 0
iconType: ""
shortPath: ""

# 模块授权
auth:
  moduleGuid: "83d5faef-403c-4fd0-ab08-12549318d7fb"
  allowTo: ""
  allowType: ""
  isFromOa: 0
  isFromSoa: 0
  rightType: ""
  moduleRightMode: ""
  tenantGuid: ""

items:
  - code: "95440001"
    name: "采购人管理"
    guid: "84f10e3a-d861-4b3f-8df9-9464db53a17f"
    menuName: ""
    url: ""
    orderNumber: 0
    isDisable: 0
    isBlank: 0
    parentGuid: "83d5faef-403c-4fd0-ab08-12549318d7fb"   # ← 指向父
    isFromSoa: 0
    isUse: 0
    # ... 其他字段同根模块
    auth:
      moduleGuid: "84f10e3a-d861-4b3f-8df9-9464db53a17f"
      allowTo: "22e58fe5-74b1-45ad-94cf-398a0349ae44"
      allowType: "Role"
      isFromOa: 0
      isFromSoa: 0
      rightType: ""
      moduleRightMode: ""
      tenantGuid: ""
```

## 简化最小示例

仅描述基础结构，可省略 `auth` 和大部分可选字段（设计器解析时会用默认值补齐）：

```yaml
type: module

code: "9544"
name: "主体管理"
guid: "83d5faef-403c-4fd0-ab08-12549318d7fb"
url: ""
orderNumber: 0
isDisable: 0
isUse: 0
parentGuid: ""

items:
  - code: "95440001"
    name: "采购人管理"
    guid: "84f10e3a-d861-4b3f-8df9-9464db53a17f"
    parentGuid: "83d5faef-403c-4fd0-ab08-12549318d7fb"
    url: "/epoint/purchaseproject/purchase_user_list"
    orderNumber: 1
    isDisable: 0
    isUse: 1
    isVue: 1
    routePath: "/epoint/purchaseproject/purchase_user_list"
    routePathName: "purchase_user_list"
```

## 对话脚本（创建新模块）

### 第一步：根模块基本信息

```
你要创建什么模块？
1. 模块中文名称是什么？（如 主体管理）
2. 模块编码 code 用哪个？（4-8 位数字字符串，如 9544；如果有现有编码规则，按工程约定）
3. 是否有模块图标地址？没有可以省略。
4. 模块是否启用？默认按启用处理。
```

### 第二步：是否有子模块

```
如果该模块下面有子菜单，请直接列出子菜单；没有可以说"没有子菜单"。
每个子模块需要：
- 名称
- code（基于父 code + 4 位序号，如 95440001）
- 路由地址（如 /epoint/xxx/yyy_list）
- 是否 Vue 模块（默认按 Vue 新方案处理）
```

### 第三步：是否需要权限设置

```
如果要给模块加权限，请说明授权对象和授权类型；不需要可以说"暂不配置权限"。
需要的信息：
- 授权对象 GUID（角色或用户的 GUID）
- 授权类型（默认 Role）
```

### 第四步：创建计划 + 明确批准

- 根模块 GUID：自动生成 UUIDv4
- 每个子模块 GUID：自动生成
- `parentGuid`：自动填为父模块 GUID
- 先展示模块结构、GUID 生成规则、目标文件路径
- 用户明确回复"批准创建"后再落盘 + 校验

## 修改已有模块

```
当前 主体管理.module.yml 子菜单：
  - 采购人管理 (code=95440001, isUse=1)
  - 供应商管理 (code=95440002, isUse=1)

你要：
1. 添加新子菜单
2. 删除某子菜单（哪个？）
3. 修改某子菜单（名称/路由/权限/启用状态）
4. 调整子菜单顺序（orderNumber）
```

## 字段填充策略

### 必问的属性

- `name`、`code`、是否有子菜单

### 强烈推荐的属性

- `url` 或 `routePath` / `routePathName`（前端路由）
- `isVue: 1`（新方案推荐都用 Vue 模块）
- `isUse: 1`（启用）
- `orderNumber`（决定显示顺序）

### 自动生成的属性

- `guid` / `parentGuid`：UUIDv4 自动生成
- `createTime` / `updateTime`：当前时间
- 其他默认值：参考"简化最小示例"

### 可省略的属性

未在示例中出现的字段（如 `i18nKey`、`whitelist`、`isReserved` 等）一般默认空字符串或 0，**可以不写**，渲染器自动补默认。

## 字段细节

### `code` 编码规则

- 根模块：4 位数字（如 `9544`）
- 一级子模块：根 + 4 位序号（如 `95440001`）
- 二级子模块：父 + 4 位序号（如 `944000010001`）

### `isVue` 与 `routePath`

- 新方案推荐 `isVue: 1`
- `routePath` 写完整前端路径，如 `/epoint/purchaseproject/purchase_user_list`
- `routePathName` 是路由 name（用于编程式跳转），通常等于 vue 文件名（去后缀）

### `auth` 字段

- `auth` 描述**默认权限**配置；实际权限可在线上界面调整
- `moduleGuid` 必须等于该层级模块自己的 `guid`
- `allowType: Role` 表示授权给角色；`allowTo` 是角色 GUID

## 校验规则

| 校验项 | 校验方式 |
|-------|---------|
| 第一行 `type: module` | 字符串 |
| `code` 是数字字符串 | 正则 |
| `guid` 是合法 UUIDv4 | UUID 校验 |
| `parentGuid` 在 items 中指向已存在的 guid（树结构闭合） | 引用校验 |
| `auth.moduleGuid` 与对应模块的 guid 相同 | 一致性 |
| `isUse`/`isDisable`/`isBlank` 等是 0 或 1 | 枚举 |

## 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| `code: 9544`（无引号）解析为整数 | 后端字符串比对失败 | 改为 `code: "9544"` |
| `guid` 为空字符串 | 模块无法保存 | 自动生成 UUID |
| 子模块 `parentGuid` 写错 | 菜单树结构断 | 同步根模块 guid |
| 多层嵌套时漏 `parentGuid` | 子模块挂在根级 | 显式写 parentGuid |
| `isVue: "1"`（字符串） | 前端解析异常 | 改为整数 `isVue: 1` |
