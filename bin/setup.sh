#!/usr/bin/env bash
# setup.sh — lowcode-dsl-gen skill 一键安装脚本
# 自动检测已安装的 IDE/CLI 工具，将 skill 目录软链到各工具的 skills 目录
#
# 用法：
#   ./bin/setup.sh              # 自动检测并安装到所有已安装的工具
#   ./bin/setup.sh --agent claude-code   # 只安装到指定工具
#   ./bin/setup.sh --list       # 列出支持的工具
#   ./bin/setup.sh --check      # 检查各工具是否已安装此 skill
#   ./bin/setup.sh --uninstall  # 移除所有已安装的软链

set -euo pipefail

SKILL_NAME="lowcode-dsl-gen"

# 定位 skill 根目录（脚本所在目录的父目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 工具 → skills 目录映射
# 格式：工具名:配置目录:skills子目录
declare -a AGENT_MAP=(
  "claude-code:${HOME}/.claude:skills"
  "cursor:${HOME}/.cursor:skills"
  "codex:${HOME}/.codex:skills"
  "windsurf:${HOME}/.codeium/windsurf:skills"
  "codebuddy:${HOME}/.codebuddy:skills"
  "antigravity:${HOME}/.gemini/config:skills"
  "amp:${HOME}/.amp:skills"
  "augment:${HOME}/.augment:skills"
  "opencode:${HOME}/.opencode:skills"
  "zed:${HOME}/.zed:skills"
  "warp:${HOME}/.warp:skills"
)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}ℹ${NC} $*"; }
ok()    { echo -e "${GREEN}✅${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠️${NC} $*"; }
err()   { echo -e "${RED}❌${NC} $*"; }

# 解析工具配置
parse_agent() {
  local entry="$1"
  AGENT_NAME="${entry%%:*}"
  local rest="${entry#*:}"
  AGENT_CONFIG_DIR="${rest%%:*}"
  AGENT_SKILLS_SUBDIR="${rest##*:}"
  AGENT_SKILLS_DIR="${AGENT_CONFIG_DIR}/${AGENT_SKILLS_SUBDIR}"
  AGENT_TARGET="${AGENT_SKILLS_DIR}/${SKILL_NAME}"
}

# 检测工具是否已安装（配置目录存在）
is_agent_installed() {
  local entry="$1"
  parse_agent "$entry"
  [[ -d "$AGENT_CONFIG_DIR" ]]
}

# 安装到指定工具
install_to_agent() {
  local entry="$1"
  parse_agent "$entry"

  if [[ -L "$AGENT_TARGET" ]]; then
    local existing_link
    existing_link="$(readlink "$AGENT_TARGET")"
    if [[ "$existing_link" == "$SKILL_ROOT" ]]; then
      ok "$AGENT_NAME: 已安装（软链指向正确）"
      return 0
    else
      warn "$AGENT_NAME: 已存在软链但指向不同位置: $existing_link"
      warn "  移除旧链并重新创建..."
      rm "$AGENT_TARGET"
    fi
  elif [[ -e "$AGENT_TARGET" ]]; then
    warn "$AGENT_NAME: 目标已存在且不是软链: $AGENT_TARGET"
    warn "  跳过。如需覆盖请先手动删除。"
    return 1
  fi

  # 创建 skills 目录（如果不存在）
  mkdir -p "$AGENT_SKILLS_DIR"

  # 创建软链
  ln -s "$SKILL_ROOT" "$AGENT_TARGET"
  ok "$AGENT_NAME: 安装成功 → $AGENT_TARGET"
}

# 卸载
uninstall_from_agent() {
  local entry="$1"
  parse_agent "$entry"

  if [[ -L "$AGENT_TARGET" ]]; then
    rm "$AGENT_TARGET"
    ok "$AGENT_NAME: 已移除"
  elif [[ -e "$AGENT_TARGET" ]]; then
    warn "$AGENT_NAME: $AGENT_TARGET 不是软链，跳过"
  else
    info "$AGENT_NAME: 未安装"
  fi
}

