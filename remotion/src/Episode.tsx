import React from "react";
import { AbsoluteFill, Audio, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import "./fonts";
import { FONT_BOLD } from "./fonts";
import { CharacterId, getPose } from "./characters";
import { Student, Teacher } from "./components/Character";
import { Header } from "./components/Header";
import { Outro } from "./components/Outro";
import { Line, Subtitles } from "./components/Subtitles";
import { EPISODES } from "./episodes";

type Shot = { pose: string; who: CharacterId; startFrame: number; endFrame: number };
export type Timeline = {
  totalFrames: number; reactionFrame: number; outroFrame: number; lines: (Line & { env: number[]; audio: string; pose: string })[];
  shots: Shot[]; sfx: { file: string; frame: number; volume: number }[];
  stickers: { text: string; x: number; y: number; color: string; delay: number }[];
};
const Ctx = React.createContext<Timeline>(null as unknown as Timeline);
const OVERLAP = 9;                     // Frames, in denen der nächste Schnitt über den vorigen blendet
const TRANSITIONS = ["zoom", "slide", "fade", "whip"] as const;

const Shot: React.FC<{ shot: Shot; index: number }> = ({ shot, index }) => {
  const T = React.useContext(Ctx);
  const local = useCurrentFrame();
  const abs = shot.startFrame + local;
  const duration = shot.endFrame - shot.startFrame + OVERLAP;
  const line = T.lines.find((l) => abs >= l.startFrame && abs <= l.endFrame);
  const talk = line && line.who === shot.who ? line.env[abs - line.startFrame] ?? 0 : 0;
  const pose = getPose(shot.who, shot.pose);
  const View = shot.who === "teacher" ? Teacher : Student;
  const type = TRANSITIONS[index % TRANSITIONS.length];
  const e = (a: number, b: number, from: number, to: number) =>
    interpolate(local, [a, b], [from, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  let style: React.CSSProperties = {};
  if (index > 0) {
    if (type === "zoom") style = { opacity: e(0, 8, 0, 1), transform: `scale(${e(0, 9, 1.18, 1)})` };
    if (type === "slide") style = { transform: `translateX(${e(0, 9, 1080, 0)}px)`, filter: `blur(${e(0, 9, 10, 0)}px)` };
    if (type === "fade") style = { opacity: e(0, 8, 0, 1) };
    if (type === "whip") style = { opacity: e(0, 5, 0, 1), transform: `translateY(${e(0, 9, 160, 0)}px)`, filter: `blur(${e(0, 9, 14, 0)}px)` };
  }
  return (
    <AbsoluteFill style={style}>
      {/* weichgezeichneter Hintergrund aus demselben Szenenbild */}
      <Img src={staticFile(pose.image)} style={{ position: "absolute", inset: 0, width: 1080, height: 1920, objectFit: "cover",
        filter: "blur(36px) saturate(1.25) brightness(0.8)", transform: "scale(1.3)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(8,16,36,0.55) 0%, rgba(8,16,36,0.05) 38%, rgba(8,16,36,0.05) 70%, rgba(8,16,36,0.5) 100%)" }} />
      <View pose={shot.pose} talk={talk} frame={local} duration={duration} />
    </AbsoluteFill>
  );
};

const Stickers: React.FC = () => {
  const T = React.useContext(Ctx);
  const frame = useCurrentFrame();
  return (
    <>
      {T.stickers.map((s, i) => {
        const f = frame - T.reactionFrame - Math.round(s.delay * 30);
        if (f < 0 || frame >= T.outroFrame) return null;
        const pop = interpolate(f, [0, 6, 10], [0.3, 1.2, 1], { extrapolateRight: "clamp" });
        return (
          <div key={i} style={{ position: "absolute", left: s.x * 1080 - 200, top: 470 + s.y * 1080, width: 400, textAlign: "center",
            fontFamily: "InterBlack, Inter, sans-serif", fontSize: 92, color: s.color, WebkitTextStroke: "10px #0b0b10",
            paintOrder: "stroke fill", transform: `scale(${pop}) rotate(${Math.sin(f / 4) * 3 - 4}deg)`, opacity: Math.min(1, f / 4) }}>
            {s.text}
          </div>
        );
      })}
    </>
  );
};

const musicVolume = (T: Timeline) => (f: number) => {
  let duck = 1;
  for (const l of T.lines) {
    duck = Math.min(duck, interpolate(f, [l.startFrame - 6, l.startFrame, l.endFrame, l.endFrame + 8], [1, 0.4, 0.4, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  }
  const fade = interpolate(f, [0, 24, T.totalFrames - 40, T.totalFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return 0.14 * duck * fade;
};

export const Episode: React.FC<{ id: string }> = ({ id }) => {
  const { episode, timeline: T } = EPISODES[id];
  return (
    <Ctx.Provider value={T}>
      <AbsoluteFill style={{ background: "#0b1224", fontFamily: FONT_BOLD }}>
        {T.shots.map((s, i) => (
          <Sequence key={i} from={s.startFrame} durationInFrames={s.endFrame - s.startFrame + (i < T.shots.length - 1 ? OVERLAP : 0)}>
            <Shot shot={s} index={i} />
          </Sequence>
        ))}
        <Stickers />
        <Header badge={episode.badge} />
        <Subtitles lines={T.lines} names={(episode as { names?: Partial<Record<CharacterId, string>> }).names} />
        <Outro from={T.outroFrame} title={episode.title} cta={(episode as { cta?: string }).cta} />
        {/* Ton */}
        <Audio src={staticFile(`assets/audio/${id}/music.wav`)} volume={musicVolume(T)} />
        {T.lines.map((l) => (
          <Sequence key={l.id} from={l.startFrame} layout="none">
            <Audio src={staticFile(l.audio)} volume={0.85} />
          </Sequence>
        ))}
        {T.sfx.map((s, i) => (
          <Sequence key={`sfx${i}`} from={Math.max(0, s.frame)} layout="none">
            <Audio src={staticFile(s.file)} volume={s.volume * 0.5} />
          </Sequence>
        ))}
      </AbsoluteFill>
    </Ctx.Provider>
  );
};
