# -*- coding: utf-8 -*-
"""字段归一化：把「任何 agent 顺手写出来的东西」翻译成看板认得的规范任务。

为什么需要这一层
----------------
不同 AI agent 表达同一件事的方式完全不同：
    {"done": true, "name": "..."} / {"status": "已完成"} / {"state": "closed"}
    {"dep": "CFO"} / {"部门": "财务"} / 干脆不写部门
本模块负责把它们统一成一套字段。**新增别名只改这里，不动其他代码。**

规范字段（看板实际消费的）
    id            str   稳定标识（由 dept + 去重键 哈希得到，重复录入同一任务会覆盖而非新增）
    dept          str   部门 id（ceo/cfo/cto/cpo/cmo/coo/cro/meeting）或 _unassigned
    title         str   必填
    desc          str   说明（也可写 description）
    status        str   todo | in_progress | done | blocked
    priority      str   high | medium | low
    project       str   项目名（默认取 source，即"来自哪个 agent/渠道"）
    source        str   来源渠道/agent 名（自由文本，如 workbuddy / claude-code / hermes）
    agent         str   同 source，保留上游原义
    external_id   str   上游系统的 id（填了就优先用它做去重键）
    due           str   截止日期（自由文本）
    tags          []str
    collaborators []str 参与协作的部门 id（>=2 时看板画联动线）
    auto          bool  true → 看板显示「🤖 自动化」
    dept_source   str   expert | guessed | none
                        「这个归部门是怎么定的」——上游自己判的，还是引擎猜的。
                        看板据此给"猜出来的"打一个问号标记，提醒人去复核。
"""
from __future__ import annotations

import hashlib
import re

#: 部门别名 → 规范 id
DEPT_ALIASES = {
    "ceo": "ceo", "战略": "ceo", "总裁": "ceo", "总经理": "ceo", "executive": "ceo", "strategy": "ceo",
    "cfo": "cfo", "财务": "cfo", "会计": "cfo", "finance": "cfo", "fin": "cfo", "资金": "cfo",
    "cto": "cto", "技术": "cto", "研发": "cto", "technology": "cto", "tech": "cto", "dev": "cto",
    "cpo": "cpo", "产品": "cpo", "设计": "cpo", "product": "cpo", "design": "cpo",
    "cmo": "cmo", "营销": "cmo", "市场": "cmo", "marketing": "cmo", "brand": "cmo",
    "coo": "coo", "运营": "coo", "operations": "coo", "ops": "coo",
    "cro": "cro", "风控": "cro", "风险": "cro", "合规": "cro", "risk": "cro", "compliance": "cro",
    "meeting": "meeting", "mt": "meeting", "会议室": "meeting", "会议": "meeting",
    "room": "meeting", "board": "meeting",
}

#: 状态别名 → 规范值
STATUS_ALIASES = {
    "todo": "todo", "pending": "todo", "open": "todo", "new": "todo", "backlog": "todo",
    "待办": "todo", "未开始": "todo", "计划": "todo", "待处理": "todo", "未完成": "todo",
    "doing": "in_progress", "in_progress": "in_progress", "in-progress": "in_progress",
    "inprogress": "in_progress", "wip": "in_progress", "working": "in_progress",
    "active": "in_progress", "running": "in_progress", "started": "in_progress",
    "进行中": "in_progress", "执行中": "in_progress", "处理中": "in_progress", "开发中": "in_progress",
    "done": "done", "complete": "done", "completed": "done", "closed": "done", "finished": "done",
    "resolved": "done", "success": "done", "ok": "done",
    "完成": "done", "已完成": "done", "完毕": "done", "结束": "done", "已闭环": "done",
    "block": "blocked", "blocked": "blocked", "stuck": "blocked", "hold": "blocked",
    "on_hold": "blocked", "onhold": "blocked", "paused": "blocked", "fail": "blocked", "failed": "blocked",
    "阻塞": "blocked", "卡住": "blocked", "搁置": "blocked", "暂停": "blocked", "失败": "blocked",
}

#: 优先级别名 → 规范值
PRIORITY_ALIASES = {
    "high": "high", "h": "high", "p0": "high", "p1": "high", "urgent": "high", "critical": "high",
    "blocker": "high", "important": "high", "高": "high", "紧急": "high", "重要": "high", "最高": "high",
    "medium": "medium", "med": "medium", "m": "medium", "p2": "medium", "normal": "medium", "default": "medium",
    "中": "medium", "普通": "medium", "一般": "medium", "中等": "medium",
    "low": "low", "l": "low", "p3": "low", "p4": "low", "minor": "low", "someday": "low", "maybe": "low",
    "低": "low", "次要": "low", "可选": "low", "不急": "low",
}

