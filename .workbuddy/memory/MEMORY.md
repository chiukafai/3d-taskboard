# MEMORY.md — workbuddy看板

> 主文件 `office-3d-taskboard.html` = v5.1 布局 + 09-16 墙体内收 + 09-17 动态数据源与认领协议。整理 2026-09-17。
> 📎 **细节在 `笔记-看板与场景详解.md`**（验证命令全表/探针/z-fighting 论证/安全黑名单/模板/性能/git）。**新增细节写那里，别加长本文件**——超限会被系统从**末尾**截断，故最活跃的内容排在最前。

## 1. 位置与数据管线

- **工作副本** `C:\Users\Perfect\Desktop\3d-taskboard-main`（git，remote `chiukafai/3d-taskboard`）。**日常改这里。**
- E 盘 `workbuddy看板` ≡ WPS 云同步目录同名夹（同物理目录）→ 仍是 09-10 旧副本。🔴 **主从未定**，同步前先定谁覆盖谁。
- 技能 `.workbuddy/skills/board-export/SKILL.md`（frontmatter 用 `trigger` 单数）。**仅用户级 `~/.workbuddy/skills/` 自动加载**；工作区级不扫描。
- 管线：⭐ taskboard 引擎（HTTP/投递箱 → `data/taskboard.db` 真相源 → 导出 `tasks-data/tasks.js`）；旧① task-logger→`extract-tasks.py`；旧② `/board-export`→`import_inbox.py`。**API 在线时不叠加旧管线**，避免重复计数。
- ⚠️ **WPS 云同步 last-write-wins 会吃改动**（「仅打开」也可能把旧版回传覆盖云端）→ 跨机编辑前确认同步状态；重要改动 zip 到非同步区。
- ⚠️ `data/taskboard.db` **不放云同步目录**（会锁 SQLite）；要同步就 `BOARD_DATA_DIR` 指非同步目录。
- 端口：预览 `python -m http.server 8934 --bind 127.0.0.1`；看板 `python -m taskboard serve`(8787)。

## 2. taskboard 引擎（09-17，当前主战场）

**任意 agent 的任务都能录进看板、随时查看、可 Docker 常开；不绑定任何 agent、不写死路径。**

- **配置** `board.config.json`（相对本文件解析）；env `BOARD_CONFIG/BOARD_DATA_DIR/BOARD_HOST/BOARD_PORT/BOARD_TOKEN/BOARD_POLL`。**引擎** `taskboard/`（**纯 stdlib 无 pip**）：`config/model/store/ingest/emit/server/__main__`，入口 `python -m taskboard <cmd>`。
- **三通道**：① HTTP `POST /api/tasks` ② 投递箱 `data/inbox/`（30s 扫，归档 `_imported/`）③ 任务体内嵌 `claim` 字段。
- **归一化＝"不绑定"关键**（`model.py`）：`name/task/标题/summary`→title；`zone/team/部门`→dept；`营销/marketing`→cmo；`已完成/done:true`→done；`doing/进行中`→in_progress；`阻塞`→blocked；`紧急/p0`→high。**title 唯一必填**；没写部门按标题关键词猜，猜不出进 `_unassigned`（不落房间）。`dept_source`＝`expert|guessed|none`，`guessed` 在看板打灰色**「部门待核」**标。
- **去重** `UNIQUE(dept,dedup_key)`（`dedup_key=external_id or 标题小写`）→ **重复上报＝更新**。
- 🔴 **`tasks-data/tasks.js` 是导出产物，禁止手改**；改数据走 API/CLI/投递箱。
- **数据源优先级** `?api=` > 服务端注入 `window.__BOARD_API_HINT` > `file://` 静态回退；20s 轮询，状态/删除**立即 `PATCH/DELETE` 回写**；左下 `#api-badge` 🟢/🔴。🔴 **不做同源盲探测**（会刷 404，改由 `_inject_hint()` 注入提示）。
- ⚠️ 主脚本在 `<script type="module">`（严格模式）：**新变量必须写进 `var` 声明行**，否则赋值抛 ReferenceError（曾漏 `_apiEverOnline`）。
- 🔴 **A+B 中间态＝认领协议（09-17 用户指定实践）**：agent **只提议**（`POST /api/tasks/<id>/claim`），任务仍 `todo`、`assignee` 空；**人在看板点批准**（`POST /api/claims/<id>/approve`）才转 `in_progress`+落 `assignee`。**保留人工审核关口，绝不自动派活。** 已 approved 的再提议**不得回退 pending**（返回 `already_approved`）；批准某人自动驳回其他 proposed；多申请人时卡片 ✓ 展开浮层让用户自己选。
- **CLI** `doctor serve ingest add ls set rm export seed-demo clear stats` + `claim/claims/approve/reject/withdraw/queue`。**`SPEC.md`＝规则唯一真源**；`any-agent-prompt.md` 可直接贴；`claim-poll.py`＝认领助手。📎 安全黑名单/CDN 依赖/模板清单/未实测项/「看板无自动派活、无新增任务 UI」见笔记 §D。

