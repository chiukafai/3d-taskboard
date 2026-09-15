# -*- coding: utf-8 -*-
"""把 addFurniture 的 7 个房间分支改为「程序化兜底组 prog + 高清模型覆盖」。"""
import io, re

P = r"C:/Users/Perfect/Desktop/3d-taskboard-main/office-3d-taskboard.html"
h = io.open(P, encoding="utf-8").read()

start = h.index("function addFurniture(){")
end = h.index("\n}\n", start) + len("\n}")
body = h[start:end]
orig_len = len(body)

# ---- 1. 头部：加 prog / FLOOR / extraProps ----
old_head = """    const{cx,cz,w,d}=zone;
    const g=new THREE.Group();
    const hw=w/2,hd=d/2;
"""
new_head = """    const{cx,cz,w,d}=zone;
    const g=new THREE.Group();
    const hw=w/2,hd=d/2;
    // prog = 程序化兜底家具组；高清模型加载成功后整组移除
    const prog=new THREE.Group();
    const FLOOR=0.09;
    let extraProps=null;   // CFO 桌面小物组（模型失败时回退台面高度）
"""
assert old_head in body
body = body.replace(old_head, new_head, 1)

# ---- 2. ceo..cto 分支内的 (g, → (prog, ----
i0 = body.index("if(id==='ceo'){")
i1 = body.index("}else if(id==='cfo'){")
seg = body[i0:i1]
n = seg.count("(g,")
seg = seg.replace("(g,", "(prog,")
body = body[:i0] + seg + body[i1:]
print("replaced (g, -> (prog,): %d" % n)

# ---- 3. CFO 分支：去掉内部 prog/FLOOR 声明与旧调用 ----
body = body.replace("""      // 程序化兜底家具（与 CFO_SHOW 同坐标对齐；高清模型加载成功后整组移除）
      const prog=new THREE.Group();
""", """      // 程序化兜底家具（与 CFO_SHOW 同坐标对齐；高清模型加载成功后整组移除）
""", 1)
body = body.replace("""      const FLOOR=0.09;
      const wallMat=""", """      const wallMat=""", 1)
body = body.replace("""      createPlant(prog, 2.95,-1.90);
      g.add(prog);
""", """      createPlant(prog, 2.95,-1.90);
""", 1)
body = body.replace("""      g.add(deskProps);
      if (window.CFO_MODELS) loadCfoShowcase(g, prog, deskProps, FLOOR, 0.90);
""", """      g.add(deskProps);
      extraProps = deskProps;
""", 1)

# ---- 4. 末尾统一：挂载 prog + 触发高清模型加载 ----
old_tail = """    g.position.set(cx,0,cz);scene.add(g);"""
new_tail = """    g.add(prog);
    const SHOW={ceo:CEO_SHOW,cro:CRO_SHOW,coo:COO_SHOW,cpo:CPO_SHOW,
                cto:CTO_SHOW,cmo:CMO_SHOW,meeting:MEETING_SHOW,cfo:CFO_SHOW};
    if(SHOW[id]) loadRoomShowcase(id.toUpperCase(), g, prog, SHOW[id], extraProps, FLOOR, 0.90);

    g.position.set(cx,0,cz);scene.add(g);"""
assert old_tail in body
body = body.replace(old_tail, new_tail, 1)

h = h[:start] + body + h[end:]
io.open(P, "w", encoding="utf-8", newline="").write(h)
print("addFurniture %d -> %d chars" % (orig_len, len(body)))
