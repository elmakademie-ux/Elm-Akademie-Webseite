// The Funny Family Studio – HTTP server (no external dependencies).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, loadEnv, capabilities } from './lib/config.js';
import { DATA, SEED, ensureDirs, readJson, writeJson, listJson, remove } from './lib/store.js';
import { DEFAULT_CHARACTERS } from './lib/characters.js';
import { parseEpisodes } from './lib/scriptParser.js';
import { buildEpisodePrompts } from './lib/promptBuilder.js';
import { DEFAULT_SETTINGS, estimateEpisode } from './lib/costs.js';

loadEnv();
ensureDirs();

const WEB = path.join(ROOT, 'web');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.mp4': 'video/mp4', '.json': 'application/json' };
const IMG_EXT = { 'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp' };

// ---------- data access ----------
const getCharacters = () => {
  const saved = listJson('characters');
  const byId = new Map(saved.map((c) => [c.id, c]));
  return DEFAULT_CHARACTERS.map((d) => byId.get(d.id) ?? d);
};
const getSettings = () => ({ ...DEFAULT_SETTINGS, ...readJson('settings.json', {}) });
const getEpisodes = () => listJson('episodes');
const getEpisode = (id) => readJson(`episodes/${id}.json`, null);

function seedIfEmpty() {
  if (getEpisodes().length) return;
  const dir = path.join(SEED, 'episodes');
  if (!fs.existsSync(dir)) return;
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.md'))) {
    for (const ep of parseEpisodes(fs.readFileSync(path.join(dir, f), 'utf8'), getCharacters())) saveEpisode(ep);
  }
}
function saveEpisode(ep) { writeJson(`episodes/${ep.id}.json`, { ...ep, updatedAt: new Date().toISOString() }); }

function outputInfo(id) {
  const file = path.join(DATA, 'output', id, 'final.mp4');
  const exists = fs.existsSync(file);
  return { finalVideo: exists ? { url: `/media/output/${id}/final.mp4`, bytes: fs.statSync(file).size } : null };
}
function pipeline(ep) {
  // Honest status: a stage is "done" only when its artefact really exists on disk.
  const outDir = path.join(DATA, 'output', ep.id);
  const has = (sub, ext) => fs.existsSync(path.join(outDir, sub)) && fs.readdirSync(path.join(outDir, sub)).some((f) => f.endsWith(ext));
  const clips = has('clips', '.mp4'), voice = has('voice', '.mp3'), final = fs.existsSync(path.join(outDir, 'final.mp4'));
  return [
    { stage: 'Script', state: ep.scenes.length ? 'done' : 'todo' },
    { stage: 'Prompts', state: ep.scenes.length ? 'ready' : 'todo' },
    { stage: 'Clips', state: clips ? 'done' : 'todo' },
    { stage: 'Voice', state: voice ? 'done' : 'todo' },
    { stage: 'Render', state: final ? 'done' : 'todo' },
  ];
}
const summarize = (ep) => ({ id: ep.id, season: ep.season, number: ep.number, title: ep.title, logline: ep.logline,
  sample: ep.sample, totalDuration: ep.totalDuration, sceneCount: ep.scenes.length, warnings: ep.warnings,
  characters: [...new Set(ep.scenes.flatMap((s) => s.dialogue.map((d) => d.speaker)))], pipeline: pipeline(ep), ...outputInfo(ep.id) });

// ---------- http helpers ----------
const send = (res, code, body, type = 'application/json') => {
  res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(type === 'application/json' ? JSON.stringify(body) : body);
};
const readBody = (req, limit = 15e6) => new Promise((resolve, reject) => {
  const chunks = []; let size = 0;
  req.on('data', (c) => { size += c.length; if (size > limit) { reject(Object.assign(new Error('Body too large'), { status: 413 })); req.destroy(); } else chunks.push(c); });
  req.on('end', () => resolve(Buffer.concat(chunks)));
  req.on('error', reject);
});
const readJsonBody = async (req) => { try { return JSON.parse((await readBody(req)).toString() || '{}'); } catch { throw Object.assign(new Error('Invalid JSON'), { status: 400 }); } };
const bad = (status, message) => Object.assign(new Error(message), { status });
const safeId = (s) => { if (!/^[a-z0-9_-]+$/i.test(s)) throw bad(400, 'Invalid id'); return s; };