## 3. 场景铁律（改代码前必读）

1. **坐标系**：`*_SHOW` 的 `p:[x,z]`=**房间局部**（世界=`cx+px, cz+pz`）；`buildMemWall`/`makePlaque` 用**世界坐标**。混算必错。
2. **模型朝向**：`exec_chair`/`sofa` 靠背在 −z（r=0 朝 +z）；**`office_chair` 相反**。
3. **`office_monitor` 是整套餐位**（显示器+键鼠+Ø0.88 托底≈1.04×0.59×1.04m）→ 一个占满桌。桌面一律 `createDeskMonitor()`/`createLaptop()`。
4. **门**：门枢 `userData.openSign`（front/back=−1，right/left=+1），`sign=(双开?±1:1)×openSign`；**加新门必须设**，否则南/北墙门内开。10 樘全外开。
5. **门牌 `makePlaque`**：贴门墙较长实墙段避门洞。`pr`：front→0/back→π/right→+π/2/left→−π/2（取反出镜像字）；**不加 `repeat.x=−1`**。
6. **桌面**：`deskGrp(parent,dx,dz,r,y)`+`createDeskMonitor`；局部「人坐 −Z、桌长轴 X、屏朝 −Z」；桌面高 `DTOP_HI=0.85`(GLB)/`DTOP_PROG=0.90`(兜底)。8 房组合与桌木 tint 各不同。
7. **记忆屏 `MEM_STYLE`**：`ceo/cro:projection, cfo/cto/cpo:display, meeting/cmo/coo:whiteboard`。白板 3 特例居中(cmo 北墙 rotY0、coo 南墙 π、meeting 南墙 π)。壁挂 front→`z=cz-hd+0.16`；back→`z=cz+hd-0.16`。
8. 📌 **不要用"通用预设/批量生成"整体替换手工调优的视觉资产**（09-10 SHOWROOM 曾因此回退）。
9. URL 直达 `?zone=<id>`（meeting 无工具栏按钮）。

## 4. 布局（v5.1+09-16）

- 包络 **29.6(x)×21.6(z)**，原点西北，z 越大越靠南。公共 132.5㎡ / 房间 337.1㎡ / 室内 469.6㎡ / 公共 28.2% / 覆盖 73.4%。
- 8 房 `(cx,cz,w×d,门墙@doorPos)`：
```
cpo 3.3,8.3 6.6×5.4 right@9.6     cro 12.5,5.9 6.2×4.6 front@12.6
meeting 4.2,13.7 6.4×5.4 right@13.6  cmo 19.7,4.1 8.2×8.2 front@17.6
cfo 5.4,19.0 6.4×5.2 right@19.0   cto 26.7,4.9 5.8×6.6 front@26.4
coo 15.4,15.9 8.0×7.0 back@15.2    ceo 22.7,15.7 6.6×6.6 back@22.6
```
- 走廊净宽：主廊 **4.2m**(z 8.2–12.4) · 西支廊上 4.0/下 2.8 · 圆厅 Ø3.0 @(9.4,10.8)（偏心）。
- 室外：西北前庭 + 东南侧庭；主入口 x=8.0,z=5.6 双开门；疏散口 x=29.4,z=10.5。**室外景观刻意保留**，只清过道。🔴 **走廊内实体家具 0 件**，不要再加落地陈设。
- 常量 `SITE/LOBBY/COURT/YARD/ENTRY/EXITX`；公共区靠 `PUB_FLOORS`(贪心矩形分解，互不重叠)/`PUB_WALLS`/`PUB_DOORS`+`createPublicWalls()`。

