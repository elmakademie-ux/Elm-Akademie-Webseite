import test from 'node:test';
import assert from 'node:assert/strict';
import { parseEpisodes } from '../server/lib/scriptParser.js';
import { DEFAULT_CHARACTERS } from '../server/lib/characters.js';
import { estimateEpisode } from '../server/lib/costs.js';
import { buildEpisodePrompts } from '../server/lib/promptBuilder.js';

const txt = `# Episode 7: Test
season: 2
## Scene 1 | Kitchen | 10s
Bob stirs soup.
BOB (sleepy): Soup.
GRANDMA ROSE: More salt!
SFX: splash
MUSIC: jazz
ZED: who?
## Scene 2 | Garden
LUCY: Hi.
`;
test('parses episode, scenes, speakers, sfx', () => {
  const [ep] = parseEpisodes(txt, DEFAULT_CHARACTERS);
  assert.equal(ep.id, 's02e07'); assert.equal(ep.scenes.length, 2);
  assert.deepEqual(ep.scenes[0].dialogue.map((d) => d.speaker), ['bob', 'rose']);
  assert.equal(ep.scenes[0].dialogue[0].emotion, 'sleepy');
  assert.deepEqual(ep.scenes[0].sfx, ['splash']); assert.deepEqual(ep.scenes[0].music, ['jazz']);
  assert.ok(ep.warnings.some((w) => w.includes('ZED')));
  assert.equal(ep.scenes[1].durationEstimated, true);
});
test('splits multiple episodes', () => {
  assert.equal(parseEpisodes('# Episode 1: A\n## S\nBOB: x\n# Episode 2: B\n## S\nLUCY: y\n', DEFAULT_CHARACTERS).length, 2);
});
test('cost estimate never invents prices', () => {
  const [ep] = parseEpisodes(txt, DEFAULT_CHARACTERS);
  assert.equal(estimateEpisode(ep).subtotal, null);
  const e = estimateEpisode(ep, { rates: { videoPerSecond: 1, ttsPer1kChars: 0 }, retryAllowance: 0.5 });
  assert.equal(e.subtotal, ep.totalDuration); assert.equal(e.withRetryAllowance, ep.totalDuration * 1.5);
});
test('prompts include character appearance', () => {
  const [ep] = parseEpisodes(txt, DEFAULT_CHARACTERS);
  assert.match(buildEpisodePrompts(ep, DEFAULT_CHARACTERS)[0].prompt, /round friendly face/);
});
