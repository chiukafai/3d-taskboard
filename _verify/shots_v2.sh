#!/usr/bin/env bash
# 渲染 8 间房近景：每个 zone=?id 直达聚焦
set -u
cd "C:/Users/Perfect/Desktop/3d-taskboard-main"
mkdir -p _shots
AB="C:/Users/Perfect/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
CLI="C:/Users/Perfect/.workbuddy/binaries/node/workspace/node_modules/agent-browser/bin/agent-browser.js"
export NO_PROXY="127.0.0.1,localhost"
export NODE_PATH="C:/Users/Perfect/.workbuddy/binaries/node/workspace/node_modules"

# 先开一次让浏览器冷启
"$AB" "$CLI" open "http://127.0.0.1:8934/office-3d-taskboard.html?zone=overview" >/dev/null 2>&1 &
sleep 12

# 全景
"$AB" "$CLI" screenshot _shots/v2_overview.png >/dev/null 2>&1 &
sleep 4

for z in ceo cro coo meeting cpo cto cfo cmo; do
  "$AB" "$CLI" open "http://127.0.0.1:8934/office-3d-taskboard.html?zone=$z" >/dev/null 2>&1
  sleep 9
  "$AB" "$CLI" screenshot "_shots/v2_$z.png" >/dev/null 2>&1 &
  sleep 4
done

"$AB" "$CLI" close >/dev/null 2>&1
ls -l _shots/v2_*.png 2>/dev/null