## 5. 防 z-fighting

- **地面**：同 y 共面的地毯/铺装 xz 重叠 → **必闪**（09-11 扫出 14 处）。按 z/x 切开，**留 ≥0.05m 缝**。自检 `verify_v51.mjs`。
- **墙体（09-16）**：5 对邻房共享墙线各生成 0.15m 墙盒 → 六面严格共面 → 颜色跳变。修法（`createRoom()` 内自适应）：`sharedNeighbor(name)` 查墙线与邻房数值是否重合 → 是则按 `zone.id` 字典序两侧内收 **8mm/3mm**；墙两端落「边界−内收量」；门洞中心以 `edgeStart` 反算**恒等于 `doorPos`**；门牌 `off` 同步减。
- **改任何 `cx/cz/w/d` 后必跑** `node _verify/verify_wall_zfight.mjs ../office-3d-taskboard.html after` → 验收**「共面重叠墙对 0」且「面最小间距 ≥0.005」**。
- ⚠️ 阈值 1e-6：墙线差 <5mm 的"近重合"不触发。⚠️ 只算 X/Z 轴；`_mine < nb` **必须比索引**（数字<字符串=NaN=false）。📎 论证见笔记 §A。

## 6. 验证工具箱（📎 全表含注释见笔记 §B）

`audit_v5.py`(静态审计6项) · `verify_v5.mjs`(结构/门开向/报错) · `verify_wall_zfight.mjs` · `verify_v51.mjs` · `verify_doors.mjs` · `probe_clearance_v5.mjs` · `sync_sysconfig.py` · `verify_syspanel.mjs` · `test_ingest_parse.py` · `verify_taskboard_api.mjs` · `verify_claim_flow.mjs` · `probe404.mjs`（均在 `_verify/`）
- ⚠️ **8934 只能起一个进程**（http.server 单线程，抢端口 → Playwright `goto` 超时＝假故障）。
- ⚠️ **中文字体缺字符**：`msyh.ttc` 无 U+2705(✅)/U+2713/↔ → 用 `√` `→` `●` `■` `vs`。
- **整栋重排五步**：①0.1m 栅格几何校验(`gen_plan_v5_geom.py`) ②转 3D 坐标(`gen3d_v5_data.py`) ③落码(`relayout_v5.py`) ④`audit_v5.py` ⑤浏览器三验。
  铁律：① 先几何校验再落码 ② 判"布局对不对"用**射线/静态几何，不要截图**（无 GPU 合成会伪造缺失区域）③ 只改室内隔墙不动外轮廓 → 相机/雾/光/垫层免重算 ④ 新报错先做版本对比再背锅。

## 7. ⚙ 系统设置面板 + 速查

- 面板 `#syspanel`（按钮 `#btn-sys`），4 分区：人格配置文件 / 记忆派生任务 / 部门任务管理 / 本会话已完成。
- **人格配置是静态快照**（正文来自 HTML 内嵌 `<script type="text/plain" id="cfg-XXX.md">`，浏览器读不了本地文件）→ **改了真实文件必然过期**；改完跑 `sync_sysconfig.py`（重写正文 + `SYS_CONFIG_FILES[].mtime`）。
- 🔴 **主脚本是 `<script type="module">`（约 411–2608 行）**：模块内 `function` **不挂全局**，内联 `onclick` 在全局求值 → `is not defined`。修法：显式挂 `window`（已挂 `openCfgModal/closeCfgModal/deleteTask/openPanel`）。**新增内联 onclick 必须同步挂 window**。
- 🔴 **截图只能走 `_verify/grab.mjs`**（`page.screenshot()` 无 GPU 返回全白）；判"某 GLB 是什么"必须**隔离渲染+实测包围盒**，别信文件名。🔴 **不要把 three.js/Draco 本地化**（浏览器拦 ES 模块，双击打不开）。
- 📎 性能基线/模型包/调试钩子/备份与 GitHub 见笔记 §C §E。
