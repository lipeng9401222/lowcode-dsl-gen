# 应用配置：appinfo.lowcode.yml

## 1. 资产定位与边界

每个低代码应用 应用根目录下**必备一份** `appinfo.lowcode.yml`，是整个应用的"身份证"。

- 本资产解决：定义应用的身份信息（开发商、应用名称、应用标识、套件归属）与基础配置
- 不在本资产范围内的事：引用其他应用资产的详细配置（由 `appref` 资产负责）；模块、数据模型、页面设计等具体业务定义
- 与 应用根目录的对应关系：`<apptag>/appinfo.lowcode.yml`

### 文件位置

```
<app-root>/appinfo.lowcode.yml
```

固定文件名，不带 type 标识（不像其他 yml 第一行有 `type:`）。

## 2. 文档导航

> 本资产内容量小（R6.3 例外），全部内容承载于本 index.md，无平级子文档。

| 文档 | 用途 | 何时读 |
|------|------|--------|
| 本文件（index.md） | appinfo 完整字段表、对话脚本、校验规则、常见错误 | 创建/修改应用身份信息时 |

## 3. 生成与修改对话速查

### 快速生成

```bash
# 调用脚本一次性生成
python3 scripts/scaffold_app.py \
  --apptag purchaseproject \
  --name "采购立项" \
  --kitid businessprocess \
  --kitname "交易过程套件" \
  --action-root /path/to/xxx-action
```

脚本会：
1. 计算并创建目录
2. 复制 `assets/templates/appinfo.lowcode.yml` 模板
3. 替换占位符
4. 调用 `validate_yml.py` 自检

### 对话脚本（创建新 appinfo）

按自然语言渐进式询问，不要求用户按字段名或 `key=value` 回复。每轮最多问 3 个问题；如果用户一句话已经给出某些信息，直接吸收并继续追问缺失项。

#### 第一组：身份信息（必问）

```
1. 这个应用的英文标识想叫什么？（小写英文，全局唯一；如果没想好，可以根据中文名建议一个）
2. 应用中文名称是什么？（如 采购立项）
3. 这个应用属于哪个套件？如果没有特别说明，建议沿用 businessprocess。
   - businessprocess（交易过程套件）
   - frame.user / frame.message（基础支撑.xxx）
   - 也可以直接说其他套件名称
```

→ 用自然语言复述已理解的信息，不要求用户按字段名确认。

#### 第二组：归属信息（可跳过）

```
4. 开发商标识是否沿用 epoint？
5. 独立单位默认不填；如果确实需要 epoint 或其他独立单位，请直接说明。
6. 是否有租户标识？多租户场景才需要。
```

→ 再次用自然语言复述，不使用快速是/否确认。

#### 第三组：分类与扩展（一般可省略）

```
7. 这个应用要放到哪个分类目录下？多层可用 / 表示；也可以直接说"不分类"。
8. 是否需要引用其他应用资产？可以直接说"不需要"，或说明要引用哪些应用资产。
   - 需要引用 → 进入 appref 流程
   - 不需要 → 直接结束信息收集
```

### 修改已有 appinfo 的对话脚本

```
当前 appinfo.lowcode.yml：
  apptag: xmlx
  applicationname: 项目立项
  kitid: businessprocess
  baseouguid: epoint

你要改哪个字段？
```

只改用户指定的字段，其他保持不动。**不要顺手"优化"用户没动的字段**。

### 校验

调用 `python3 scripts/validate_yml.py <appinfo.lowcode.yml>` 自动校验。

## 4. 与其他资产的引用关系

- 引用其他资产：`refs` 字段可内联引用其他应用资产（通常由 `appref` 资产单独管理）
- 被其他资产引用：所有资产的 `apptag` 必须与 appinfo 中声明的一致；`module`、`event`、`workflow` 等资产隐式依赖 appinfo 的 `apptag` 与 `kitid`
- 跨资产校验脚本：`scripts/validate_yml.py --check-refs`

### `refs` 内联 vs 外置

| 写法 | 适用场景 |
|------|---------|
| 内联在 `appinfo.lowcode.yml` 的 `refs:` 数组里 | 引用项较少（≤ 5 个） |
| 单独放在 `appref.lowcode.yml` | 引用项较多，或团队习惯解耦 |

两种都被支持。**新应用推荐外置**，一致性更好。

---