#: 常见字段别名（上游用什么键名都认）
KEY_ALIASES = {
    "title": ["title", "name", "task", "summary", "subject", "what", "标题", "任务", "名称", "事项"],
    "desc": ["desc", "description", "detail", "details", "note", "notes", "body", "remark", "备注", "说明", "详情"],
    "dept": ["dept", "department", "zone", "team", "room", "owner_dept", "部门", "房间", "归属"],
    "status": ["status", "state", "stage", "progress_state", "状态", "进展"],
    "priority": ["priority", "prio", "importance", "level", "severity", "优先级", "重要度"],
    "project": ["project", "program", "campaign", "initiative", "项目", "所属项目"],
    "source": ["source", "from", "agent", "channel", "origin", "tool", "来源", "渠道", "智能体"],
    "external_id": ["external_id", "extid", "key", "uid", "code", "ref", "ticket", "issue_id",
                    "id", "外部id", "编号", "单号"],
    "due": ["due", "deadline", "due_date", "eta", "until", "截止", "截止日期", "期限"],
    "tags": ["tags", "labels", "keywords", "标签"],
    "collaborators": ["collaborators", "collab", "with", "related_depts", "depts", "协作", "关联部门"],
    "dept_reason": ["dept_reason", "dept_why", "why_dept", "dept_note", "部门理由", "归类理由", "归口理由"],
    "auto": ["auto", "automated", "by_script", "bot", "自动化"],
    "done": ["done", "is_done", "finished", "completed_flag", "已完成标志"],
}

_TITLE_WS = re.compile(r"\s+")
_TITLE_STRIP = re.compile(r"^[\s\-*•\[\]【】()（）0-9.、]+")

#: 标题里出现这些词时，自动归部门（当上游没给 dept）
KEYWORD_RULES = [
    (("财务", "对账", "报表", "发票", "报销", "成本", "预算", "税务", "资金", "结算", "收款", "付款"), "cfo"),
    (("技术", "接口", "代码", "部署", "服务器", "数据库", "bug", "开发", "上线", "容器", "docker"), "cto"),
    (("营销", "推广", "小红书", "公众号", "文案", "投放", "品牌", "活动", "海报"), "cmo"),
    (("运营", "发货", "物流", "库存", "订单", "仓储", "供应链", "采购"), "coo"),
    (("风控", "合规", "审计", "合同", "法务", "风险"), "cro"),
    (("产品", "设计", "原型", "需求", "功能", "原型图", "UI"), "cpo"),
    (("战略", "年度", "规划", "投资", "董事会", "决策"), "ceo"),
    (("会议", "评审", "复盘", "讨论", "例会"), "meeting"),
]


def _first(d: dict, keys: list[str]):
    """按别名顺序取第一个非空值。"""
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    # 大小写不敏感兜底
    low = {str(k).lower(): v for k, v in d.items()}
    for k in keys:
        v = low.get(k.lower())
        if v not in (None, "", [], {}):
            return v
    return None


#: 有些 agent 不写 "priority"，而是丢一个布尔旗标，如 {"urgent": true}
_PRIORITY_FLAGS = (("urgent", "high"), ("blocker", "high"), ("critical", "high"),
                   ("important", "high"), ("p0", "high"),
                   ("low", "low"), ("minor", "low"), ("someday", "low"), ("maybe", "low"))


def _priority_from_flags(d: dict):
    low = {str(k).lower(): v for k, v in d.items()}
    for flag, prio in _PRIORITY_FLAGS:
        v = low.get(flag)
        if v is True or (isinstance(v, str) and v.strip().lower() in ("1", "true", "yes", "y", "on")):
            return prio
    return None


def norm_dept(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower().replace(" ", "").replace("-", "_")
    if not s:
        return None
    s = s.replace("_中心", "").replace("中心", "").replace("办公室", "").replace("室", "")
    if s in DEPT_ALIASES:
        return DEPT_ALIASES[s]
    for alias, dept in DEPT_ALIASES.items():
        if len(alias) > 1 and alias in s:
            return dept
    return None


def norm_status(value, default="todo") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "done" if value else default
    s = str(value).strip().lower()
    return STATUS_ALIASES.get(s, STATUS_ALIASES.get(s.replace(" ", "_"), default))


def norm_priority(value, default="medium") -> str:
    if value is None:
        return default
    s = str(value).strip().lower()
    return PRIORITY_ALIASES.get(s, default)


def guess_dept(*texts) -> str | None:
    blob = " ".join(str(t) for t in texts if t)
    if not blob:
        return None
    for words, dept in KEYWORD_RULES:
        for w in words:
            if w in blob:
                return dept
    return None


def clean_title(raw, limit=80) -> str:
    s = _TITLE_WS.sub(" ", str(raw or "")).strip()
    s = _TITLE_STRIP.sub("", s).strip()
    s = re.sub(r"^\[[A-Za-z_]{1,12}\]\s*", "", s)      # 去掉 "[cfo]" 前缀
    s = s.strip(" -—:：|")
    return s[:limit]


def to_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple, set)):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in re.split(r"[,，;；/|]", str(v)) if x.strip()]


