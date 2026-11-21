# The Funny Family – AI Video Production Studio

```bash
cd funny-family
cp .env.example .env     # add keys when you have them
npm start                # http://localhost:4310
npm test
```

Implemented (step 1): dashboard, episode manager (import/edit scripts, seasons, scenes, timeline), character library (profiles, reference-image upload, expression prompts, voice profiles), video prompt builder, cost estimator, ElevenLabs voice list.
Not yet implemented: video generation, voice synthesis, FFmpeg render — see `ARCHITECTURE.md`.

Importing your 30 scripts: Episodes → Import scripts (format shown there). The two included episodes are samples.
