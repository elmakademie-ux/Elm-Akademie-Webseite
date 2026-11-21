// Tiny JSON-file store with atomic writes. Data lives in ./data (gitignored).
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './config.js';

export const DATA = path.join(ROOT, 'data');
export const SEED = path.join(ROOT, 'seed');

export function ensureDirs() {
  for (const d of ['episodes', 'characters', 'output']) fs.mkdirSync(path.join(DATA, d), { recursive: true });
}

export function readJson(rel, fallback) {
  try { return JSON.parse(fs.readFileSync(path.join(DATA, rel), 'utf8')); } catch { return fallback; }
}

export function writeJson(rel, obj) {
  const file = path.join(DATA, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2));
  fs.renameSync(tmp, file);
}

export function listJson(dirRel) {
  const dir = path.join(DATA, dirRel);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
}

export function remove(rel) { fs.rmSync(path.join(DATA, rel), { force: true, recursive: true }); }
