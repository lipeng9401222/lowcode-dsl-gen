# lowcode-dsl-gen Skill 五项优化

## 背景

经 grill-me 多轮确认，以下五个问题需要优化：
1. module 的 `auth` 字段应该是数组而非 object（已与开发确认）
2. 所有生成的文件名必须强制小写
3. 所有原子 skill 的 SKILL.md 需要增强多轮确认（grill-me）描述，统一风格
4. `workflowProcessVersion` 为空时校验器必须报错，不能静默跳过
5. npx skills 安装后只进了 `.agents/skills`，没有进各 IDE 目录，需提供一键安装脚本 + 优化 README

---

## 优化一：module `auth` 从 object 改为 array

### 涉及文件

#### [MODIFY] [module.yml](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/assets/templates/module.yml)

将第 92-100 行的 `auth` 从 object 改为 array：

```diff
 # 模块授权
 auth:
-  moduleGuid: "{{GUID}}"
-  allowTo: ""
-  ...
+  - moduleGuid: "{{GUID}}"
+    allowTo: ""
+    ...
```

#### [MODIFY] [add_module.py](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/add_module.py)

将第 113-122 行 `build_sub_module` 中的 `auth` 从 dict 改为 list：

```diff
-        "auth": {
-            "moduleGuid": guid,
-            ...
-        },
+        "auth": [
+            {
+                "moduleGuid": guid,
+                ...
+            },
+        ],
```

#### [MODIFY] [index.md](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/references/module/模块/index.md)

- 第 98 行字段表：`auth` 类型从 `object` 改为 `array`
- 第 101 行标题从 `auth 子对象字段` 改为 `auth 数组项字段`
- 标准示例（第 177-209 行）和简化最小示例中的 `auth` 格式同步更新

#### [MODIFY] [validate_yml.py](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/validate_yml.py)

在 module 校验逻辑中增加：`auth` 必须是 list 类型的校验，以及每个元素的 `moduleGuid` 一致性校验。

---

## 优化二：文件名强制小写

### 涉及文件

#### [MODIFY] [_common.py](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/_common.py)

修改 `safe_filename` 函数（第 414-417 行），添加 `.lower()` 调用：

```diff
 def safe_filename(name: str) -> str:
     """把任意字符串转换为安全的文件名（保留中文，去除特殊字符）."""
-    # 仅替换文件系统不允许的字符
-    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()
+    # 替换文件系统不允许的字符，并强制小写
+    return re.sub(r'[<>:"/\\|?*]', "_", name).strip().lower()
```

#### [MODIFY] [add_page.py](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/add_page.py)

第 203-204 行有独立的 `safe_filename` 副本，同步加 `.lower()`。

#### [MODIFY] [add_mis_field.py](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/add_mis_field.py)

第 216 行 `target = mis_dir / f"{args.table}{ext}"` 改为 `f"{args.table.lower()}{ext}"`，防御大写 `--table` 参数。

---

## 优化三：所有原子 skill 增强多轮确认描述

### 设计原则

参照 workflow skill 的详细程度，为每个原子 skill 增加统一的 `## Grill Gate 追问门禁` 章节，明确：

1. **必问事实**：哪些关键字段/决策点必须在生成前追问确认
2. **可推断事实**：哪些字段可以从仓库推断（需标记 `repo_inferred`）
3. **安全默认值**：哪些字段有安全默认值（需标记 `safe_default`）
4. **禁止猜测**：哪些字段绝不能用 `model_inferred` 静默补齐
5. **确认矩阵**：生成前需确认的事项清单

### 涉及文件（6 个原子 skill）

| 原子 skill | 必问事实 | 禁止猜测 |
|-----------|---------|---------|
| [lowcode-gen-module](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-module/SKILL.md) | 模块名称、编码、是否有子模块 | 模块 code 编码 |
| [lowcode-gen-codeitem](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-codeitem/SKILL.md) | 代码项名称、所有子项 | 子项 codevalue |
| [lowcode-gen-mis](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-mis/SKILL.md) | 表名、中文名、字段列表 | 字段名称和类型 |
| [lowcode-gen-event](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-event/SKILL.md) | 动作流名称、触发类型、bizAction | bizAction、contextClass |
| [lowcode-gen-page](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-page/SKILL.md) | 页面标题、pagetag、类型 | 字段-组件映射 |
| [lowcode-gen-app-shell](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-app-shell/SKILL.md) | apptag、应用名称 | apptag、developerstag |

> [!NOTE]
> `lowcode-gen-workflow` 已有充分的多轮确认机制（含确认矩阵），只做章节标题统一微调。

---

## 优化四：workflowProcessVersion 不能为空

### 问题根因

从截图看到实际生成的 workflow.yml 中 `workflowProcessVersion:` 为空（第 616-617 行），导致流程版本信息丢失。

