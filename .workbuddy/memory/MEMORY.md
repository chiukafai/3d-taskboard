# MEMORY.md — workbuddy看板 项目长期记忆

## 关键事实（2026-08-10 确认）

- **目录是 junction**：`E:\AI\Workbuddy\workbuddy看板` 与 `E:\AI\Workbuddy\WPS云同步（workbuddy)\workbuddy看板` 是同一物理目录（cp 报 "same file"）。所有写入只会影响一份文件，无需分别同步。
- **WPS 云占位（Offline 属性）**：`tasks-data/tasks.js`（真实任务数据）在本机为 WPS 云占位文件，内容未本地化，`cat`/Read/python 读取均失败（OSError 22 / Permission denied）；`ls`/`wc`/`attrib` 正常。`office-3d-taskboard.html` 为本地可用（无 O 属性）。若看板显示示例任务，多半是 tasks.js 未"始终保留在此设备"导致加载失败回退 FALLBACK_TASKS。

## 看板任务数据双管线

| 管线 | 触发 | 脚本 | 产物 | 加载方式 |
|------|------|------|------|----------|
| 自动 | task-logger 技能 | `tasks-data/extract-tasks.py` | `tasks-data/tasks.js`（`window.TASK_DATA`） | HTML `loadTasks()` |
| 手动/跨机 | board-export 技能（`/board-export`） | `tasks-data/import_inbox.py` | `tasks-data/inbox_tasks.js`（`window.TASK_INBOX`） | HTML `loadTasks()` 合并 |

