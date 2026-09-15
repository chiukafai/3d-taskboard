#!/usr/bin/env python3
"""
任务提取脚本 — 从 WorkBuddy 记忆文件中提取所有任务，按部门分类，生成 tasks.js

数据源：
  1. ~/.workbuddy/task_log.md          — 结构化任务日志
  2. ~/.workbuddy/memory/CONTEXT_INDEX.md — 活跃主题、任务索引、决策记录
  3. ~/.workbuddy/MEMORY.md             — 项目描述、自动化配置
  4. 当前 workspace daily log           — 最近工作记录

用法：
  python3 extract-tasks.py
  
输出：
  tasks-data/tasks.js — 看板直接加载的任务数据文件
  
如需换账号使用，只需确保上述数据源路径存在即可（WorkBuddy 标准化路径）。
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

HOME = Path.home()
WORKBUDDY = HOME / ".workbuddy"
KEYMAP_PATH = Path(__file__).parent / "keymap.json"
OUTPUT_PATH = Path(__file__).parent / "tasks.js"

def load_keymap():
    with open(KEYMAP_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_department(title, project, description, keymap):
    """根据关键词匹配确定主部门和协作者"""
    text = f"{title} {project} {description}".lower()
    
    # 计算每个部门的得分
    scores = {}
    for rule in keymap["rules"]:
        dept = rule["department"]
        score = 0
        for kw in rule["keywords"]:
            if kw.lower() in text:
                score += rule["weight"]
        if score > 0:
            scores[dept] = score
    
    # 找出协作者
    collaborators = []
    for rule in keymap.get("secondary_rules", []):
        if rule.get("role") == "collaborator":
            for kw in rule["keywords"]:
                if kw.lower() in text:
                    if rule["department"] not in collaborators:
                        collaborators.append(rule["department"])
    
    # 主部门是得分最高的
    if not scores:
        return "cto", collaborators  # 默认归入 CTO
    
    primary = max(scores, key=scores.get)
    
    # 如果主部门的得分并不明显高于其他部门，将高分部门也加入协作者
    threshold = scores[primary] * 0.6
    for dept, score in scores.items():
        if dept != primary and score >= threshold:
            if dept not in collaborators:
                collaborators.append(dept)
    
    # 移除重复的主部门
    if primary in collaborators:
        collaborators.remove(primary)
    
    return primary, collaborators

def is_auto_task(title, description, keymap):
    """检测是否为自动化任务"""
    text = f"{title} {description}".lower()
    for kw in keymap.get("auto_detect", {}).get("keywords", []):
        if kw.lower() in text:
            return True
    return False

def parse_task_log():
    """解析 task_log.md"""
    tasks = []
    task_log_path = WORKBUDDY / "task_log.md"
    if not task_log_path.exists():
        print(f"  ⚠ 未找到 {task_log_path}")
        return tasks
    
    with open(task_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配每个任务：## 日期 开头，到下一个 ## 或 --- 或文件末尾
    date_blocks = re.split(r'\n## (\d{4}-\d{2}-\d{2})', content)
    
    for i in range(1, len(date_blocks), 2):
        date_str = date_blocks[i]
        block = date_blocks[i+1] if i+1 < len(date_blocks) else ""
        
        # 匹配 ### 状态 [分类] 标题
        task_pattern = r'### (✅|🔄) \[([^\]]+)\] (.+?)(?:\n|$)'
        for match in re.finditer(task_pattern, block):
            status_icon = match.group(1)
            category = match.group(2)
            title = match.group(3).strip()
            
            # 提取项目名
            project = category
            
            # 提取描述（任务后的段落直到下一个 ###）
            task_start = match.end()
            next_task = re.search(r'\n### ', block[task_start:])
            desc_end = task_start + next_task.start() if next_task else len(block)
            description = block[task_start:desc_end].strip()[:500]
            
            status = "done" if status_icon == "✅" else "in_progress"
            auto = is_auto_task(title, description, load_keymap())
            
            tasks.append({
                "title": title,
                "status": status,
                "project": project,
                "date": date_str,
                "description": description[:200],
                "auto": auto,
                "source": "task_log.md"
            })
    
    return tasks

def parse_context_index():
    """解析 CONTEXT_INDEX.md"""
    tasks = []
    ctx_path = WORKBUDDY / "memory" / "CONTEXT_INDEX.md"
    if not ctx_path.exists():
        print(f"  ⚠ 未找到 {ctx_path}")
        return tasks
    
    with open(ctx_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析活跃主题
    theme_pattern = r'\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*.+?\|\s*(✅|🔄)\s*(.+?)\s*\|'
    for match in re.finditer(theme_pattern, content):
        title = match.group(1).strip()
        date = match.group(2)
        status_icon = match.group(3)
        status_text = match.group(4).strip()
        
        status = "done" if status_icon == "✅" else "in_progress"
        priority = "high" if "重要" in status_text or "高" in status_text else "medium"
        
        tasks.append({
            "title": title,
            "status": status,
            "project": "从CONTEXT_INDEX提取",
            "date": date,
            "priority": priority,
            "source": "CONTEXT_INDEX.md (活跃主题)"
        })
    
    # 解析任务索引
    task_idx_pattern = r'- \*\*(\d{4}-\d{2}-\d{2})\*\* — (.+?) — (✅|🔄)'
    for match in re.finditer(task_idx_pattern, content):
        date = match.group(1)
        title = match.group(2).strip()
        status_icon = match.group(3)
        
        status = "done" if status_icon == "✅" else "in_progress"
        
        tasks.append({
            "title": title,
            "status": status,
            "project": "从CONTEXT_INDEX提取",
            "date": date,
            "priority": "medium",
            "source": "CONTEXT_INDEX.md (任务索引)"
        })
    
    # 解析决策记录
    decision_pattern = r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|'
    for match in re.finditer(decision_pattern, content):
        if "决策内容" in content[:match.start()].split('\n')[-3]:
            continue
        date = match.group(1)
        decision = match.group(2).strip()
        impact = match.group(3).strip()
        
        tasks.append({
            "title": f"决策: {decision[:40]}",
            "status": "done",
            "project": "关键决策",
            "date": date,
            "priority": "high",
            "description": impact,
            "source": "CONTEXT_INDEX.md (决策记录)"
        })
    
    return tasks

def generate_tasks():
    """主函数：从所有数据源提取任务，分类，输出 tasks.js"""
    print("📊 WorkBuddy 任务提取器")
    print("=" * 50)
    
    keymap = load_keymap()
    
    # 从各数据源提取
    print("\n📁 读取数据源...")
    tasks = []
    tasks.extend(parse_task_log())
    print(f"  task_log.md → {len([t for t in tasks if t['source']=='task_log.md'])} 条")
    
    ctx_tasks = parse_context_index()
    tasks.extend(ctx_tasks)
    print(f"  CONTEXT_INDEX.md → {len(ctx_tasks)} 条")
    
    total = len(tasks)
    print(f"\n  共提取 {total} 条任务")
    
    # 去重
    seen = set()
    unique = []
    for t in tasks:
        key = t["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(t)
    if len(unique) < len(tasks):
        print(f"  去重后: {len(unique)} 条（移除 {len(tasks) - len(unique)} 条重复）")
    tasks = unique
    
    # 按部门分类
    print("\n🔀 按部门分类...")
    departments = {dept: [] for dept in ['ceo','cfo','cto','cpo','cmo','coo','cro','meeting','lounge']}
    counter = {}
    
    for task in tasks:
        title = task.get("title", "")
        project = task.get("project", "")
        desc = task.get("description", "")
        
        primary, collaborators = classify_department(title, project, desc, keymap)
        
        dept_tasks = departments.get(primary, departments['cto'])
        task_id_prefix = primary[:3]
        task_num = counter.get(primary, 0) + 1
        counter[primary] = task_num
        
        entry = {
            "id": f"{task_id_prefix}{task_num}",
            "title": title[:50],
            "status": task.get("status", "todo"),
            "priority": task.get("priority", "medium"),
            "project": project[:20],
        }
        
        if task.get("auto"):
            entry["auto"] = True
        if collaborators:
            entry["collaborators"] = [primary] + collaborators
        
        dept_tasks.append(entry)
    
    # 输出统计
    print()
    for dept, task_list in departments.items():
        if task_list:
            print(f"  {dept}: {len(task_list)} 条")
    
    # 生成 JS 文件
    print(f"\n💾 生成 {OUTPUT_PATH} ...")
    
    js_content = f"""window.TASK_DATA = {json.dumps(departments, ensure_ascii=False, indent=2)};

window.TASK_META = {{
  "generated": "{datetime.now().isoformat()}",
  "sources": ["task_log.md", "CONTEXT_INDEX.md"],
  "totalTasks": {sum(len(v) for v in departments.values())},
  "totalDepartments": {len([d for d, v in departments.items() if v])}
}};
"""
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"  ✅ 已生成，共 {sum(len(v) for v in departments.values())} 条任务")
    print(f"\n  ⚡ 刷新看板即可加载最新数据")

if __name__ == "__main__":
    generate_tasks()
