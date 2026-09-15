#!/bin/bash
NODE="C:/Users/Perfect/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
AB="C:/Users/Perfect/.workbuddy/binaries/node/workspace/node_modules/agent-browser/bin/agent-browser.js"
export NO_PROXY="127.0.0.1,localhost"
cd "C:/Users/Perfect/Desktop/3d-taskboard-main" || exit 1
URL="http://127.0.0.1:8934/office-3d-taskboard.html"

# 1. CFO 近景
"$NODE" "$AB" open "$URL"
sleep 8
"$NODE" "$AB" click '.tool-btn[data-view="cfo"]'
sleep 5
"$NODE" "$AB" screenshot "_shots/close_cfo.png"
echo "close_cfo: $(ls -l _shots/close_cfo.png | awk '{print $5}')"

# 2. CMO 近景
"$NODE" "$AB" click '.tool-btn[data-view="cmo"]'
sleep 4
"$NODE" "$AB" screenshot "_shots/close_cmo.png"
echo "close_cmo: $(ls -l _shots/close_cmo.png | awk '{print $5}')"

# 3. CPO 近景
"$NODE" "$AB" click '.tool-btn[data-view="cpo"]'
sleep 4
"$NODE" "$AB" screenshot "_shots/close_cpo.png"
echo "close_cpo: $(ls -l _shots/close_cpo.png | awk '{print $5}')"

# 4. Meeting 近景（已修植物位置）
"$NODE" "$AB" click '.tool-btn[data-view="meeting"]'
sleep 4
"$NODE" "$AB" screenshot "_shots/close_meeting.png"
echo "close_meeting: $(ls -l _shots/close_meeting.png | awk '{print $5}')"

# 5. CEO
"$NODE" "$AB" click '.tool-btn[data-view="ceo"]'
sleep 4
"$NODE" "$AB" screenshot "_shots/close_ceo.png"
echo "close_ceo: $(ls -l _shots/close_ceo.png | awk '{print $5}')"