- 两条管线**互不覆盖**：`import_inbox.py` 只读 `inbox/*.md`，生成独立 `inbox_tasks.js`，绝不改 `tasks.js`。
- `import_inbox.py` 自动探测 inbox 位置（Win 全角括号 `（workbuddy）`/Mac/工作区兜底），解析 ```board 代码块，归档已处理 `.md` 至 `inbox/_imported/`。
- board-export 技能已安装：`E:\AI\Workbuddy\workbuddy看板\.workbuddy\skills\board-export\SKILL.md`（frontmatter 用 `trigger` 单数列表，非 `triggers`）。

## 技能文件位置

- board_export_skill.md（SSOT）与已安装的 SKILL.md 为同一目录树下的两份（junction 同一文件），改一处即同步。

## 浏览器内导入的 UX 陷阱 (2026-08-10)

看板内 📥 导入按钮走浏览器 `<input webkitdirectory>` → 解析 → **自动下载** inbox_tasks.js 到 `Downloads/`，但浏览器安全限制无法直接写入 `tasks-data/`。

- **典型踩坑**：用户以为"导入完成 = 任务已入看板"，其实文件还在 Downloads 没移动，刷新看不到任务。
- **看板弹窗已优化**（v1.1）：明确显示"接下来要做 2 步"+ 目标路径 + 一键复制按钮 + `<kbd>F5</kbd>` 提示。
- **建议优先用 Python 路径**：`python3 tasks-data/import_inbox.py` 直接写 `tasks-data/inbox_tasks.js`，免移动。Python 解析已用 node 单测 6/6 验证。

## ⚠️ WPS 云同步冲突风险（2026-08-11 确认，重大）

- 本看板项目经 **WPS云同步（workbuddy)** 在 **Mac + Windows 双机**间同步。
- 同步机制为 **last-write-wins**；WPS 对 `.html`/`.js` 等纯文本文件**通常不保留历史版本**（历史版本主要覆盖 WPS 自有文档格式）。
- **致命陷阱**：在任一台机器「仅打开/查看」文件，也可能触发 WPS 把该机**本地旧版**回传云端，覆盖另一台机器更新的修改。2026-08-11 已发生：Mac 本地为 Aug 10 00:20 旧版，仅打开页面即把云端 Windows 早修改覆盖，且云端无解。
- **恢复窗口依赖另一台机器的本地副本**：对方 WPS 尚未把坏版本拉下来前，其本地仍存好版本。处置顺序：立即去另一台 → 复制到非同步区（桌面/U盘）→ 再确认内容。
- **预防约定**：①跨机编辑前确认 WPS 状态=已同步；②只看效果就开副本、不开同步文件；③重要修改后 `zip` 一份到非同步区；④建议项目用 **git** 做版本控制（独立于 WPS，能真正留历史）。

## 3D 看板布局 —— v5 错落非对称 + 宽走廊（2026-09-11 落地 · 现行）

- **平面结构**（包络 **29.6(x) × 21.6(z)**，原点西北角，**z 越大越靠南**）：
  ```
  z=0.0  前庭(室外)              ┌─── CMO 营销 8.2×8.2 = 67.2㎡ ───┐
  z=1.6                          │                                 ├ CTO 5.8×6.6
  z=3.6  ├── CRO 6.2×4.6 ────────┤                                 │  =38.3㎡
  z=5.6  ├ CPO 6.6×5.4=35.6㎡ ───┤                                 │
  z=8.2  │  门(东墙) ─────────────门(南墙)──────────────────────── 门(南墙)
         │      东西主廊 · 净宽 4.2m（v5 由 3.0m 加宽）
  z=11.0 ├ MT 6.4×5.4 ─ 门 ┌ ✓ 偏心圆厅 Ø3.0 (9.4,10.8) ← 不在中轴14.8
  z=12.4 ├──────┤          └─ COO 8.0×7.0 = 56.0㎡ ─┬─ CEO 6.6×6.6 = 43.6㎡ ─ 侧庭
  z=16.4 ├ 西支廊上段4.0m ─→ CFO 6.4×5.2 = 33.3㎡（东墙门）  │               (室外)
  z=21.6 └─── 西支廊下段 2.8m（并入原 7.7㎡ 死区）──────────┘
  ```
- **8 房实际坐标**：cpo(3.3,8.3,6.6×5.4,door=right@9.6) / meeting(4.2,13.7,6.4×5.4,right@13.6) /
  cfo(5.4,19.0,6.4×5.2,right@19.0) / cro(12.5,5.9,6.2×4.6,front@12.6) / cmo(19.7,4.1,8.2×8.2,front@17.6) /
  cto(26.7,4.9,5.8×6.6,front@26.4) / coo(15.4,15.9,8.0×7.0,back@15.2) / ceo(22.7,15.7,6.6×6.6,back@22.6)
  （`cx/cz` 为房心，`doorPos` 是沿门墙的坐标）
- **公共区 132.5㎡ / 房间 337.1㎡ / 室内 469.6㎡ / 公共占比 28.2%**（v4 为 114.0 / 351.6 / 465.6 / 24.5%）。
  包络与覆盖率（73.4%）**与 v4 完全一致** —— v5 只动室内隔墙，外轮廓/退台/外墙一律没动。
- **走廊净宽（v5 目标即验收值）**：东西主廊 **4.2m**（z 8.2–12.4）· 西支廊上段 **4.0m**（z 12.4–16.4）· 西支廊下段 **2.8m**（z 16.4–21.6）· 圆厅 **Ø3.0m (9.4,10.8,r1.5)**。
- **室外**：西北入口前庭(x0–6.6,z0–5.6) + 东南侧庭(x26.2–29.6,z12.6–19.0)；主入口 **x=8.0,z=5.6 双开门**；东侧疏散口 x=29.4,z=10.5。
  ⚠️ **室外景观（长椅/绿植/喷泉/缆绳卷）刻意保留**，用户只要求清"过道"。
- **新常量**：`SITE{ex29.6,ez21.6,cx14.8,cz10.8}` `LOBBY{x9.4,z10.8,r1.5}` `COURT` `YARD` `ENTRY` `EXITX`；公共区由 `PUB_FLOORS`(贪心矩形分解，防 z-fighting) / `PUB_WALLS` / `PUB_DOORS` + `createPublicWalls()` 生成。
- 🔴 **走廊内实体家具 = 0 件（v5 铁律）**：`createAtrium()` 里圆厅的 9 组 15 件（接待台/台面屏/杯笔筒/访客椅/长椅×2/花坛绿植/贝壳喷泉/贝壳罐）+ 主廊 2 处缆绳卷**已全部拆除**。
  **不要再往走廊/圆厅加落地陈设**；圆厅只留圆形石盘 + 外环带作视觉锚点。
- ✅ **8 樘房门 + 2 樘公共门全部朝公共区、全部外开**（10 樘全绿）。
- 🔴 **门开向修正（v4 新坑）**：`animateDoors` 的旋向 sign 原为全局常数，但**东/西墙 vs 南/北墙"朝外"的局部旋向相反** →
  门枢新增 `userData.openSign`（`front`/`back` = −1，`right`/`left` = +1），`sign = (双开? ±1 : 1) × openSign`。**加新门前必须照此设 openSign**。
- **历史备份**：v4 = `.bak_pre_v5_20260911`(172,493 B) · v3 = `.bak_pre_v4_20260911`(163,609 B) · v5 = `.bak_pre_v51_20260911`(169,006 B)。**现行主文件 = v5.1 = 173,147 B**。
- **家具 = 高清 GLB 单套**（`all-models.js`，9 类，`window.OFFICE_MODELS`）。`addFurniture()` 有 `hasModels` 分支：包可用 → 跳过程序化兜底；CFO 装饰（墙板/地毯/保险柜/桌面小物）与 GLB 共存。旧 `cfo-models.js` 已无引用。
- 🔴🔴 **`office_monitor` 不是一台显示器！**（2026-09-11 隔离渲染实测）它是「**显示器 + 键盘 + 鼠标 摆在 Ø0.88m 圆木托底上**」的**一整套工位**，世界包围盒 ≈ 1.044×0.592×1.043m —— 一个就占满整张 1.88×0.70 办公桌。**每桌放两个 = 两套工位叠罗汉**（用户看到的"两台笔记本各带一个圆盘托底"就是这个）。
  ⇒ **所有桌面显示器/笔记本一律用程序化 `createDeskMonitor()` / `createLaptop()`，不要再往桌上摆 `office_monitor` GLB。**
- 🔴 **模型自身朝向（实测，极易踩坑）**：`exec_chair`/`sofa` 靠背在 **−z** ⇒ r=0 面朝 **+z**；但 `office_chair` 靠背在 **+z** ⇒ r=0 面朝 **−z**（**与前者相反**）。改摆位前先确认，别想当然。
- 🔴 **坐标系**：`*_SHOW` 里的 `p:[x,z]` 是**房间局部坐标**，世界坐标 = `(cx+px, cz+pz)`。而 `buildMemWall` / `makePlaque` 用的是**世界坐标**。两者混算必错。
- **统一座向样板**（CFO/CRO 为准）：椅子贴在**桌子靠门那一侧**，人**面朝桌子**（= 背对门）；显示器放桌面靠椅子侧。房间内有记忆屏时，桌子要离屏留 ≥0.25m 净距。
- **门牌 `makePlaque(parent,text,color,x,y,z,rotY,pw)`**：贴在门墙**较长实墙段**、必须避开门洞。
  🔴 **`pr` 取值规则（v5.1 修，否则走廊看到的是镜像字）**：`front→0`、`back→π`、**`right→+π/2`、`left→−π/2`**（原来 right/left 取反了，导致牌面法线朝房内，走廊侧只能看到 `back` 面 → CPO/战略会议室/CFO 三块字全反）。
  背面 `back` 面**共用同一张贴图**，**不要再加 `repeat.x=−1`**（Group 已绕 Y 转 π，再镜像 = 双重镜像）。
- **桌面布置约定（v5.1）**：`deskGrp(parent,dx,dz,r,y)` 建桌局部坐标系 + `createDeskMonitor(parent,x,y,z,rotY)`。**桌子局部：人坐 −Z，桌长轴 = X，所有屏幕朝 −Z**。桌面高度 `DTOP_HI=0.85`（GLB 桌面）/ `DTOP_PROG=0.90`（程序化兜底）。8 房各有不同组合（双屏/单屏+笔记本/座机/托盘…）+ 不同桌木 tint，**不要再让 8 房桌子长一个样**。
- **记忆屏 `MEM_STYLE`**：`{ceo:'projection',cfo:'display',cto:'display',cro:'projection',meeting:'whiteboard',cmo:'whiteboard',coo:'whiteboard',cpo:'display'}`。
  **白板 3 特例**（全部居中，不再靠墙偏心）：cmo `x=cx, z=cz-hd+0.6, rotY=0`（北墙，面朝南迎门）；coo `x=cx, z=cz+hd-0.6, rotY=π`（南墙，入口在北）；meeting `x=cx, z=cz+hd-0.6, rotY=π`（南墙，门在东）。
  **壁挂式**：doorWall=front → `z=cz-hd+0.16`；back → `z=cz+hd-0.16`（与 v3 相反，注意别套旧值）。
- 📌 **铁律**：不要用"通用预设/批量生成"整体替换手工调优的视觉资产；改前先确认现有版本是否刻意为之（2026-09-10 SHOWROOM 曾因此回退）。
- **URL 直达**：`office-3d-taskboard.html?zone=<id>` 打开即聚焦该房（meeting 无工具栏按钮，靠此参数或双击地板进入）。
- HTTP 服务器预览：`python -m http.server 8934 --bind 127.0.0.1` + URL zone 参数实测（沙箱需此端口）。

## 布局审计与重排工作流（改布局必跑）

```
python _verify/audit_v5.py                 # v5 静态审计（现行主用，基准 plan_v5.json）
python _verify/audit_v4.py                 # v4 历史留档（基准 plan_v4.json）
python _verify/audit_v2.py office-3d-taskboard.html   # v3 历史留档
```
纯静态几何、不依赖截图（无 GPU 沙箱截图不可靠）。6 项：①房间重叠 ②门不被封 ③门牌不压门洞 ④家具包围盒(旋转感知)越界/压门洞 ⑤**座位朝向** ⑥**家具是否穿插记忆屏**（含局部↔世界坐标转换）。当前 **0 问题**。

**走廊净空实测（v5 新增，判"够不够宽/有没有被挡"只认这个）**
```
node _verify/probe_clearance_v5.mjs
```
对公共区逐格从 y=1.6m 垂直下打射线（步行高度带 0.20~1.60m 内有实体即判"不通"）→
输出 ① 主廊沿 x 逐 0.2m 的逐断面净宽 ② 西支廊逐断面净宽 ③ 公共区残留障碍物聚类。
v5 实测：主廊 **110 个断面全部 4.2m**、西支廊 4.0/2.8m、障碍物 **0 件**。

- 辅助实测脚本：`_verify/probe_facing2.mjs`（顶点分布判模型朝向）、`probe_chairs.mjs`（世界坐标核对）、`probe_models.mjs`（原生尺寸+朝向）、`probe_corridor_clutter.mjs`（走廊内实体清单，清障前必跑）、`diag_v2.mjs`（区域实体转储）、`verify_doors.mjs`（门交互回归）、`verify_v5.mjs`（结构+门开向+门洞净空+报错）、`cmp_v4_v5_errors.mjs`（新旧版本报错画像对比，判"新报错是不是自己引入的"）、`shots_v5.mjs`/`shots_v5_corr.mjs`（多视角截图）、`footprint_probe.mjs`（射线足印）。

### 整栋重排标准流程（v4/v5 沉淀 · 五步）

| 步 | 干什么 | 工具 |
|---|---|---|
| ① 几何先行 | 0.1m 栅格校验：0 重叠 / 每门通公共区 / 镜像自对称统计 → `plan_v5.json` | `gen_plan_v5_geom.py` |
| ② 转 3D 坐标 | 墙向映射 S→front/N→back/E→right/W→left；PUB_FLOORS 贪心矩形分解防 z-fighting → `gen3d_v5.json` | `gen3d_v5_data.py` |
| ③ 落码 | ZONES + 公共常量 + `createPublicWalls()` + `createMainFloor()` + 8 组 `*_SHOW` + `createAtrium()` + 相机/雾/灯光 | `relayout_v5.py`（v4 分 a/b 两个脚本，v5 合为一个） |
| ④ 静态审计 | `audit_v5.py` 6 项全绿 | 同上 |
| ⑤ 浏览器验证 + 净空/足印 | 模型/门/报错 + **射线净空**（**别用截图判布局**） | `verify_v5.mjs` / `probe_clearance_v5.mjs` |

- 📌 **铁律 1：整栋重排必须先跑几何校验再落码**。门朝向 / 家具偏移 / 记忆屏位 / 相机范围**四处联动**，直接在 HTML 里手改 8 个 ZONES 必漏。
- 📌 **铁律 2：判"布局对不对"用射线探测或静态几何，不要用截图**。无 GPU 环境的画布 alpha 合成 + 页面背景会伪造"缺失区域"（v4 时 grass 色差法 IoU 25% → silhouette 1.3% → 93%，全是伪影，白折腾）。
- 📌 **铁律 3：加/改门前必须设 `openSign`**（见上），否则南/北墙门会内开。
- 📌 **铁律 4：只改室内隔墙的"加宽/挪墙"类改动，外轮廓一律不动** —— 这样相机、雾、光照、垫层免重算，包络与覆盖率不变，风险面直接砍掉一半（v5 即此法）。
- 📌 **铁律 5：新报错先做版本对比再背锅**。无 GPU 沙箱会稳定抛 `THREE.WebGLProgram: Shader Error 0 - VALIDATE_STATUS false`，v4/v5 都有 → 用 `cmp_v4_v5_errors.mjs` 一比就知道是不是自己引入的。
- 平面图出图有两套：`gen_plan_v5_geom.py`(栅格校验) + `gen_plan_v5_svg.py`(出 SVG/HTML 明暗双主题) + `shot_plan_v5.mjs`(截图) + `make_compare_v5f.py`(验收对照图)。
- ⚠️ **中文字体缺字符坑**：`msyh.ttc` **没有** U+2705(✅)/U+2713(✓)/U+2714/U+2194(↔)，出图会渲染成豆腐块 □。可用的替代：`√`(U+221A)、`→`(U+2192)、`●`(U+25CF)、`■`(U+25A0)、`vs`。

## 看板性能基线（2026-09-11 深度清理后）

- **数字**（同机冷缓存、无 GPU 测试环境）：FCP 564ms / DOMContentLoaded 3959ms / 8 房模型就位 9295ms / 网格 453 / 材质 190 / 主文件 158KB / 模型包 3.4MB。
  （v4 后房间变大变多：网格 **463** / 材质 **229** / 三角面 **282 万** / 主文件 **172KB**；
  v5 清掉走廊陈设后：网格 **396** / 材质 **212** / 三角面 **281 万** / 主文件 **169KB** —— 大屏仍是流畅的，阴影按需更新是主要功臣。）
- **核心机制 `hasModels`**：`addFurniture()` 顶部 `const hasModels = !!window.OFFICE_MODELS`；模型包可用 → **跳过程序化兜底家具构建**（此前两套叠加 = 双重家具 + 启动慢）；CFO 装饰（橙墙板/地毯/保险柜/打印机/主机/桌面小物）与 GLB 共存、始终构建；包缺失才走程序化兜底。
- **阴影按需**：`shadowMap.autoUpdate=false`，仅在门动画（`animateDoors` 内 `shadowDirty`）与 `loadRoomShowcase` 成功后 `needsUpdate=true`。
- **材质缓存**：`mcolor()` 对**无 opts** 的纯色调用走 `_matCache`；带 opts（transparent/emissive）不复用，避免运行时改材质互相污染。
- 模型包构建脚本 `_verify/build_all_models.py`（源 `E:/AI/Workbuddy/office3d-assets/models`）→ 现打包 **9 类**（去掉未用的 `office_desk`）。
- 📌 **铁律：不要把 three.js/Draco 本地化**。实测 `file://` 双击可用（CDN 带 CORS）；改成本地相对路径 ES 模块后浏览器会拦截 → 双击打不开。
- 📌 `models_light/` 与 `models/` 体积几乎一致（无提速空间）。沙箱 headless 是软件渲染（~15FPS），**不可用于 FPS 判断**。
- 调试钩子 `window.__showCount`、`__boardDebug`（含 `scene/camera/controls/renderer/doorGroups/doorPickables/toggleDoor/animateToZone`）。
- ⚠️ **Desktop 副本缺任务数据**：`tasks-data/tasks.js`、`inbox_tasks.js` 都不存在 → 404 后回退示例任务。任务数据在 E 盘 `workbuddy看板` 目录。