// ---------- API ----------
async function api(req, res, url) {
  const p = url.pathname.replace(/^\/api/, '');
  const m = req.method;
  let r;

  if (m === 'GET' && p === '/status') {
    const eps = getEpisodes(); const sums = eps.map(summarize);
    return send(res, 200, {
      capabilities: capabilities(),
      counts: { episodes: eps.length, target: 30, seasons: new Set(eps.map((e) => e.season)).size,
        withFinalVideo: sums.filter((s) => s.finalVideo).length, samples: eps.filter((e) => e.sample).length,
        warnings: eps.reduce((n, e) => n + e.warnings.length, 0) },
    });
  }
  if (m === 'GET' && p === '/characters') return send(res, 200, getCharacters());
  if ((r = p.match(/^\/characters\/([\w-]+)$/)) && m === 'PUT') {
    const id = safeId(r[1]); const cur = getCharacters().find((c) => c.id === id);
    if (!cur) throw bad(404, 'Unknown character');
    const b = await readJsonBody(req);
    const next = { ...cur };
    for (const k of ['name', 'age', 'role', 'tagline', 'personality', 'appearance']) if (k in b) next[k] = b[k];
    if (Array.isArray(b.expressions)) next.expressions = b.expressions.map(String).slice(0, 24);
    if (b.voice) next.voice = { ...cur.voice, ...Object.fromEntries(['description', 'voiceId', 'stability', 'similarity'].filter((k) => k in b.voice).map((k) => [k, b.voice[k]])) };
    writeJson(`characters/${id}.json`, next);
    return send(res, 200, next);
  }
  if ((r = p.match(/^\/characters\/([\w-]+)\/references$/)) && m === 'POST') {
    const id = safeId(r[1]); const cur = getCharacters().find((c) => c.id === id);
    if (!cur) throw bad(404, 'Unknown character');
    const ext = IMG_EXT[(req.headers['content-type'] || '').split(';')[0]];
    if (!ext) throw bad(415, 'Upload a PNG, JPEG or WEBP image');
    const buf = await readBody(req);
    const label = String(url.searchParams.get('label') || 'reference').replace(/[^\w -]/g, '').slice(0, 40) || 'reference';
    const file = `${Date.now()}${ext}`;
    fs.mkdirSync(path.join(DATA, 'characters', id), { recursive: true });
    fs.writeFileSync(path.join(DATA, 'characters', id, file), buf);
    const next = { ...cur, referenceImages: [...cur.referenceImages, { file, label, url: `/media/characters/${id}/${file}`, source: 'upload' }] };
    writeJson(`characters/${id}.json`, next);
    return send(res, 201, next);
  }
  if ((r = p.match(/^\/characters\/([\w-]+)\/references\/([\w.-]+)$/)) && m === 'DELETE') {
    const id = safeId(r[1]); const cur = getCharacters().find((c) => c.id === id);
    if (!cur) throw bad(404, 'Unknown character');
    const file = path.basename(r[2]);
    remove(`characters/${id}/${file}`);
    const next = { ...cur, referenceImages: cur.referenceImages.filter((i) => i.file !== file) };
    writeJson(`characters/${id}.json`, next);
    return send(res, 200, next);
  }

  if (m === 'GET' && p === '/episodes') return send(res, 200, getEpisodes().map(summarize));
  if (m === 'POST' && p === '/episodes/import') {
    const b = await readJsonBody(req);
    if (typeof b.text !== 'string' || !b.text.trim()) throw bad(400, 'No script text provided');
    const eps = parseEpisodes(b.text, getCharacters(), { season: b.season });
    if (!eps.length) throw bad(422, 'No episodes found. Each episode must start with "# Episode N: Title".');
    const replaced = [];
    for (const ep of eps) { if (getEpisode(ep.id)) replaced.push(ep.id); saveEpisode(ep); }
    return send(res, 201, { imported: eps.map((e) => e.id), replaced, warnings: eps.flatMap((e) => e.warnings) });
  }
  if ((r = p.match(/^\/episodes\/([\w-]+)$/))) {
    const id = safeId(r[1]); const ep = getEpisode(id);
    if (m === 'GET') { if (!ep) throw bad(404, 'Episode not found'); return send(res, 200, { ...ep, pipeline: pipeline(ep), ...outputInfo(id) }); }
    if (m === 'PUT') {
      if (!ep) throw bad(404, 'Episode not found');
      const b = await readJsonBody(req);
      const [parsed, ...extra] = parseEpisodes(String(b.script || ''), getCharacters(), { season: ep.season, number: ep.number });
      if (!parsed || extra.length) throw bad(422, 'Script must contain exactly one episode starting with "# Episode N: Title".');
      if (parsed.id !== id) throw bad(422, `Season/episode number changed (${id} → ${parsed.id}). Use Import to create a new episode.`);
      saveEpisode({ ...parsed, sample: b.keepSample ? ep.sample : parsed.sample });
      return send(res, 200, { ...getEpisode(id), pipeline: pipeline(parsed) });
    }
    if (m === 'DELETE') { remove(`episodes/${id}.json`); return send(res, 200, { deleted: id }); }
  }
  if ((r = p.match(/^\/episodes\/([\w-]+)\/prompts$/)) && m === 'GET') {
    const ep = getEpisode(safeId(r[1])); if (!ep) throw bad(404, 'Episode not found');
    return send(res, 200, buildEpisodePrompts(ep, getCharacters()));
  }
  if ((r = p.match(/^\/episodes\/([\w-]+)\/estimate$/)) && m === 'GET') {
    const ep = getEpisode(safeId(r[1])); if (!ep) throw bad(404, 'Episode not found');
    return send(res, 200, { ...estimateEpisode(ep, getSettings()), generationEnabled: false,
      generationNote: 'Paid generation is not wired up yet. When it is, every job will require your explicit approval of this estimate.' });
  }

  if (m === 'GET' && p === '/settings') return send(res, 200, getSettings());
  if (m === 'PUT' && p === '/settings') {
    const b = await readJsonBody(req); const cur = getSettings();
    const num = (v) => (v === '' || v == null ? null : Number.isFinite(Number(v)) && Number(v) >= 0 ? Number(v) : (() => { throw bad(400, 'Rates must be non-negative numbers'); })());
    const rates = { ...cur.rates };
    for (const k of ['videoPerSecond', 'ttsPer1kChars', 'imagePerImage']) if (b.rates && k in b.rates) rates[k] = num(b.rates[k]);
    if (b.rates?.currency) rates.currency = String(b.rates.currency).slice(0, 5);
    const next = { ...cur, rates, retryAllowance: b.retryAllowance != null ? Math.min(2, Math.max(0, Number(b.retryAllowance) || 0)) : cur.retryAllowance };
    writeJson('settings.json', next);
    return send(res, 200, next);
  }

  // Real ElevenLabs endpoint: GET https://api.elevenlabs.io/v1/voices (header xi-api-key).
  if (m === 'GET' && p === '/voices') {
    const key = process.env.ELEVENLABS_API_KEY;
    if (!key) throw bad(503, 'ELEVENLABS_API_KEY is not set. Add it to .env and restart the server.');
    let resp;
    try { resp = await fetch('https://api.elevenlabs.io/v1/voices', { headers: { 'xi-api-key': key } }); }
    catch (e) { throw bad(502, `Could not reach ElevenLabs: ${e.message}`); }
    if (!resp.ok) throw bad(resp.status === 401 ? 401 : 502, `ElevenLabs returned ${resp.status}`);
    const data = await resp.json();
    return send(res, 200, (data.voices || []).map((v) => ({ voiceId: v.voice_id, name: v.name, category: v.category, previewUrl: v.preview_url })));
  }
  throw bad(404, 'Not found');
}

function serveFile(res, file) {
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) return send(res, 404, 'Not found', 'text/plain');
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Content-Length': st.size });
    fs.createReadStream(file).pipe(res);
  });
}
const inside = (base, rel) => { const f = path.resolve(base, '.' + path.sep + decodeURIComponent(rel)); return f.startsWith(base + path.sep) ? f : null; };

export function createServer() {
  seedIfEmpty();
  return http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (url.pathname.startsWith('/api/')) return await api(req, res, url);
      if (url.pathname.startsWith('/media/')) {
        const f = inside(DATA, url.pathname.replace('/media/', ''));
        return f ? serveFile(res, f) : send(res, 400, 'Bad path', 'text/plain');
      }
      const f = inside(WEB, url.pathname === '/' ? 'index.html' : url.pathname.slice(1));
      return f ? serveFile(res, f) : send(res, 400, 'Bad path', 'text/plain');
    } catch (e) {
      send(res, e.status || 500, { error: e.status ? e.message : 'Internal server error' });
      if (!e.status) console.error(e);
    }
  });
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const port = Number(process.env.PORT) || 4310;
  createServer().listen(port, '127.0.0.1', () => console.log(`Funny Family Studio → http://localhost:${port}`));
}
