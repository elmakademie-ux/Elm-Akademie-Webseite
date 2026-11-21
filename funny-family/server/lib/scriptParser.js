// Parses the studio's plain-text script format into structured episodes.
//
//   # Episode 4: The Remote
//   season: 1
//   logline: Bob hides the TV remote.
//
//   ## Scene 1 | Living room | 6s        (location and duration optional)
//   Bob lies on the sofa, eyes closed.   <- action line
//   BOB (yawning): Not today, gravity.   <- dialogue, optional emotion
//   SFX: cushion squeak                  <- sound effect
//   MUSIC: lazy jazz bass                <- background music cue
//
// The raw text is the source of truth; scenes are always derived from it.

export const WORDS_PER_SECOND = 2.6;
export const TARGET_RANGE = [30, 45];

export function slug(n) { return String(n).padStart(2, '0'); }
export function episodeId(season, number) { return `s${slug(season)}e${slug(number)}`; }

function speakerMap(characters) {
  const map = new Map();
  for (const c of characters) {
    const keys = [c.id, c.name, ...(c.aliases || [])];
    for (const k of keys) map.set(k.toLowerCase(), c.id);
  }
  return map;
}

export function estimateDuration(scene) {
  const words = scene.dialogue.reduce((n, d) => n + d.text.split(/\s+/).filter(Boolean).length, 0);
  const speech = words / WORDS_PER_SECOND + scene.dialogue.length * 0.4;
  return Math.max(3, Math.ceil(speech + (scene.action.length ? 1.5 : 0.5)));
}

function parseScene(header, lines, speakers, warnings, label) {
  const parts = header.split('|').map((s) => s.trim());
  const scene = { number: 0, title: parts[0], location: '', duration: null, action: [], dialogue: [], sfx: [], music: [] };
  for (const p of parts.slice(1)) {
    const d = p.match(/^(\d+(?:\.\d+)?)\s*s(?:ec)?$/i);
    if (d) scene.duration = Number(d[1]); else if (!scene.location) scene.location = p;
  }
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const m = line.match(/^([A-Za-z][A-Za-z ]{0,24}?)\s*(?:\(([^)]*)\))?\s*:\s*(.+)$/);
    if (m) {
      const key = m[1].trim();
      const lower = key.toLowerCase();
      if (lower === 'sfx') { scene.sfx.push(m[3]); continue; }
      if (lower === 'music') { scene.music.push(m[3]); continue; }
      if (speakers.has(lower)) {
        scene.dialogue.push({ speaker: speakers.get(lower), emotion: (m[2] || '').trim(), text: m[3].trim() });
        continue;
      }
      if (key === key.toUpperCase() && key.length > 1) {
        warnings.push(`${label}: unknown speaker "${key}" treated as action text`);
      }
    }
    scene.action.push(line.replace(/^\[|\]$/g, ''));
  }
  if (scene.duration == null) { scene.duration = estimateDuration(scene); scene.durationEstimated = true; }
  return scene;
}

export function parseEpisodes(text, characters, defaults = {}) {
  const speakers = speakerMap(characters);
  const blocks = text.replace(/\r\n/g, '\n').split(/^(?=# (?!#))/m).filter((b) => b.trim().startsWith('# '));
  return blocks.map((block, idx) => {
    const lines = block.split('\n');
    const head = lines.shift().replace(/^#\s*/, '').trim();
    const hm = head.match(/^episode\s+(\d+)\s*[:\-–—]?\s*(.*)$/i);
    const number = hm ? Number(hm[1]) : (defaults.number ?? idx + 1);
    const title = (hm ? hm[2] : head) || `Episode ${number}`;
    const meta = {};
    const sceneChunks = [];
    let cur = null;
    for (const l of lines) {
      const sh = l.match(/^##\s+(.*)$/);
      if (sh) { cur = { header: sh[1].replace(/^scene\s*\d*\s*[:\-–—|]?\s*/i, '') || `Scene ${sceneChunks.length + 1}`, lines: [] }; sceneChunks.push(cur); continue; }
      if (!cur) {
        const mm = l.match(/^(\w+)\s*:\s*(.+)$/);
        if (mm) meta[mm[1].toLowerCase()] = mm[2].trim();
      } else cur.lines.push(l);
    }
    const season = Number(meta.season ?? defaults.season ?? 1);
    const id = episodeId(season, number);
    const warnings = [];
    const scenes = sceneChunks.map((c, i) => {
      const s = parseScene(c.header, c.lines, speakers, warnings, `${id} scene ${i + 1}`);
      s.number = i + 1;
      return s;
    });
    const total = scenes.reduce((n, s) => n + s.duration, 0);
    if (!scenes.length) warnings.push(`${id}: no scenes found (start each with "## Scene N | Location | 6s")`);
    else if (total < TARGET_RANGE[0] || total > TARGET_RANGE[1]) {
      warnings.push(`${id}: total length ${total}s is outside the ${TARGET_RANGE[0]}–${TARGET_RANGE[1]}s target`);
    }
    return {
      id, season, number, title, logline: meta.logline || '', sample: meta.sample === 'true',
      script: block.trimEnd() + '\n', scenes, totalDuration: total, warnings,
    };
  });
}