### ⭐ 在本沙箱里出图**只能**用 `_verify/grab.mjs`（v5.1 血泪）

- ❌ `page.screenshot()` / `canvas.toDataURL()` 在此环境**返回全白**（std=0）。根因：renderer 是 `new THREE.WebGLRenderer({antialias:true, alpha:true})`，**没开 `preserveDrawingBuffer`**，且无 GPU 时画布合成被丢弃。（为此白折腾 6 次）
- ✅ `_verify/grab.mjs` 解法：渲染到离屏 `WebGLRenderTarget` → `readRenderTargetPixels` → 翻 Y → **手工用 zlib 编码 PNG**。导出：
  - `encodePNG(W,H,rgbaTopDown)` — 手写 PNG 编码
  - `rtShot(page, file, W=1280, H=900, bg=0xf4f1eb)` — 离屏渲染 + 出图
  - `look(page, px,py,pz, lx,ly,lz)` — **必须先调它**：会把 OrbitControls 的 `minDistance` 9→0.05、`maxDistance`→200、`minPolarAngle 0 / maxPolarAngle π` 放开，否则近景相机被控件覆盖。
  - （`shot_grab.mjs` 是同套的最小示例）
- 🔴 **判"某个 GLB 到底是什么"必须隔离渲染 + 实测包围盒**，别信文件名。做法见 `_verify/probe_monitor_face.mjs`：按世界包围盒把目标模型从场景筛出、其余全 `visible=false`，从 +Z/−Z/顶三角度出图。