# 检查安装状态
check_agent() {
  local entry="$1"
  parse_agent "$entry"

  if ! [[ -d "$AGENT_CONFIG_DIR" ]]; then
    echo "  $AGENT_NAME: 未检测到（配置目录不存在）"
    return
  fi

  if [[ -L "$AGENT_TARGET" ]]; then
    local target
    target="$(readlink "$AGENT_TARGET")"
    if [[ "$target" == "$SKILL_ROOT" ]]; then
      echo -e "  ${GREEN}$AGENT_NAME: ✅ 已安装${NC} → $target"
    else
      echo -e "  ${YELLOW}$AGENT_NAME: ⚠️ 软链指向其他位置${NC}: $target"
    fi
  elif [[ -d "$AGENT_TARGET" ]]; then
    echo -e "  ${YELLOW}$AGENT_NAME: ⚠️ 存在实体目录${NC}（非软链）"
  else
    echo -e "  ${RED}$AGENT_NAME: ❌ 未安装${NC}"
  fi
}

# 列出支持的工具
list_agents() {
  echo "支持的 IDE/CLI 工具："
  echo ""
  printf "  %-18s %-40s %s\n" "工具名" "配置目录" "状态"
  printf "  %-18s %-40s %s\n" "------" "------" "----"
  for entry in "${AGENT_MAP[@]}"; do
    parse_agent "$entry"
    local status
    if [[ -d "$AGENT_CONFIG_DIR" ]]; then
      status="已安装"
    else
      status="未检测到"
    fi
    printf "  %-18s %-40s %s\n" "$AGENT_NAME" "$AGENT_CONFIG_DIR" "$status"
  done
}

# 主逻辑
main() {
  local action="install"
  local target_agent=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --list)
        action="list"
        shift
        ;;
      --check)
        action="check"
        shift
        ;;
      --uninstall)
        action="uninstall"
        shift
        ;;
      --agent|-a)
        target_agent="$2"
        shift 2
        ;;
      --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --agent, -a <name>  只安装到指定工具（可重复使用）"
        echo "  --list              列出支持的工具及检测状态"
        echo "  --check             检查各工具的 skill 安装状态"
        echo "  --uninstall         移除所有已安装的软链"
        echo "  --help, -h          显示帮助"
        echo ""
        echo "示例:"
        echo "  $0                          # 自动检测并安装"
        echo "  $0 --agent claude-code      # 只装到 Claude Code"
        echo "  $0 --check                  # 检查安装状态"
        exit 0
        ;;
      *)
        err "未知参数: $1"
        exit 1
        ;;
    esac
  done

  echo ""
  echo "═══════════════════════════════════════════════"
  echo "  lowcode-dsl-gen Skill 安装器"
  echo "  Skill 目录: $SKILL_ROOT"
  echo "═══════════════════════════════════════════════"
  echo ""

  case "$action" in
    list)
      list_agents
      ;;
    check)
      info "检查各工具的安装状态："
      echo ""
      for entry in "${AGENT_MAP[@]}"; do
        check_agent "$entry"
      done
      ;;
    uninstall)
      info "移除所有已安装的软链："
      echo ""
      for entry in "${AGENT_MAP[@]}"; do
        uninstall_from_agent "$entry"
      done
      ;;
    install)
      if [[ -n "$target_agent" ]]; then
        # 安装到指定工具
        local found=false
        for entry in "${AGENT_MAP[@]}"; do
          parse_agent "$entry"
          if [[ "$AGENT_NAME" == "$target_agent" ]]; then
            found=true
            install_to_agent "$entry"
            break
          fi
        done
        if ! $found; then
          err "未知工具: $target_agent"
          echo "  支持的工具: $(printf '%s ' "${AGENT_MAP[@]}" | sed 's/:[^ ]*//g')"
          exit 1
        fi
      else
        # 自动检测并安装
        local installed=0
        local skipped=0
        for entry in "${AGENT_MAP[@]}"; do
          if is_agent_installed "$entry"; then
            if install_to_agent "$entry"; then
              ((installed++))
            fi
          else
            parse_agent "$entry"
            info "$AGENT_NAME: 未检测到，跳过"
            ((skipped++))
          fi
        done
        echo ""
        ok "安装完成：$installed 个工具已安装，$skipped 个未检测到"
      fi
      echo ""
      info "安装后验证：运行 $0 --check 检查状态"
      ;;
  esac
  echo ""
}

main "$@"
