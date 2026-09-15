#!/bin/bash
NODE="C:/Users/Perfect/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
AB="C:/Users/Perfect/.workbuddy/binaries/node/workspace/node_modules/agent-browser/bin/agent-browser.js"
export NO_PROXY="127.0.0.1,localhost"
cd "C:/Users/Perfect/Desktop/3d-taskboard-main" || exit 1
URL="http://127.0.0.1:8934/office-3d-taskboard.html"

# 全景（等模型全部加载）
"$NODE" "$AB" open "$URL"
sleep 18
"$NODE" "$AB" screenshot "_shots/full_overview.png"
echo "full_overview: $(ls -l _shots/full_overview.png | awk '{print $5}')"

for z in ceo cfo cto cpo cmo coo cro; do
  "$NODE" "$AB" click ".tool-btn[data-view=\"$z\"]"
  sleep 4
  "$NODE" "$AB" screenshot "_shots/full_$z.png"
  echo "full_$z: $(ls -l _shots/full_$z.png | awk '{print $5}')"
done
echo "ALL DONE"