def stable_id(dept: str, dedup_key: str) -> str:
    h = hashlib.sha1(("{}|{}".format(dept, dedup_key)).encode("utf-8")).hexdigest()[:10]
    return "{}-{}".format(dept, h)


def normalize(raw: dict, defaults: dict | None = None, limits: dict | None = None,
              unassigned_key: str = "_unassigned") -> dict:
    """把任意 dict 归一化成规范任务。抛 ValueError 表示这条无法识别。"""
    if not isinstance(raw, dict):
        raise ValueError("任务必须是对象（dict）")
    defaults = defaults or {}
    limits = limits or {"title": 80, "desc": 400, "project": 40}

    title = clean_title(_first(raw, KEY_ALIASES["title"]), limits.get("title", 80))
    if not title:
        raise ValueError("缺少 title/name/标题")

    desc = _first(raw, KEY_ALIASES["desc"])
    desc = _TITLE_WS.sub(" ", str(desc)).strip()[: limits.get("desc", 400)] if desc else ""

    dept_raw = _first(raw, KEY_ALIASES["dept"])
    dept = norm_dept(dept_raw)
    if dept is not None:
        dept_source = "expert"          # 上游自己判的（最可信，看板不打问号）
    else:
        dept = guess_dept(title, desc)  # 上游没写部门 → 按标题关键词猜
        dept_source = "guessed" if dept else "none"
    unassigned = dept is None
    if unassigned:
        dept = unassigned_key
    # 上游判错了（写了部门但认不出来）也留个痕迹，别静默吞掉
    if dept_raw not in (None, "") and dept_source != "expert":
        dept_source = "guessed"

    status_raw = _first(raw, KEY_ALIASES["status"])
    if status_raw is None and _first(raw, KEY_ALIASES["done"]) is not None:
        status_raw = _first(raw, KEY_ALIASES["done"])
    status = norm_status(status_raw, defaults.get("status", "todo"))

    source = str(_first(raw, KEY_ALIASES["source"]) or "").strip()[:40]
    project = str(_first(raw, KEY_ALIASES["project"]) or "").strip()[: limits.get("project", 40)]
    if not project:
        # 默认：项目名 = 来源渠道（"这条是哪个 agent 录的"一眼可见）
        project = source or str(defaults.get("project") or "未归类")

    ext = _first(raw, KEY_ALIASES["external_id"])
    ext = str(ext).strip()[:64] if ext not in (None, "") else ""
    dedup_key = (ext or title).lower()

    auto_v = _first(raw, KEY_ALIASES["auto"])
    if isinstance(auto_v, str):
        auto = auto_v.strip().lower() in ("1", "true", "yes", "y", "on", "是", "自动化")
    else:
        auto = bool(auto_v)

    prio_raw = _first(raw, KEY_ALIASES["priority"])
    if prio_raw is None:
        prio_raw = _priority_from_flags(raw)

    # 「顺手提个认领」的人性化写法：{"title":..., "claim":"my-agent"} 或
    # {"title":..., "claim":{"agent":"my-agent","note":"我能接"}}
    # 这样只会发 HTTP 的 agent 一次请求就能"上报 + 申请接手"，不用学新接口。
    cl = raw.get("claim") if isinstance(raw.get("claim"), dict) else None
    claim_agent = str((cl or {}).get("agent") or (raw.get("claim") if isinstance(raw.get("claim"), str) else "")
                      or _first(raw, ["claim_agent", "claim_by", "认领人", "认领"]) or "").strip()[:40]
    claim_note = str((cl or {}).get("note") or _first(raw, ["claim_note", "认领说明"]) or "").strip()[:200]

    return {
        "id": stable_id(dept, dedup_key),
        "dept": dept,
        "title": title,
        "desc": desc,
        "status": status,
        "priority": norm_priority(prio_raw, defaults.get("priority", "medium")),
        "project": project,
        "source": source,
        "agent": str(_first(raw, ["agent"]) or source).strip()[:40],
        "external_id": ext,
        "dedup_key": dedup_key,
        "due": str(_first(raw, KEY_ALIASES["due"]) or "").strip()[:40],
        "tags": to_list(_first(raw, KEY_ALIASES["tags"]))[:12],
        "collaborators": [d for d in (norm_dept(x) for x in to_list(_first(raw, KEY_ALIASES["collaborators"]))) if d][:8],
        "dept_source": dept_source,
        "dept_reason": _TITLE_WS.sub(" ", str(_first(raw, KEY_ALIASES["dept_reason"]) or "")).strip()[:80],
        "auto": auto,
        "unassigned": unassigned,
        "session": "standalone" if unassigned else None,
        # 不由 upsert 落库，而是交给 ingest.apply_claims 去「提申请」（见 §认领协议）
        "claim": {"agent": claim_agent, "note": claim_note} if claim_agent else None,
    }
