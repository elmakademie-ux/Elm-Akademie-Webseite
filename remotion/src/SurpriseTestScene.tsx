import React from "react";
import { AbsoluteFill, Audio, Easing, Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import "./fonts";
import { FONT_BOLD } from "./fonts";
import { getPose } from "./characters";
import { TeacherF } from "./components/Character";
import { Subtitles } from "./components/Subtitles";
import timeline from "./timelines/surprise-test.json";

const T = timeline;
const OVERLAP = 8;

/** Weichgezeichneter Hintergrund aus demselben Szenenbild + Abdunkelung oben/unten. */
const Backdrop: React.FC<{ image: string }> = ({ image }) => (
  <>
    <Img src={staticFile(image)} style={{ position: "absolute", inset: 0, width: 1080, height: 1920, objectFit: "cover",
      filter: "blur(36px) saturate(1.25) brightness(0.8)", transform: "scale(1.3)" }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(8,16,36,0.55) 0%, rgba(8,16,36,0.05) 38%, rgba(8,16,36,0.05) 70%, rgba(8,16,36,0.5) 100%)" }} />
  </>
);

/** Eine Einstellung der Lehrerin (Pose aus dem Storyboard) mit Kamerafahrt; Sprechen steuert Mund und Wippen. */
const Shot: React.FC<{ pose: string; start: number; end: number; enter: "whip" | "fade" | "none"; speaking?: boolean }> =
  ({ pose, start, end, enter, speaking }) => {
    const local = useCurrentFrame();
    const { fps } = useVideoConfig();
    const abs = start + local;
    const p = getPose("teacher_f", pose);
    const talk = speaking && abs >= T.voiceStart && abs <= T.voiceEnd ? T.env[abs - T.voiceStart] ?? 0 : 0;
    // Betonung bei "SURPRISE TEST": kurzer Zoom-Punch und leichtes Wackeln
    const since = abs - T.hotFrame;
    const amt = speaking && since >= 0 && since < 20 ? Math.exp(-since / 5) : 0;
    const pop = enter === "whip" ? spring({ frame: local, fps, config: { damping: 14, stiffness: 180, mass: 0.8 } }) : 1;
    const fade = enter === "fade" ? interpolate(local, [0, OVERLAP], [0, 1], { extrapolateRight: "clamp" })
      : enter === "whip" ? interpolate(local, [0, 4], [0, 1], { extrapolateRight: "clamp" }) : 1;
    return (
      <AbsoluteFill style={{ opacity: fade, transform: `translate(${Math.sin(abs * 2.3) * 11 * amt}px, ${Math.cos(abs * 3.1) * 6 * amt}px) scale(${1 + 0.1 * amt + 0.12 * (1 - pop)})` }}>
        <Backdrop image={p.image} />
        <TeacherF pose={pose} talk={talk} frame={local} duration={end - start + OVERLAP} />
      </AbsoluteFill>
    );
  };

/** Weiße Schlaglinien um das Gesicht, wenn "SURPRISE TEST" fällt. */
const ImpactLines: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const since = frame - T.hotFrame;
  if (since < 0 || since > 14) return null;
  const s = spring({ frame: since, fps, config: { damping: 10, stiffness: 260, mass: 0.6 } });
  const a = interpolate(since, [0, 4, 14], [0, 1, 0], { extrapolateRight: "clamp" });
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: a }}>
      {Array.from({ length: 12 }).map((_, i) => {
        const ang = (i / 12) * Math.PI * 2 + 0.2;
        const r0 = 390 + 40 * s, r1 = r0 + 70 + 30 * (i % 3);
        const cx = 540, cy = 960;
        const l = { x1: cx + Math.cos(ang) * r0, y1: cy + Math.sin(ang) * r0 * 0.95, x2: cx + Math.cos(ang) * r1, y2: cy + Math.sin(ang) * r1 * 0.95 };
        return (
          <g key={i}>
            <line {...l} stroke="#0b0b10" strokeWidth={22} strokeLinecap="round" />
            <line {...l} stroke="#ffffff" strokeWidth={11} strokeLinecap="round" />
          </g>
        );
      })}
    </svg>
  );
};

/**
 * Szene 1 – "The Surprise Test" (ca. 4,8 s, 1080 x 1920, 30 fps).
 * Vorher: Lehrerin mit gehobener Augenbraue, Blick durch die Klasse (langsamer Zoom).
 * Sprechen: Nahaufnahme, Lippenbewegung nach der Stimme, "SURPRISE TEST" betont (Zoom-Punch, Effekt).
 * Danach: Arme verschränkt, strenger Blick, Pose halten.
 */
export const SurpriseTestScene: React.FC = () => {
  const frame = useCurrentFrame();
  const subtitleLine = { id: 1, who: "teacher_f" as const, text: "Today, we're having a surprise test!",
    startFrame: T.voiceStart, endFrame: T.voiceEnd, words: T.words };
  return (
    <AbsoluteFill style={{ background: "#0b1224", fontFamily: FONT_BOLD }}>
      <Sequence from={0} durationInFrames={T.cut1 + OVERLAP}>
        <Shot pose="thinking" start={0} end={T.cut1} enter="none" />
      </Sequence>
      <Sequence from={T.cut1} durationInFrames={T.cut2 - T.cut1 + OVERLAP}>
        <Shot pose="pointing" start={T.cut1} end={T.cut2} enter="whip" speaking />
      </Sequence>
      <Sequence from={T.cut2} durationInFrames={T.totalFrames - T.cut2}>
        <Shot pose="arms_crossed" start={T.cut2} end={T.totalFrames} enter="fade" />
      </Sequence>
      <ImpactLines />
      <Subtitles lines={[subtitleLine]} />
      {/* Ton: Klassenzimmer-Atmosphäre, Stimme, Effekte */}
      <Audio src={staticFile(T.ambience)} volume={(f) => 0.22 * interpolate(f, [0, 12, T.totalFrames - 15, T.totalFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
      <Sequence from={T.voiceStart} layout="none">
        <Audio src={staticFile(T.voice)} volume={0.9} />
      </Sequence>
      {T.sfx.map((s, i) => (
        <Sequence key={i} from={Math.max(0, s.frame)} layout="none">
          <Audio src={staticFile(s.file)} volume={s.volume} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
