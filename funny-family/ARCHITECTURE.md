# Architecture – The Funny Family Studio

## Environment findings
- Node 22, Python 3.13, FFmpeg 6.1 available. No API keys configured.
- The surrounding repo contains unrelated German learning videos, so the studio lives in its own `funny-family/` folder.

## Decisions
| Choice | Why |
|---|---|
| Node 22 server, **zero npm dependencies** | Runs anywhere, nothing to install or audit. Built-in `fetch`, `node:test`. |
| Vanilla JS dashboard, no build step | Simple, fast, easy to maintain. |
| JSON files in `data/` (gitignored) | Human-readable, atomic writes; enough for 30 episodes. Swappable behind `store.js`. |
| Plain-text script format | Easy to write, diff and import in bulk; raw text is the source of truth, scenes are derived. |

## Pipeline
```
Script (.md) ─parse─▶ Scenes ─promptBuilder─▶ Video prompts ─[approval + cost]─▶ Provider adapter ─▶ clips/
                          └──▶ Dialogue ─[approval]─▶ ElevenLabs ─▶ voice/
clips + voice + sfx/music ─▶ FFmpeg (9:16, subtitles, 1080×1920) ─▶ output/<ep>/final.mp4
```
Stage status on the dashboard is derived from **files that really exist** in `data/output/<episode>/{clips,voice,final.mp4}` – never from a flag.

## Modules (`server/lib`)
- `config.js` – .env loading, capability report (never returns key values)
- `store.js` – JSON persistence
- `characters.js` – character bible + style bible (editable, saved to `data/characters`)
- `scriptParser.js` – script → episodes/scenes/dialogue/sfx/music, duration estimate, warnings
- `promptBuilder.js` – scene → detailed video prompt using character appearance
- `costs.js` – estimates from **user-entered rates only** (no invented prices)

## Safety rules
- Keys only via environment variables; the browser never sees them.
- No paid call exists in code yet. Future generation jobs must: show estimate → require explicit approval → record result → mark failed scenes for regeneration.
- Only real endpoints: currently just ElevenLabs `GET /v1/voices` (untested without a key).

## Roadmap
1. ✅ Dashboard, character library, episode manager, prompts, cost estimator
2. Video provider adapter (**needs your choice of provider**; implement only its documented API) + approval-gated job queue + per-scene regenerate
3. ElevenLabs dialogue synthesis per line (text-to-speech endpoint), timing from real audio length
4. FFmpeg assembly: clip normalisation to 1080×1920, voice/SFX/music mix, ASS/SRT subtitles, transitions, final MP4 + progress reporting
