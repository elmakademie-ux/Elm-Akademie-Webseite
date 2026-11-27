import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import "../fonts";
import { FONT_BLACK } from "../fonts";
import timeline from "../timelines/tiktok-3-dinge.json";
import { Scene1, Scene2, Scene3, Scene4, Scene5, SceneProps } from "./Scenes";

type Word = { text: string; start: number; end: number; hot: boolean };
const T = timeline as unknown as {
  totalFrames: number; music: string;
  scenes: { id: number; startFrame: number; endFrame: number; lines: { relStart: number; relEnd: number }[] }[];
  lines: { id: number; startFrame: number; endFrame: number; audio: string; words: Word[] }[];
  sfx: { file: string; frame: number; volume: number }[];
};
export const TIKTOK_FRAMES = T.totalFrames;
const SCENES: Record<number, React.FC<SceneProps>> = { 1: Scene1, 2: Scene2, 3: Scene3, 4: Scene4, 5: Scene5 };

/** Große TikTok-Untertitel: Wort für Wort, wichtige Wörter gelb. Liegen über der unteren TikTok-Leiste (y 1130-1330). */
const Subtitles: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const line = T.lines.find((l) => frame >= l.startFrame - 2 && frame < l.endFrame + 8);
  if (!line) return null;
  const idx = Math.max(0, line.words.reduce((a, w, i) => (frame + 1 >= w.start ? i : a), 0));
  const w = line.words[idx];
  const pop = spring({ frame: frame - w.start, fps, config: { damping: 10, stiffness: 280, mass: 0.5 } });
  const fade = interpolate(frame, [line.endFrame, line.endFrame + 8], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const size = Math.max(70, Math.min(150, 880 / (w.text.length * 0.6)));
  return (
    <div style={{ position: "absolute", left: 0, top: 1130, width: 940, height: 200, display: "flex", justifyContent: "center", alignItems: "center", opacity: fade }}>
      <div style={{ fontFamily: FONT_BLACK, fontSize: size, lineHeight: 1, whiteSpace: "nowrap", color: w.hot ? "#ffd23f" : "#fff",
        WebkitTextStroke: `${Math.round(size * 0.11)}px #0b0b10`, paintOrder: "stroke fill", textShadow: "0 8px 0 rgba(0,0,0,0.4)",
        transform: `scale(${(w.hot ? 0.75 : 0.82) + (w.hot ? 0.35 : 0.2) * pop}) rotate(${w.hot ? (idx % 2 ? 2 : -2) : 0}deg)` }}>
        {w.text}
      </div>
    </div>
  );
};

/** Szenenübergang: kurzer Zoom und weißer Blitz. */
const SceneFrame: React.FC<{ first: boolean; children: React.ReactNode }> = ({ first, children }) => {
  const f = useCurrentFrame();
  const s = first ? 1 : interpolate(f, [0, 7], [1.08, 1], { extrapolateRight: "clamp" });
  const flash = first ? 0 : interpolate(f, [0, 5], [0.6, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ transform: `scale(${s})` }}>
      {children}
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </AbsoluteFill>
  );
};

const musicVolume = (f: number) => {
  let duck = 1;
  for (const l of T.lines) duck = Math.min(duck, interpolate(f, [l.startFrame - 4, l.startFrame, l.endFrame, l.endFrame + 8], [1, 0.32, 0.32, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return 0.42 * duck * interpolate(f, [T.totalFrames - 12, T.totalFrames], [1, 0.3], { extrapolateLeft: "clamp" });
};

export const TikTokVideo: React.FC = () => (
  <AbsoluteFill style={{ background: "#05081c" }}>
    {T.scenes.map((s, i) => {
      const Scene = SCENES[s.id];
      return (
        <Sequence key={s.id} from={s.startFrame} durationInFrames={s.endFrame - s.startFrame}>
          <SceneFrame first={i === 0}><Scene lines={s.lines} duration={s.endFrame - s.startFrame} /></SceneFrame>
        </Sequence>
      );
    })}
    <Subtitles />
    <Audio src={staticFile(T.music)} volume={musicVolume} />
    {T.lines.map((l) => (
      <Sequence key={l.id} from={l.startFrame} layout="none"><Audio src={staticFile(l.audio)} volume={1} /></Sequence>
    ))}
    {T.sfx.map((s, i) => (
      <Sequence key={i} from={Math.max(0, s.frame)} layout="none"><Audio src={staticFile(s.file)} volume={s.volume * 0.6} /></Sequence>
    ))}
  </AbsoluteFill>
);
