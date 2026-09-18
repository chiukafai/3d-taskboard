#!/usr/bin/env node
// Node 环境接入（Node 18+ 自带 fetch，无需 npm install）
//
//   node node.mjs "任务标题" cfo in_progress high
//   BOARD_URL=http://nas:8787 node node.mjs "..."
//
// 也可以在别的脚本里 import：
//   import { record } from './node.mjs';
//   await record({ title: '联调完成', dept: 'cto', status: 'done', source: 'cursor' });

const BOARD = (process.env.BOARD_URL || 'http://127.0.0.1:8787').replace(/\/+$/, '');
const TOKEN = process.env.BOARD_TOKEN || '';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  if (TOKEN) h.Authorization = 'Bearer ' + TOKEN;
  return h;
}

export async function record(payload) {
  const r = await fetch(BOARD + '/api/tasks', {
    method: 'POST', headers: headers(), body: JSON.stringify(payload),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${JSON.stringify(j)}`);
  return j;
}

export async function list(query = '') {
  const r = await fetch(BOARD + '/api/tasks' + query, { headers: headers() });
  return r.json();
}

// 直接执行时按命令行参数录一条
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const _self = fileURLToPath(import.meta.url);
const _isMain = process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === _self.toLowerCase();

if (_isMain) {
  const [title, dept, status, priority, source] = process.argv.slice(2);
  if (!title) {
    console.error('用法: node node.mjs "任务标题" [dept] [status] [priority] [source]');
    process.exit(2);
  }
  const out = await record({
    title, dept, status: status || 'todo', priority: priority || 'medium',
    source: source || process.env.AGENT_NAME || 'node-agent',
  });
  console.log(JSON.stringify(out, null, 1));
}
