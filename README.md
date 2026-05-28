# lowcode-dsl-gen

新点（Epoint）低代码线下应用 YAML 元数据生成与维护 Skill。运行时由 IDE/CLI Agent 读取 `SKILL.md` 执行；本 README 仅供人查看。

## 安装到各 IDE/CLI

把本目录注册到对应工具的 skills 目录（推荐用软链以便统一更新）：

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

v1.4.0 — spec v2 收紧。统一字段命名为全小写下划线（去掉旧驼峰，如 `isDefault → is_default` / `mobileHandleType → mobilehandletype` / `subProMultiTransctorMode → subpromultitransctormode`）；删除 `tableid` 字段（引擎根据 `sql_tablename` 自动绑定）；workflowContext 用 `fromsqltablename + fromfieldname` 取代 `fromMisTableId / fromFieldId`；脚本（`scaffold_app.py / add_*.py / path_resolver.py`）对 `--app-root` 包含 `/metadata/` 段做 fail-fast；`validate_yml.py --strict` 把已废弃字段、`metadata/` 残留、旧驼峰键统一升级为 error。

v1.3.0 — 统一新建资产文件名为 `名字.类型.yml`，pagedesigne 改为 `.pagedesigne.yml`（内容仍为 Core Schema JSON 文本），MIS 表名禁止下划线，整应用阶段顺序调整为 `pagedesigne → workflow → event`，并补齐工作流扩展能力与 ruleGuid 动作流引用校验。
