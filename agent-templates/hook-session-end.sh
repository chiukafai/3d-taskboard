#!/usr/bin/env bash
# 会话结束钩子 —— 适配「任何支持 hook / 收尾命令」的 AI agent。
#
# 设计取舍：**刻意不在本脚本里解析任务**。
#   本脚本只做一件事：把你 agent 已经写好的内容，规范化成一个投递箱文件，
#   交给看板的引擎去解析（引擎认 4 种格式、别名容错、去重，已单测过）。
#   这样"什么算一条任务"的规则只有一处，不会出现脚本和引擎各说各话。
#
# 环境变量：
#   BOARD_DIR   看板目录（默认：本脚本所在目录的上一级）
#   AGENT_NAME  你这个 agent 的名字 → 写进任务的 source 字段
#   TASKS_FILE  一行一条任务的文件（agent 只管往这里追加）；不设则从 stdin 读
#   AUTO_INGEST 1 = 写完后立刻调 python 收件（默认 1，找不到 python 就跳过）
#
# 一行一种写法（引擎都认，识别不了也不会丢，会进"未归类"）：
#   [cfo] 月度营收联调 | s:in_progress | p:high | desc:对外数据模块
#   [cto] 图片匹配逻辑归档 | s:done
#   这条不写部门，靠标题关键词自动归类（对账 → CFO）
#   - [x] 用清单写法也行，[x] 视为已完成
#   {"title":"JSON 行也认","dept":"coo","status":"done"}

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOARD_DIR="${BOARD_DIR:-$(cd "$HERE/.." && pwd)}"
INBOX="$BOARD_DIR/data/inbox"
AGENT="${AGENT_NAME:-$(basename "${0%.*}")}"
TASKS_FILE="${TASKS_FILE:-}"
AUTO_INGEST="${AUTO_INGEST:-1}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$INBOX/hook-${AGENT}-${STAMP}.md"

mkdir -p "$INBOX" "$INBOX/_imported"
{
  echo "---"
  echo "source: ${AGENT}"
  echo "origin: session-hook"
  echo "at: ${STAMP}"
  echo "---"
  echo
  echo '```board'
  if [ -n "$TASKS_FILE" ] && [ -f "$TASKS_FILE" ]; then
    cat "$TASKS_FILE"
  else
    cat
  fi
  echo '```'
} > "$OUT"

LINES="$(grep -cvE '^\s*$|^---$|^```' "$OUT" 2>/dev/null || echo 0)"
echo "[$AGENT] 已写入投递箱：$OUT（约 ${LINES} 行）"

if [ "$AUTO_INGEST" = "1" ]; then
  for PY in python3 python py; do
    if command -v "$PY" >/dev/null 2>&1; then
      ( cd "$BOARD_DIR" && "$PY" -m taskboard ingest ) && break
    fi
  done
  echo "[$AGENT] 若上面没看到收件结果：服务端会在 30 秒内自动扫到，无需处理。"
fi

if [ -n "$TASKS_FILE" ] && [ -f "$TASKS_FILE" ]; then
  mv "$TASKS_FILE" "$TASKS_FILE.done" 2>/dev/null || true
fi
echo "[$AGENT] 完成"
