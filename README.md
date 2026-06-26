# lowcode-dsl-gen

新点（Epoint）低代码线下应用 YAML 元数据生成与维护 Skill。运行时由 IDE/CLI Agent 读取 `SKILL.md` 执行；本 README 仅供人查看。

## 安装到各 IDE/CLI

### 方式一：用 Skills CLI 安装（推荐，可定向到指定 IDE）

本 skill 可用 [vercel-labs/skills](https://github.com/vercel-labs/skills) 的 `npx skills add` 安装。
用 `-a/--agent` 指定目标 IDE，避免「明明选了 Claude 却没装进 `.claude/skills`」的问题：

> 前提：仓库根目录需有 `SKILL.md`。若该 skill 不在仓库根（例如放在子目录或一个仓库里放了多个 skill），用 `--skill <skill 名>` 指定，例如 `npx skills add lipeng9401222/lowcode-dsl-gen --skill lowcode-dsl-gen -a claude-code`。

```bash
# 只装到 Claude Code
npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code

# 同时装到多个 agent（重复 -a）
npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code -a cursor -a codex

# 全局安装（用户级，跨项目可用）：加 -g
npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code -g
```

> **关于安装目录（重要）**：Skills CLI 默认走 **symlink 模式**——先把规范副本放到
> `.agents/skills/<skill>`（全局是 `~/.agents/skills/<skill>`），再从各 IDE 目录
> （`.claude/skills/`、`.cursor/skills/` 等）**软链**回这个规范副本。所以你在
> `.claude/skills/` 下看到的通常是一个**软链**，而不是实体副本，这是正常设计（单一真相源，便于统一更新）。
>
> 如果选了 Claude 却发现 `~/.claude/skills/` 下既没有实体也没有软链、内容只进了
> `~/.agents/skills/`，多半是 symlink 创建失败回退到了 copy 模式，或命中了
> [issue #744](https://github.com/vercel-labs/skills/issues/744)。此时改用 `--copy`
> 强制复制模式，把实体副本直接写进每个 IDE 目录：
>
> ```bash
> npx skills add lipeng9401222/lowcode-dsl-gen -a claude-code --copy
> ```
>
> 安装后可用 `npx skills list` 查看各 agent 是否都装上了。

### 方式二：手动软链（最稳妥的兜底）

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

v1.4.3 — 默认资产收敛 + 安装文档定向化。`scaffold_app.py` 默认只创建 5 个核心目录（codeitem/mis/module/workflow/page），`event`（动作流）、`api`（接口元数据）改为按需创建，分别需 `--with-event` / `--with-api`；SKILL.md 增加「API / Event 按需门禁」，未明确要求时不生成 event/api 资产。README 安装段落改为优先使用 Skills CLI 定向安装（`-a claude-code` / `--copy`），并补充 `.agents/skills` 软链机制说明与排查指引。

v1.4.2 — 工作流生成规范加固。`workflow` 必须通过 `scripts/add_workflow.py` 生成骨架；`validate_yml.py --strict` 强校验 `workflowVersion` 对象结构、`mistablesetguid`、`workflowProcessVersion.version` 与必填字段；`lint_skill.py --strict` 扫描 workflow 知识库/模板/fixture，防止旧字段和手写结构重新污染正例。

v1.4.1 — 计划文档追溯增强。`.lowcode-plans/<apptag>-plan.md` 从第一轮开始持续维护，作为全过程审计台账；无论是否开启 Plan Mode，都必须记录每轮问题、选项、用户回复、解析结果和确认状态，并保留 `对话确认记录 / 阶段确认结果 / 生成计划 / 执行与校验记录` 四个章节。

v1.4.0 — spec v2 收紧。统一字段命名为全小写下划线（去掉旧驼峰，如 `isDefault → is_default` / `mobileHandleType → mobilehandletype` / `subProMultiTransctorMode → subpromultitransctormode`）；删除 `tableid` 字段（引擎根据 `sql_tablename` 自动绑定）；workflowContext 用 `fromsqltablename + fromfieldname` 取代 `fromMisTableId / fromFieldId`；脚本（`scaffold_app.py / add_*.py / path_resolver.py`）对 `--app-root` 包含 `/metadata/` 段做 fail-fast；`validate_yml.py --strict` 把已废弃字段、`metadata/` 残留、旧驼峰键统一升级为 error。

v1.3.0 — 统一新建资产文件名为 `名字.类型.yml`，pagedesigne 改为 `.pagedesigne.yml`（内容仍为 Core Schema JSON 文本），MIS 表名禁止下划线，整应用阶段顺序调整为 `pagedesigne → workflow → event`，并补齐工作流扩展能力与 ruleGuid 动作流引用校验。
