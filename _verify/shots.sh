#!/bin/bash
# 渲染验证：打开看板并逐房间截图
NODE="C:/Users/Perfect/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
AB="C:/Users/Perfect/.workbuddy/binaries/node/workspace/node_modules/agent-browser/bin/agent-browser.js"
export NO_PROXY="127.0.0.1,localhost"
cd "C:/Users/Perfect/Desktop/3d-taskboard-main" || exit 1
mkdir -p _shots
URL="http://127.0.0.1:8934/office-3d-taskboard.html"

echo "== open overview =="
"$NODE" "$AB" open "$URL"
sleep 10
"$NODE" "$AB" screenshot "_shots/p_overview.png"
echo "overview done: $(ls -l _shots/p_overview.png 2>/dev/null | awk '{print $5}')"

for z in cfo cmo cpo meeting ceo coo cto cro; do
  echo "== open zone=$z =="
  "$NODE" "$AB" open "$URL?zone=$z"
  sleep 7
  "$NODE" "$AB" screenshot "_shots/p_$z.png"
  echo "$z done: $(ls -l _shots/p_$z.png 2>/dev/null | awk '{print $5}')"
done
echo "ALL DONE"
ls -l _shots/
