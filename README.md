# lowcode-dsl-gen

新点（Epoint）低代码线下应用 YAML 元数据生成与维护 Skill。运行时由 IDE/CLI Agent 读取 `SKILL.md` 执行；本 README 仅供人查看。

## 安装到各 IDE/CLI

### 方式一：一键安装脚本（推荐）

使用 `bin/setup.sh` 自动检测已安装的 IDE/CLI 工具并创建软链：

```bash
# 自动检测并安装到所有已安装的工具
./bin/setup.sh

# 只安装到 Claude Code
./bin/setup.sh --agent claude-code

# 检查安装状态
./bin/setup.sh --check

# 列出支持的工具
./bin/setup.sh --list

# 卸载
./bin/setup.sh --uninstall
```

支持的工具：Claude Code、Cursor、Codex CLI、Windsurf、CodeBuddy、Antigravity、Amp、Augment、OpenCode、Zed、Warp。

### 方式二：用 Skills CLI 安装

用 [vercel-labs/skills](https://github.com/vercel-labs/skills) 的 `npx skills add` 安装。
**建议使用 `--copy` 模式**以避免 symlink 创建失败的问题：

```bash
# 推荐：--copy 模式直接写实体副本到各 IDE 目录
npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code --copy

# 同时装到多个 agent
npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code -a cursor -a codex --copy

# 全局安装：加 -g
npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code -g --copy
```

> **关于默认 symlink 模式的已知问题**：Skills CLI 默认走 symlink 模式——先把副本放到
> `.agents/skills/<skill>`，再从各 IDE 目录软链回去。但 symlink 可能因权限或工具版本
> 问题创建失败，导致只有 `.agents/skills/` 下有内容而 `.claude/skills/` 下没有。
> 使用 `--copy` 可避免此问题。安装后用 `npx skills list` 或 `./bin/setup.sh --check` 验证。

### 方式三：手动软链（兜底）

不依赖任何 CLI，直接把本目录软链到对应工具的 skills 目录：

```bash
# Codex CLI
ln -s "$PWD" ~/.codex/skills/lowcode-dsl-gen
# Claude Code
ln -s "$PWD" ~/.claude/skills/lowcode-dsl-gen
# Windsurf
ln -s "$PWD" ~/.codeium/windsurf/skills/lowcode-dsl-gen
# CodeBuddy
ln -s "$PWD" ~/.codebuddy/skills/lowcode-dsl-gen
# Antigravity
ln -s "$PWD" ~/.gemini/config/skills/lowcode-dsl-gen
```

也可在 `~/.codex/config.toml` 添加 `[[skills]] path = "<本目录绝对路径>"` 显式注册。

## 行为约定

- 详尽指令见 `SKILL.md`
- 各资产字段白名单见 `references/<asset>/<中文目录>/index.md`
- 通用约定见 `references/conventions.md`

## 依赖

- Python 3.10+
- PyYAML（按需 `pip install pyyaml`）

## 版本

v1.4.5 — 落盘前确认硬闸（脚本层强制逐资产逐文件确认）。修复"AI 一股脑生成全部资产、未逐项人工核对"问题：为 `add_codeitem.py / add_mis_field.py / add_module.py / add_page.py` 补齐 `--dry-run`（原先缺失，无法预览）；全部 7 个落盘脚本（含 `add_event/add_workflow/update_workflow`）统一加 `--confirm` 硬闸——不加 `--confirm` 一律拒绝写文件，必须先 `--dry-run` 预览。新增 `--items-file / --fields-file / --sub-modules-file / --query-file` 文件传参，避免超长中文 JSON 撑爆命令行导致执行环境挂起。SKILL.md「落盘前确认红线」明令禁止批处理循环脚本、禁止手写 YAML/JSON 绕过脚本、禁止用一句"计划已批准"当全量落盘许可。

v1.4.4 — 恢复落盘前人工确认门禁。修复「资产被一股脑生成、未经人工核对」问题：`SKILL.md` 新增「落盘前确认红线」（所有模式强制：无 pending open question、显式批准、禁止 model_inferred 内容落盘、逐资产可追溯）；调度流程从「单次批准→批量落盘」改为多资产/整应用「分阶段逐资产确认」，单 workflow/event 快速通道保留提速；`whole-app` 与多资产 `existing-app` 落盘前重新强制 `validate_plan.py`。`validate_plan.py` 与 IR 解耦：缺 `ir.yml` 不再硬失败（IR 仍可选），改由主计划资产队列表 + 子计划完整性兜底审计，并新增对应回归用例。

v1.4.3 — 默认资产收敛 + 安装文档定向化。`scaffold_app.py` 默认只创建 5 个核心目录（codeitem/mis/module/workflow/page），`event`（动作流）、`api`（接口元数据）改为按需创建，分别需 `--with-event` / `--with-api`；SKILL.md 增加「API / Event 按需门禁」，未明确要求时不生成 event/api 资产。README 安装段落改为优先使用 Skills CLI 定向安装（`-a claude-code` / `--copy`），并补充 `.agents/skills` 软链机制说明与排查指引。

v1.4.2 — 工作流生成规范加固。`workflow` 必须通过 `scripts/add_workflow.py` 生成骨架；`validate_yml.py --strict` 强校验 `workflowVersion` 对象结构、`mistablesetguid`、`workflowProcessVersion.version` 与必填字段；`lint_skill.py --strict` 扫描 workflow 知识库/模板/fixture，防止旧字段和手写结构重新污染正例。

v1.4.1 — 计划文档追溯增强。`.lowcode-plans/<apptag>-plan.md` 从第一轮开始持续维护，作为全过程审计台账；无论是否开启 Plan Mode，都必须记录每轮问题、选项、用户回复、解析结果和确认状态，并保留 `对话确认记录 / 阶段确认结果 / 生成计划 / 执行与校验记录` 四个章节。

v1.4.0 — spec v2 收紧。统一字段命名为全小写下划线（去掉旧驼峰，如 `isDefault → is_default` / `mobileHandleType → mobilehandletype` / `subProMultiTransctorMode → subpromultitransctormode`）；删除 `tableid` 字段（引擎根据 `sql_tablename` 自动绑定）；workflowContext 用 `fromsqltablename + fromfieldname` 取代 `fromMisTableId / fromFieldId`；脚本（`scaffold_app.py / add_*.py / path_resolver.py`）对 `--app-root` 包含 `/metadata/` 段做 fail-fast；`validate_yml.py --strict` 把已废弃字段、`metadata/` 残留、旧驼峰键统一升级为 error。

v1.3.0 — 统一新建资产文件名为 `名字.类型.yml`，pagedesigne 改为 `.pagedesigne.yml`（内容仍为 Core Schema JSON 文本），MIS 表名禁止下划线，整应用阶段顺序调整为 `pagedesigne → workflow → event`，并补齐工作流扩展能力与 ruleGuid 动作流引用校验。