代码分析：
- [add_workflow.py L1464-1482](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/add_workflow.py#L1464-L1482) ✅ 正常生成了完整的 `workflowProcessVersion`
- [workflow.yml 模板 L355-372](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/assets/templates/workflow.yml#L355-L372) ✅ 模板有完整定义
- [validate_yml.py L914-918](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/validate_yml.py#L914-L918) ❌ **当 `workflowProcessVersion` 为 None/空时，静默回退到 `{}`，没有报错**
- [update_workflow.py L63-65](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/update_workflow.py#L63-L65) ✅ 已有空值检查，会抛 ValueError

> [!IMPORTANT]
> 脚本本身能正确生成 `workflowProcessVersion`，但问题可能来自 AI 绕过脚本直接手写 YAML、或其他未知路径。**无论来源如何**，校验器必须能拦截这种异常。

### 涉及文件

#### [MODIFY] [validate_yml.py](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/scripts/validate_yml.py)

**第 914-918 行**：当 `workflowProcessVersion` 为 None 或非 dict 时，从静默回退改为报 error：

```diff
     pversion_obj = (
         version.get("workflowProcessVersion")
         or version.get("WorkflowProcessVersion")
-        or {}
     )
+    if not isinstance(pversion_obj, dict) or not pversion_obj:
+        result.err(p, "workflowVersion.workflowProcessVersion 缺失或为空，"
+                      "必须包含 processversionguid/processguid/version 等流程版本信息")
+        return result  # 后续字段校验依赖此对象，直接返回
```

同时增加 **必填字段校验**：
- `processversionguid` 不能为空
- `processguid` 不能为空
- `version` 不能为空（如 `V1`）
- `status` 必须为 10

#### [MODIFY] [SKILL.md（调度器）](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/SKILL.md)

在 **Workflow / Event Split** 章节或 **红线** 中强调：
- `workflowProcessVersion` 是流程版本的核心身份信息，**绝不能为空**
- 必须包含 `processversionguid`、`processguid`、`version`、`status` 等必填字段

#### [MODIFY] [lowcode-gen-workflow/SKILL.md](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/skills/lowcode-gen-workflow/SKILL.md)

在 **Red Lines 红线** 中新增：
```
- workflowProcessVersion 绝不能为空，必须包含 processversionguid、processguid、version、status、designversion 等完整版本信息。
```

---

## 优化五：一键安装脚本 + README 安装指引优化

### 问题根因

`npx skills add` 使用 symlink 模式时，可能因文件系统权限、工具版本兼容性等问题，导致 symlink 未能创建到目标 IDE 目录（如 `.claude/skills`），内容只落在 `.agents/skills` 中。

### 涉及文件

#### [NEW] [bin/setup.sh](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/bin/setup.sh)

一键安装脚本，功能：
1. 自动检测用户已安装的 IDE/CLI 工具（通过检测配置目录是否存在）
2. 将当前 skill 目录软链到各工具的 skills 目录
3. 支持的工具映射表：

| 工具 | 目标目录 |
|-----|---------|
| Claude Code | `~/.claude/skills/lowcode-dsl-gen` |
| Cursor | `~/.cursor/skills/lowcode-dsl-gen` |
| Codex CLI | `~/.codex/skills/lowcode-dsl-gen` |
| Windsurf | `~/.codeium/windsurf/skills/lowcode-dsl-gen` |
| CodeBuddy | `~/.codebuddy/skills/lowcode-dsl-gen` |
| Antigravity | `~/.gemini/config/skills/lowcode-dsl-gen` |
| Amp | `~/.amp/skills/lowcode-dsl-gen` |
| AstrBot | `~/data/skills/lowcode-dsl-gen` |
| Augment | `~/.augment/skills/lowcode-dsl-gen` |

4. 脚本支持参数：
   - 无参数：自动检测已安装的工具并全部安装
   - `--agent <name>`：只安装到指定工具
   - `--list`：列出支持的工具
   - `--check`：检查各工具目录是否已有 skill
5. 安装前检测目标是否已存在（避免覆盖）
6. 安装后输出验证结果

#### [MODIFY] [README.md](file:///Users/juanjuan/Workspace/epoint/epoint-lowcode-parent/docs/skills/lowcode-dsl-gen/README.md)

重构安装章节：
1. **方式一**改为 `bin/setup.sh` 一键安装（推荐）
2. **方式二**保留 `npx skills add` 但默认推荐 `--copy` 模式
3. **方式三**保留手动软链作为兜底
4. 增加安装后校验步骤

---

## 验证计划

### 自动化验证

```bash
# 1. 验证模板 auth 格式
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from _common import yaml_load_str
t = open('assets/templates/module.yml').read()
data = yaml_load_str(t.replace('{{CODE}}','9999').replace('{{NAME}}','test').replace('{{GUID}}','00000000-0000-0000-0000-000000000000').replace('{{CREATE_TIME}}','2026-01-01').replace('{{UPDATE_TIME}}','2026-01-01'))
assert isinstance(data['auth'], list), f'auth 应为 list，实际为 {type(data[\"auth\"])}'
print('✅ 模板 auth 格式正确')
"

# 2. 验证 safe_filename 小写
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from _common import safe_filename
assert safe_filename('ProjectApply') == 'projectapply'
assert safe_filename('IPD管理') == 'ipd管理'
print('✅ safe_filename 小写规则正确')
"

# 3. 验证 workflowProcessVersion 空值校验
# 构造一个 workflowProcessVersion 为空的 yml，validate_yml.py 应报 error
python3 scripts/validate_yml.py <test-empty-wpv.yml>

# 4. 验证 setup.sh 语法
bash -n bin/setup.sh && echo '✅ setup.sh 语法正确'
```

### 人工验证

- 检查所有修改后的 SKILL.md 文件，确认 Grill Gate 章节风格统一
- 检查参考文档中的 auth 示例格式是否全部同步更新
- 运行 `bin/setup.sh --check` 确认安装检测逻辑正确
