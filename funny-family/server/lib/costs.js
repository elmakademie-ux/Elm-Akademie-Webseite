// Cost estimation. The studio never hard-codes provider prices (they change and
// differ per plan). You enter your own rates in Settings; until then only the
// quantities (seconds, characters, clips) are shown.
export const DEFAULT_SETTINGS = {
  rates: { videoPerSecond: null, ttsPer1kChars: null, imagePerImage: null, currency: 'USD' },
  retryAllowance: 0.25, // extra share budgeted for failed / regenerated clips
  seasons: { 1: 'Season 1' },
};

export function estimateEpisode(episode, settings = DEFAULT_SETTINGS) {
  const r = settings.rates || {};
  const seconds = episode.scenes.reduce((n, s) => n + s.duration, 0);
  const chars = episode.scenes.reduce((n, s) => n + s.dialogue.reduce((m, d) => m + d.text.length, 0), 0);
  const clips = episode.scenes.length;
  const retry = settings.retryAllowance ?? 0;
  const money = (rate, qty) => (typeof rate === 'number' ? +(rate * qty).toFixed(2) : null);
  const video = money(r.videoPerSecond, seconds);
  const tts = money(r.ttsPer1kChars, chars / 1000);
  const known = [video, tts].filter((v) => v !== null);
  const base = known.reduce((a, b) => a + b, 0);
  return {
    quantities: { clips, videoSeconds: seconds, dialogueCharacters: chars },
    lines: [
      { item: 'Video clips', qty: `${seconds}s in ${clips} clips`, cost: video },
      { item: 'Voice (ElevenLabs)', qty: `${chars} characters`, cost: tts },
    ],
    currency: r.currency || 'USD',
    subtotal: known.length ? +base.toFixed(2) : null,
    withRetryAllowance: known.length ? +(base + (video ?? 0) * retry).toFixed(2) : null,
    complete: video !== null && tts !== null,
    note: known.length === 0
      ? 'No rates set. Enter your provider rates in Settings to see a cost estimate.'
      : 'Estimate based on the rates you entered; actual provider billing may differ.',
  };
}
