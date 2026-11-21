// Funny Family Studio – dashboard frontend (vanilla ES modules, no build step).
const $ = (s) => document.querySelector(s);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

async function api(path, opts = {}) {
  const r = await fetch('/api' + path, {
    method: opts.method || 'GET',
    headers: opts.raw ? { 'Content-Type': opts.type } : opts.body ? { 'Content-Type': 'application/json' } : {},
    body: opts.raw ? opts.raw : opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
  return data;
}
function toast(msg, err = false) {
  const t = $('#toast'); t.textContent = msg; t.className = 'toast' + (err ? ' err' : ''); t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 4500);
}
const guard = (fn) => async (...a) => { try { await fn(...a); } catch (e) { toast(e.message, true); } };

let CHARS = [];
const charById = (id) => CHARS.find((c) => c.id === id);
function avatar(c, cls = '') {
  const img = c?.referenceImages?.[0];
  if (img) return `<img class="av ${cls}" src="${esc(img.url)}" alt="${esc(c.name)}" title="${esc(c.name)}">`;
  return `<div class="av ${cls}" style="background:${esc(c?.color || '#888')}" title="${esc(c?.name)} (placeholder – no reference image yet)">${esc((c?.name || '?')[0])}</div>`;
}
const stepper = (p) => `<div class="steps">${p.map((s) => `<i class="${s.state}" title="${esc(s.stage)}: ${esc(s.state)}"></i>`).join('')}</div>
  <div class="steplabels">${p.map((s) => `<span>${esc(s.stage)}</span>`).join('')}</div>`;

// ---------- views ----------
async function dashboard() {
  const [st, eps] = await Promise.all([api('/status'), api('/episodes')]);
  const c = st.counts, cap = st.capabilities;
  const flag = (ok, label, hint) => `<div class="row spread"><span>${label}</span><span class="pill ${ok ? 'ok' : 'warn'}">${ok ? 'ready' : hint}</span></div>`;
  const finals = eps.filter((e) => e.finalVideo);
  return `<h1>Production Dashboard</h1><p class="sub">Script → scenes → clips → voices → FFmpeg render. Nothing paid runs without your approval.</p>
  <div class="grid g4">
    <div class="card stat"><b>${c.episodes}<small style="font-size:16px;color:var(--mut)"> / ${c.target}</small></b><span>Episodes imported${c.samples ? ` (${c.samples} sample)` : ''}</span></div>
    <div class="card stat"><b>${c.seasons}</b><span>Seasons</span></div>
    <div class="card stat"><b>${c.withFinalVideo}</b><span>Finished videos on disk</span></div>
    <div class="card stat"><b>${c.warnings}</b><span>Script warnings</span></div>
  </div>
  <h2>System readiness</h2>
  <div class="grid g2">
    <div class="card grid" style="gap:10px">
      ${flag(cap.ffmpeg.available, 'FFmpeg', 'not installed')}
      ${flag(cap.elevenlabs.configured, 'ElevenLabs API key', 'set ELEVENLABS_API_KEY')}
      ${flag(cap.video.configured, 'AI video provider', 'not configured')}
      <small style="color:var(--mut)">${esc(cap.ffmpeg.version || '')}</small>
    </div>
    <div class="card"><h3>Build progress</h3>
      <div class="grid" style="gap:6px;color:var(--mut);font-size:14px">
        <div>✅ Dashboard · Episode manager · Character library</div>
        <div>⬜ Video provider adapter &amp; clip generation (needs your provider choice)</div>
        <div>⬜ ElevenLabs dialogue synthesis</div>
        <div>⬜ FFmpeg 9:16 assembly, subtitles, 1080×1920 export</div>
      </div></div>
  </div>
  <h2>Characters</h2>
  <div class="row">${CHARS.map((ch) => `<a href="#/characters/${ch.id}" class="card hover row" style="padding:12px 16px">${avatar(ch)}<div><b>${esc(ch.name)}</b><br><small style="color:var(--mut)">${esc(ch.role)}</small></div></a>`).join('')}</div>
  <h2>Latest episodes</h2>
  <div class="grid g3">${eps.slice(0, 6).map(epCard).join('') || '<div class="empty">No episodes yet. Open Episodes → Import.</div>'}</div>
  ${finals.length ? `<h2>Finished videos</h2><div class="row">${finals.map((e) => `<a class="pill ok" href="#/episodes/${e.id}">${esc(e.title)}</a>`).join('')}</div>` : ''}`;
}

function epCard(e) {
  return `<a class="card hover ep" href="#/episodes/${e.id}">
    <div class="poster">S${e.season}·E${e.number}</div>
    <div class="row spread"><h3 style="margin:0">${esc(e.title)}</h3>${e.sample ? '<span class="pill acc">sample</span>' : ''}</div>
    <div style="color:var(--mut);font-size:14px">${esc(e.logline)}</div>
    <div class="row spread"><div class="faces">${e.characters.map((id) => avatar(charById(id))).join('')}</div>
      <span class="pill ${e.warnings.length ? 'warn' : ''}">${e.sceneCount} scenes · ${e.totalDuration}s</span></div>
    ${stepper(e.pipeline)}</a>`;
}

async function episodes() {
  const eps = await api('/episodes');
  const seasons = [...new Set(eps.map((e) => e.season))].sort((a, b) => a - b);
  return `<div class="row spread"><div><h1>Episodes</h1><p class="sub">${eps.length} of 30 imported · organised by season</p></div>
    <button class="btn pri" id="toggle-import">+ Import scripts</button></div>
  <div id="import" class="card" hidden>
    <h3>Import episode scripts</h3>
    <p class="sub" style="margin-bottom:8px">Paste one or many episodes, or load a .md/.txt file. Each episode starts with <code># Episode N: Title</code> and a <code>season: N</code> line. Existing episodes with the same season/number are replaced.</p>
    <details style="margin-bottom:10px;color:var(--mut)"><summary>Script format</summary><pre class="prompt">${esc(`# Episode 4: The Remote
season: 1
logline: Bob hides the remote.

## Scene 1 | Living room | 6s
Bob lies on the sofa, eyes closed.
BOB (yawning): Not today, gravity.
SFX: cushion squeak
MUSIC: lazy jazz bass`)}</pre></details>
    <input type="file" id="file" accept=".md,.txt,text/plain" style="margin-bottom:10px">
    <textarea id="imp-text" class="code" style="min-height:200px" placeholder="# Episode 3: ..."></textarea>
    <div class="row" style="margin-top:12px"><button class="btn pri" id="do-import">Import</button><span id="imp-result"></span></div>
  </div>
  ${seasons.map((s) => `<h2>Season ${s}</h2><div class="grid g3">${eps.filter((e) => e.season === s).map(epCard).join('')}</div>`).join('') || '<div class="empty" style="margin-top:20px">No episodes yet.</div>'}`;
}
function episodesBind() {
  $('#toggle-import').onclick = () => ($('#import').hidden = !$('#import').hidden);
  $('#file').onchange = async (e) => { const f = e.target.files[0]; if (f) $('#imp-text').value = await f.text(); };
  $('#do-import').onclick = guard(async () => {
    const r = await api('/episodes/import', { method: 'POST', body: { text: $('#imp-text').value } });
    toast(`Imported ${r.imported.length} episode(s)${r.replaced.length ? `, replaced ${r.replaced.length}` : ''}.`);
    if (r.warnings.length) alert('Warnings:\n' + r.warnings.join('\n'));
    route();
  });
}

let epTab = 'scenes';
async function episodeDetail(id) {
  const ep = await api('/episodes/' + id);
  const tabs = [['scenes', 'Scenes & timeline'], ['script', 'Script editor'], ['prompts', 'Video prompts'], ['cost', 'Cost & approval'], ['final', 'Final video']];
  let body = '';
  if (epTab === 'scenes') body = scenesView(ep);
  if (epTab === 'script') body = `<textarea id="script" class="code" spellcheck="false">${esc(ep.script)}</textarea>
    <div class="row" style="margin-top:12px"><button class="btn pri" id="save-script">Save script</button><span class="pill">Scenes are re-derived on save</span></div>`;
  if (epTab === 'prompts') {
    const pr = await api(`/episodes/${id}/prompts`);
    body = `<div class="info-box">Prompts are built from the character bible (Character Library). They are not sent anywhere until a video provider is connected and you approve the cost.</div>` +
      pr.map((p) => `<div class="card" style="margin-top:12px"><div class="row spread"><h3>Scene ${p.scene} · ${p.duration}s</h3><button class="btn sm" data-copy="${p.scene}">Copy</button></div>
      <pre class="prompt" id="pr${p.scene}">${esc(p.prompt)}</pre><small style="color:var(--mut)">Negative: ${esc(p.negative)}</small></div>`).join('');
  }
  if (epTab === 'cost') {
    const est = await api(`/episodes/${id}/estimate`);
    body = `<div class="card"><h3>Estimated API cost</h3><table><tr><th>Item</th><th>Quantity</th><th>Cost (${esc(est.currency)})</th></tr>
      ${est.lines.map((l) => `<tr><td>${esc(l.item)}</td><td>${esc(l.qty)}</td><td>${l.cost === null ? '<span class="pill warn">rate not set</span>' : l.cost.toFixed(2)}</td></tr>`).join('')}
      <tr><td><b>Subtotal</b></td><td></td><td><b>${est.subtotal === null ? '—' : est.subtotal.toFixed(2)}</b></td></tr>
      <tr><td>With retry allowance</td><td></td><td>${est.withRetryAllowance === null ? '—' : est.withRetryAllowance.toFixed(2)}</td></tr></table>
      <p class="sub" style="margin-top:12px">${esc(est.note)} <a href="#/settings" style="color:var(--acc)">Edit rates →</a></p>
      <div class="info-box">${esc(est.generationNote)}</div>
      <div class="row" style="margin-top:14px"><button class="btn pri" disabled title="Not available yet">Approve &amp; generate clips</button></div></div>`;
  }
  if (epTab === 'final') {
    body = ep.finalVideo ? `<video controls src="${esc(ep.finalVideo.url)}"></video><div class="row" style="margin-top:12px"><a class="btn pri" download href="${esc(ep.finalVideo.url)}">Download MP4</a><span class="pill">${(ep.finalVideo.bytes / 1e6).toFixed(1)} MB</span></div>`
      : `<div class="empty"><b>No final video exists yet.</b><br>This tab only shows a video when <code>data/output/${esc(ep.id)}/final.mp4</code> is really on disk.</div>`;
  }
  return `<a href="#/episodes" style="color:var(--mut)">← Episodes</a>
  <div class="row spread" style="margin-top:8px"><div><h1>${esc(ep.title)}</h1><p class="sub">Season ${ep.season} · Episode ${ep.number} · ${esc(ep.logline)}</p></div>
    <div class="row">${ep.sample ? '<span class="pill acc">sample script</span>' : ''}<button class="btn danger sm" id="del-ep">Delete</button></div></div>
  ${ep.warnings.map((w) => `<div class="warn-box">⚠ ${esc(w)}</div>`).join('')}
  <div class="card">${stepper(ep.pipeline)}</div>
  <div class="tabs">${tabs.map(([k, l]) => `<button data-tab="${k}" class="${epTab === k ? 'on' : ''}">${l}</button>`).join('')}</div>${body}`;
}
function scenesView(ep) {
  const total = ep.scenes.reduce((n, s) => n + s.duration, 0) || 1;
  const col = (s) => charById(s.dialogue[0]?.speaker)?.color || '#4a5372';
  return `<div class="card"><div class="row spread"><h3>Timeline</h3><span class="pill">${total}s total · target 30–45s</span></div>
    <div class="timeline">${ep.scenes.map((s) => `<div class="tl ${s.durationEstimated ? 'est' : ''}" style="flex:${s.duration};background:${col(s)}" title="Scene ${s.number}: ${s.duration}s${s.durationEstimated ? ' (estimated)' : ''}" onclick="document.getElementById('sc${s.number}').scrollIntoView({behavior:'smooth'})">${s.number}</div>`).join('')}</div>
    <small style="color:var(--mut)">Striped = duration estimated from dialogue length. Add <code>| 6s</code> to a scene header to fix it.</small></div>
  ${ep.scenes.map((s) => `<div class="card scene" id="sc${s.number}" style="margin-top:14px"><div class="n">${s.number}</div><div>
    <div class="row spread"><h3>${esc(s.title || 'Scene ' + s.number)}${s.location ? ` · ${esc(s.location)}` : ''}</h3><span class="pill">${s.duration}s</span></div>
    ${s.action.map((a) => `<div class="act">${esc(a)}</div>`).join('')}
    ${s.dialogue.map((d) => `<div class="dlg">${avatar(charById(d.speaker))}<div class="bubble"><small>${esc(charById(d.speaker)?.name || d.speaker)}${d.emotion ? ` · ${esc(d.emotion)}` : ''}</small><br>${esc(d.text)}</div></div>`).join('')}
    ${[...s.sfx.map((x) => '🔊 ' + x), ...s.music.map((x) => '🎵 ' + x)].map((x) => `<span class="sfx">${esc(x)}</span> `).join('')}
  </div></div>`).join('')}`;
}
function episodeBind(id) {
  document.querySelectorAll('[data-tab]').forEach((b) => (b.onclick = () => { epTab = b.dataset.tab; route(); }));
  document.querySelectorAll('[data-copy]').forEach((b) => (b.onclick = () => { navigator.clipboard?.writeText($('#pr' + b.dataset.copy).textContent); toast('Prompt copied'); }));
  $('#save-script')?.addEventListener('click', guard(async () => {
    await api('/episodes/' + id, { method: 'PUT', body: { script: $('#script').value, keepSample: true } });
    toast('Script saved'); epTab = 'scenes'; route();
  }));
  $('#del-ep').onclick = guard(async () => {
    if (!confirm('Delete this episode and its script?')) return;
    await api('/episodes/' + id, { method: 'DELETE' }); location.hash = '#/episodes';
  });
}

async function characters(id) {
  if (id) return characterDetail(charById(id));
  return `<h1>Character Library</h1><p class="sub">Single source of truth for look, personality and voice. Edit the appearance text to keep every prompt consistent.</p>
  <div class="grid g3">${CHARS.map((c) => `<a class="card hover" href="#/characters/${c.id}"><div class="row">${avatar(c, 'lg')}<div><h3>${esc(c.name)}</h3><span class="pill">${esc(c.role)}, ${esc(c.age)}</span><div style="color:var(--mut);margin-top:6px">${esc(c.tagline)}</div></div></div>
    <p style="color:var(--mut);font-size:14px">${esc(c.personality)}</p>
    <span class="pill ${c.referenceImages.length ? 'ok' : 'warn'}">${c.referenceImages.length} reference image(s)</span> <span class="pill ${c.voice.voiceId ? 'ok' : 'warn'}">${c.voice.voiceId ? 'voice assigned' : 'no voice yet'}</span></a>`).join('')}</div>`;
}
function characterDetail(c) {
  if (!c) return '<div class="err-box">Unknown character</div>';
  return `<a href="#/characters" style="color:var(--mut)">← Library</a>
  <div class="row" style="margin:8px 0 20px">${avatar(c, 'lg')}<div><h1>${esc(c.name)}</h1><p class="sub" style="margin:0">${esc(c.role)} · ${esc(c.tagline)}</p></div></div>
  <div class="grid g2">
   <div class="card"><h3>Profile</h3>
    <label>Personality</label><textarea id="c-personality" style="min-height:70px">${esc(c.personality)}</textarea>
    <label>Visual description (injected into every prompt)</label><textarea id="c-appearance">${esc(c.appearance)}</textarea>
    <label>Expressions (comma separated)</label><input id="c-expr" value="${esc(c.expressions.join(', '))}">
    <div class="row" style="margin-top:14px"><button class="btn pri" id="save-char">Save profile</button></div></div>
   <div class="card"><h3>Reference images</h3>
    <p class="sub" style="margin-bottom:10px">Upload approved reference art (PNG/JPEG/WEBP). The first image is used as the avatar.</p>
    <div class="thumbs">${c.referenceImages.map((i) => `<div class="thumb"><img src="${esc(i.url)}" alt=""><button class="btn sm danger" data-del="${esc(i.file)}">✕</button><small>${esc(i.label)}</small></div>`).join('') || '<div class="empty" style="width:100%">None yet</div>'}</div>
    <label>Label</label><input id="img-label" value="front view">
    <label>Image file</label><input type="file" id="img-file" accept="image/png,image/jpeg,image/webp">
    <div class="info-box" style="margin-top:12px">AI image generation for reference art / expression sheets is not connected: no image provider has been chosen. Use the prompts below in the tool of your choice and upload the result.</div></div>
  </div>
  <h2>Expression sheet prompts</h2>
  <div class="grid g3">${c.expressions.map((x) => `<div class="card"><div class="row spread"><b>${esc(x)}</b><button class="btn sm" data-cp="${esc(x)}">Copy</button></div><small style="color:var(--mut)">${esc(exprPrompt(c, x))}</small></div>`).join('')}</div>
  <h2>Voice profile</h2>
  <div class="card"><div class="grid g2"><div><label>Voice character</label><textarea id="v-desc" style="min-height:60px">${esc(c.voice.description)}</textarea></div>
   <div><label>ElevenLabs voice ID</label><input id="v-id" value="${esc(c.voice.voiceId)}" placeholder="from Voice Settings page">
    <label>Stability (${c.voice.stability})</label><input id="v-stab" type="number" min="0" max="1" step="0.05" value="${c.voice.stability}">
    <label>Similarity (${c.voice.similarity})</label><input id="v-sim" type="number" min="0" max="1" step="0.05" value="${c.voice.similarity}"></div></div>
   <button class="btn pri" id="save-voice" style="margin-top:14px">Save voice</button></div>`;
}
const exprPrompt = (c, x) => `Character expression sheet, ${c.name}: ${c.appearance}. Expression: ${x}. Stylised 3D animated family sitcom, neutral background, front and three-quarter view.`;
function charactersBind(id) {
  const c = charById(id); if (!c) return;
  const save = (body, msg) => guard(async () => { await api('/characters/' + id, { method: 'PUT', body }); await loadChars(); toast(msg); route(); });
  $('#save-char').onclick = save2(() => ({ personality: $('#c-personality').value, appearance: $('#c-appearance').value, expressions: $('#c-expr').value.split(',').map((s) => s.trim()).filter(Boolean) }), 'Profile saved');
  $('#save-voice').onclick = save2(() => ({ voice: { description: $('#v-desc').value, voiceId: $('#v-id').value.trim(), stability: Number($('#v-stab').value), similarity: Number($('#v-sim').value) } }), 'Voice saved');
  function save2(get, msg) { return () => save(get(), msg)(); }
  $('#img-file').onchange = guard(async (e) => {
    const f = e.target.files[0]; if (!f) return;
    await api(`/characters/${id}/references?label=${encodeURIComponent($('#img-label').value)}`, { method: 'POST', raw: f, type: f.type });
    await loadChars(); toast('Reference image stored'); route();
  });
  document.querySelectorAll('[data-del]').forEach((b) => (b.onclick = guard(async () => { await api(`/characters/${id}/references/${b.dataset.del}`, { method: 'DELETE' }); await loadChars(); route(); })));
  document.querySelectorAll('[data-cp]').forEach((b) => (b.onclick = () => { navigator.clipboard?.writeText(exprPrompt(c, b.dataset.cp)); toast('Prompt copied'); }));
}

async function voices() {
  const st = await api('/status');
  return `<h1>Voice Settings</h1><p class="sub">One consistent English voice per character, generated separately and synced to scenes (synthesis arrives in build step 4).</p>
  <div class="card"><table><tr><th></th><th>Character</th><th>Voice character</th><th>ElevenLabs voice</th></tr>
  ${CHARS.map((c) => `<tr><td>${avatar(c)}</td><td><a href="#/characters/${c.id}"><b>${esc(c.name)}</b></a></td><td style="color:var(--mut)">${esc(c.voice.description)}</td>
   <td><select data-voice="${c.id}"><option value="${esc(c.voice.voiceId)}">${c.voice.voiceId ? esc(c.voice.voiceId) : '— not assigned —'}</option></select></td></tr>`).join('')}</table>
  <div class="row" style="margin-top:14px"><button class="btn" id="load-voices" ${st.capabilities.elevenlabs.configured ? '' : 'disabled'}>Load my ElevenLabs voices</button>
  ${st.capabilities.elevenlabs.configured ? '' : '<span class="pill warn">Set ELEVENLABS_API_KEY in .env, then restart</span>'}<span id="v-msg"></span></div></div>`;
}
function voicesBind() {
  $('#load-voices').onclick = guard(async () => {
    const list = await api('/voices');
    document.querySelectorAll('[data-voice]').forEach((sel) => {
      const cur = charById(sel.dataset.voice).voice.voiceId;
      sel.innerHTML = `<option value="">— not assigned —</option>` + list.map((v) => `<option value="${esc(v.voiceId)}" ${v.voiceId === cur ? 'selected' : ''}>${esc(v.name)}</option>`).join('');
      sel.onchange = guard(async () => { await api('/characters/' + sel.dataset.voice, { method: 'PUT', body: { voice: { voiceId: sel.value } } }); await loadChars(); toast('Voice assigned'); });
    });
    toast(`${list.length} voices loaded`);
  });
}

async function settings() {
  const s = await api('/settings'); const r = s.rates;
  return `<h1>Costs &amp; Settings</h1><p class="sub">Provider prices change and depend on your plan, so none are built in. Enter your own rates to get estimates before anything is generated.</p>
  <div class="card" style="max-width:560px"><label>Currency</label><input id="s-cur" value="${esc(r.currency)}">
   <label>Video – price per generated second</label><input id="s-vid" type="number" step="any" min="0" value="${r.videoPerSecond ?? ''}" placeholder="not set">
   <label>Voice – price per 1,000 characters</label><input id="s-tts" type="number" step="any" min="0" value="${r.ttsPer1kChars ?? ''}" placeholder="not set">
   <label>Image – price per image</label><input id="s-img" type="number" step="any" min="0" value="${r.imagePerImage ?? ''}" placeholder="not set">
   <label>Retry allowance for failed clips (0.25 = +25%)</label><input id="s-retry" type="number" step="0.05" min="0" max="2" value="${s.retryAllowance}">
   <button class="btn pri" id="save-set" style="margin-top:16px">Save</button></div>`;
}
function settingsBind() {
  $('#save-set').onclick = guard(async () => {
    await api('/settings', { method: 'PUT', body: { retryAllowance: $('#s-retry').value, rates: { currency: $('#s-cur').value, videoPerSecond: $('#s-vid').value, ttsPer1kChars: $('#s-tts').value, imagePerImage: $('#s-img').value } } });
    toast('Settings saved');
  });
}

// ---------- router ----------
async function loadChars() { CHARS = await api('/characters'); }
async function route() {
  const [, page = '', arg] = location.hash.replace(/^#/, '').split('/');
  const name = page || 'dashboard';
  document.querySelectorAll('#nav a').forEach((a) => a.classList.toggle('on', a.dataset.r === name));
  const main = $('#main');
  try {
    if (!CHARS.length) await loadChars();
    if (name === 'dashboard') main.innerHTML = await dashboard();
    else if (name === 'episodes' && arg) { main.innerHTML = await episodeDetail(arg); episodeBind(arg); }
    else if (name === 'episodes') { main.innerHTML = await episodes(); episodesBind(); }
    else if (name === 'characters') { main.innerHTML = await characters(arg); if (arg) charactersBind(arg); }
    else if (name === 'voices') { main.innerHTML = await voices(); voicesBind(); }
    else if (name === 'settings') { main.innerHTML = await settings(); settingsBind(); }
    else main.innerHTML = '<div class="err-box">Page not found</div>';
    const st = await api('/status');
    $('#sidefoot').innerHTML = `<span>${st.capabilities.ffmpeg.available ? '🟢' : '🔴'} FFmpeg</span><span>${st.capabilities.elevenlabs.configured ? '🟢' : '⚪'} ElevenLabs</span><span>${st.capabilities.video.configured ? '🟢' : '⚪'} Video provider</span>`;
  } catch (e) { main.innerHTML = `<div class="err-box">${esc(e.message)}</div>`; }
}
addEventListener('hashchange', () => { epTab = 'scenes'; route(); });
route();
