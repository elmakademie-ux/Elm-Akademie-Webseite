import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CHARACTERS, CharacterId } from "../characters";
import { FONT_BLACK, FONT_BOLD } from "../fonts";

type Word = { text: string; start: number; end: number; hot?: boolean };
export type Line = { id: number; who: CharacterId; text: string; startFrame: number; endFrame: number; words: Word[] };

/** Große Untertitel, Wort für Wort mit der Stimme synchron; Name des Sprechers als Schild. */
export const Subtitles: React.FC<{ lines: Line[]; names?: Partial<Record<CharacterId, string>> }> = ({ lines, names }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const line = lines.find((l) => frame >= l.startFrame - 3 && frame < l.endFrame + 9);
  if (!line) return null;
  const def = CHARACTERS[line.who];
  const idx = Math.max(0, line.words.reduce((acc, w, i) => (frame + 1 >= w.start ? i : acc), 0));
  const word = line.words[idx];
  const pop = spring({ frame: frame - word.start, fps, config: { damping: 11, stiffness: 260, mass: 0.5 } });
  const fade = interpolate(frame, [line.startFrame - 3, line.startFrame, line.endFrame + 2, line.endFrame + 9], [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Schriftgröße: groß, aber das Wort muss immer in die Breite passen (Großbuchstaben sind breiter)
  const caps = word.text === word.text.toUpperCase() && /[A-ZÄÖÜ]/.test(word.text);
  const fit = 930 / (word.text.length * (caps ? 0.8 : 0.62));
  const size = Math.max(64, Math.min(176, 176 - (word.text.length - 6) * 6.5, fit));
  const stroke = Math.round(size * 0.11);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 470, opacity: fade }}>
      <div style={{ position: "absolute", top: 222, left: 0, width: 1080, display: "flex", justifyContent: "center" }}>
        <div style={{ background: def.color, color: "#fff", fontFamily: FONT_BOLD, fontSize: 40, letterSpacing: 2,
          padding: "8px 36px", borderRadius: 40, border: "5px solid #111", boxShadow: "0 6px 0 rgba(0,0,0,0.35)" }}>
          {names?.[line.who] ?? def.name}
        </div>
      </div>
      <div style={{ position: "absolute", top: 268, left: 0, width: 1080, height: 190, display: "flex",
        justifyContent: "center", alignItems: "center" }}>
        <div style={{ fontFamily: FONT_BLACK, fontSize: size, lineHeight: 1, color: word.hot ? "#ffd640" : def.textColor, whiteSpace: "nowrap",
          transform: `scale(${(word.hot ? 0.7 : 0.78) + (word.hot ? 0.4 : 0.22) * pop})`, WebkitTextStroke: `${stroke}px #0b0b10`, paintOrder: "stroke fill",
          textShadow: "0 8px 0 rgba(0,0,0,0.35)" }}>
          {word.text}
        </div>
      </div>
    </div>
  );
};
