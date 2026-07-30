#!/usr/bin/env bash
# tingle 插件 — SessionStart hook。
#
# 会话开启 / 恢复 / 清空 / 压缩（matcher: startup|resume|clear|compact）后，
# 把 using-tingle 入口 skill 的全文注入会话上下文，使 agent 从第一轮起
# 就在场执行项目锚定与就绪路由。
#
# 为什么注入全文而不是一句指针：只给「去调 using-tingle」的指针，赶工的
# agent 会跳过；全文在场，入口三步与 Red Flags 跳不掉。
#
# 插件根由脚本自行推导（SCRIPT_DIR/..），不依赖环境变量——同一脚本在
# 任何装载路径下均可运行；Claude Code 与 Codex 对本 hook 形态同构支持。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

using_tingle_content=$(cat "${PLUGIN_ROOT}/skills/using-tingle/SKILL.md" 2>&1 || echo "Error reading using-tingle skill")

escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

using_tingle_escaped=$(escape_for_json "$using_tingle_content")
session_context="<EXTREMELY_IMPORTANT>\ntingle 已激活。\n\n**以下是 tingle:using-tingle 入口 skill 的全文——在回应用户之前，先按它完成项目锚定与就绪路由；其余 skill 一律用 Skill 工具调用：**\n\n${using_tingle_escaped}\n</EXTREMELY_IMPORTANT>"

printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$session_context"

exit 0
