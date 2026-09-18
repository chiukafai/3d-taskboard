#!/usr/bin/env bash
# 最通用的一种：任何能执行 shell 的 AI agent 都能用
# 用法:
#   ./curl.sh "任务标题" [dept] [status] [priority] [source]
# 例:
#   ./curl.sh "9 月投放复盘" cmo in_progress high 小红书-agent
#
# 也可以直接手写 JSON（批量）：
#   ./curl.sh --json '[{"title":"A","dept":"cfo"},{"title":"B","dept":"cto","status":"done"}]'

set -euo pipefail

BOARD="${BOARD:-http://127.0.0.1:8787}"      # 看板服务地址
TOKEN="${TOKEN:-}"                            # board.config.json 里的 server.token

AUTH=()
[ -n "$TOKEN" ] && AUTH=(-H "Authorization: Bearer $TOKEN")

if [ "${1:-}" = "--json" ]; then
  BODY="$2"
else
  TITLE="${1:?用法: curl.sh \"任务标题\" [dept] [status] [priority] [source]}"
  DEPT="${2:-}"
  STATUS="${3:-todo}"
  PRIORITY="${4:-medium}"
  SOURCE="${5:-${AGENT_NAME:-shell}}"
  BODY=$(printf '{"title":"%s","dept":"%s","status":"%s","priority":"%s","source":"%s"}' \
    "$TITLE" "$DEPT" "$STATUS" "$PRIORITY" "$SOURCE")
fi

curl -sS -X POST "$BOARD/api/tasks" \
  -H "Content-Type: application/json" "${AUTH[@]}" \
  -d "$BODY"
echo
