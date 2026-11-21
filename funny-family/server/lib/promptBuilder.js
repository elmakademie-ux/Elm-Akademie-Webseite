// Turns a parsed scene into a detailed text-to-video prompt using the character bible.
import { STYLE_BIBLE } from './characters.js';

export const NEGATIVE =
  'text overlays, watermark, subtitles burned into the image, extra fingers, deformed faces, ' +
  'inconsistent outfits, photorealistic humans, horizontal framing';

export function buildScenePrompt(scene, characters, episode) {
  const byId = new Map(characters.map((c) => [c.id, c]));
  const present = [...new Set(scene.dialogue.map((d) => d.speaker))];
  const mentioned = characters.filter((c) => scene.action.join(' ').toLowerCase().includes(c.name.toLowerCase().split(' ').pop()));
  for (const c of mentioned) if (!present.includes(c.id)) present.push(c.id);

  const cast = present.map((id) => byId.get(id)).filter(Boolean)
    .map((c) => `${c.name} (${c.appearance})`).join('; ');
  const action = scene.action.join(' ');
  const speaking = scene.dialogue.map((d) => {
    const c = byId.get(d.speaker);
    return `${c?.name ?? d.speaker}${d.emotion ? ` (${d.emotion})` : ''} says: "${d.text}"`;
  }).join(' ');

  const prompt = [
    STYLE_BIBLE + '.',
    scene.location ? `Setting: ${scene.location}.` : '',
    cast ? `Characters: ${cast}.` : '',
    action ? `Action: ${action}` : '',
    speaking ? `Dialogue (animate mouths and gestures to match; audio is added separately): ${speaking}` : '',
    `Duration about ${scene.duration} seconds. Comedic timing, clear staging, locked-off or gently moving camera.`,
  ].filter(Boolean).join(' ');

  return {
    scene: scene.number, duration: scene.duration, prompt, negative: NEGATIVE,
    referenceCharacters: present, episode: episode?.id,
  };
}

export function buildEpisodePrompts(episode, characters) {
  return episode.scenes.map((s) => buildScenePrompt(s, characters, episode));
}
