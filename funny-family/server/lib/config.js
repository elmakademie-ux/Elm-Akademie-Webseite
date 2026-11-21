// Loads .env (no dependency) and reports which integrations are configured.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

export function loadEnv(file = path.join(ROOT, '.env')) {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (!m || line.trim().startsWith('#')) continue;
    const v = m[2].replace(/^["']|["']$/g, '');
    if (!(m[1] in process.env)) process.env[m[1]] = v;
  }
}

export function ffmpegInfo() {
  try {
    const r = spawnSync('ffmpeg', ['-version'], { encoding: 'utf8' });
    if (r.status === 0) return { available: true, version: r.stdout.split('\n')[0] };
  } catch { /* fall through */ }
  return { available: false, version: null };
}

// Never exposes key values, only whether they exist.
export function capabilities() {
  return {
    ffmpeg: ffmpegInfo(),
    elevenlabs: { configured: Boolean(process.env.ELEVENLABS_API_KEY) },
    video: {
      configured: Boolean(process.env.VIDEO_API_KEY && process.env.VIDEO_PROVIDER),
      provider: process.env.VIDEO_PROVIDER || null,
      note: 'No video provider adapter is implemented yet (planned for build step 3).',
    },
  };
}