## 完整字段表

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `developerstag` | string | ✅ | `epoint` | 开发商标识，与目录第一层一致 |
| `applicationname` | string | ✅ | — | 应用名称，中文 |
| `apptag` | string | ✅ | — | 应用标识，**全局唯一**，与目录名一致 |
| `kitid` | string | ✅ | `businessprocess` | 套件标识；多套件时填全路径如 `frame.user` |
| `kitname` | string | ❌ | 空 | 套件名称，通常与 `kitid` 配套填写，便于阅读和展示 |
| `extendappsource` | string | ❌ | 空 | 扩展信息（用于扩展型应用） |
| `organappsource` | string | ❌ | 空 | 扩展的原始应用 |
| `baseouguid` | string | ❌ | 空 | 独立单位标识；需要 `epoint` 或其他值时必须由用户明确提出 |
| `tenantguid` | string | ❌ | 空 | 租户标识 |
| `refs` | array | ❌ | 不写 | 引用其他应用资产；通常单独放 `appref.lowcode.yml`，但也可以内联在这里 |

## 既有应用示例（来自本工程 xmlx 应用）

> 这是历史应用示例，包含 `baseouguid: epoint`。新建应用默认不填 `baseouguid`，除非用户明确要求。

```yaml
# 开发商标识
developerstag: epoint
# 应用名称
applicationname: 项目立项
# 应用标识(全局唯一)
apptag: xmlx
# 套件标识，不填时默认当前组件套件，组件内有多个套件时必填
kitid: businessprocess
# 套件名称
kitname: 交易过程套件
# 扩展信息
extendappsource:
# 扩展的原始应用
organappsource:
baseouguid: epoint
# 引用其他应用的组件实例
refs:
    # 组件标识
  - engineguid: codeitem
    # 组件实例名称（代码项或数据表sql表名）
    name: 行政区划
    # 原应用标识
    sourceAppTag: common
```

## 多套件场景示例

```yaml
developerstag: epoint
applicationname: 统一消息管理
apptag: messagemanage
# 多套件场景，写全路径（用 . 分隔多层）
kitid: frame.message
kitname: 消息套件
baseouguid: ""
```

## 字段细化说明

### `kitid` 的多种取值

参考 `01-vue方案.md` 的「组件定义」章节：

| 场景 | 写法 | 说明 |
|------|------|------|
| 单套件组件 | `kitid: businessprocess` | 来自组件 `kit.id=businessprocess` |
| 多套件组件 | `kitid: user` | 取 `kit.user.id=user`（前缀 `user` 是套件键） |
| 多层套件 | `kitid: frame.user` | 取 `kit.user.id=frame.user`（带点的全路径） |
| 留空 | 不写 `kitid:` | 自动 fallback 当前组件唯一套件，**多套件时报错** |

### `developerstag` 与目录关系

`developerstag` 必须等于目录树里 `META-INF/resources/` 之后的第一层目录名。例如：

```
META-INF/resources/epoint/.../  → developerstag: epoint
META-INF/resources/abccompany/.../  → developerstag: abccompany
```

### `apptag` 与目录关系

`apptag` 必须等于该 yml 所在目录（`<apptag>` 目录）的名字。例如：

```
.../xmlx/appinfo.lowcode.yml → apptag: xmlx
.../purchaseproject/appinfo.lowcode.yml → apptag: purchaseproject
```

不一致时设计器会无法识别应用，**必须严格对齐**。

## 校验规则

| 校验项 | 校验方式 |
|--------|---------|
| `developerstag` 必填且非空 | 字符串校验 |
| `applicationname` 必填且非空 | 字符串校验 |
| `apptag` 必填、全小写英文+数字、无短横线 | 正则 `^[a-z][a-z0-9]*$` |
| `apptag` 与目录名一致 | 路径比对 |
| `kitid` 套件标识，不填时默认当前组件套件，组件内有多个套件时必填（套件多层级嵌套的话，填全路径，如上面的：frame.message/frame.user） | 业务校验 |
| `refs` 中每个元素都有 `engineguid` 和 `name` | 数组项检查 |

## 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| `apptag` 大写或带短横线 | 设计器无法识别 | 改为全小写英文 |
| 文件名拼错 `appinfo.yml`（少 `.lowcode`） | 不会被加载 | 改为 `appinfo.lowcode.yml` |
| `apptag` 与目录名不一致 | 应用展示混乱 | 同步两边 |
| 缺 `kitid` 但组件内有多套件 | 启动报错"无法定位套件" | 显式填 `kitid` |