### 防 Z-fighting 规则（v5.1）

- **同 y、共面的两块地毯/铺装只要 xz 有重叠 → 必然闪烁**。2026-09-11 全场景扫出 **14 处**。
- 处置：**按 z（或 x）切开，留 ≥0.05m 缝**。CFO 双毯现行值：米白 `2.9×3.1 @(−1.70, 0.40)` z∈[−1.15,1.95]；鼠尾草绿 `3.2×1.3 @(−0.60,−1.85)` z∈[−2.50,−1.20]。
- 自检命令：`node _verify/verify_v51.mjs`（会打印「同 y 地毯重叠」列表，应为 `[]`）。
- 走廊/公共地板另有专门防重叠手段：`PUB_FLOORS` 用**贪心矩形分解**，不许矩形互压。

## 备份位置（WPS 同步区之外）

- `E:/AI/Workbuddy/backups/workbuddy看板_样板房8间_20260909_1218.tar.gz`
- git 仓库（E 盘）作第二备份，当前分支 main 含 4 次 commit：Initial（2026-08-10）→ SHOWROOM feat（9e9db49）→ **revert 回退（121c68d）** → README 同步 + gitignore 屏蔽（f2e4be3）。均未 push（待 Kingsley 确认）。
- GitHub 仓库 **chiukafai/3d-taskboard** 为公开仓库：业务规划文档（营收/定价/计划书/会议纪要）**刻意不入库**，2026-09-10 起 `.gitignore` 已加规则 `*营收*`/`*计划书*`/`*规划*`/`*会议纪要*`/`看板优化*` 防 `git add -A` 误入；仅入库看板主文件 + 模型包 + README + memory。
