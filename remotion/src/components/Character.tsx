import React from "react";
import { Img, interpolate, staticFile, Easing } from "remotion";
import { CharacterId, getPose } from "../characters";

export const BAND = { y: 470, w: 1080, h: 1080 };

export type CharacterProps = {
  pose: string;
  /** Lautstärke der Stimme 0..1 (steuert das Mitwippen beim Sprechen) */
  talk?: number;
  /** Bildfortschritt in dieser Einstellung und ihre Länge (für Zoom und Fahrt) */
  frame: number;
  duration: number;
};

/**
 * Zeigt eine Figur in einer Pose aus dem Storyboard mit Kamerafahrt und Sprech-Wippen.
 * Verwendet ausschließlich die Referenzbilder (keine neuen Figurenbilder).
 */
export const CharacterView: React.FC<CharacterProps & { character: CharacterId }> = ({
  character, pose, talk = 0, frame, duration,
}) => {
  const p = getPose(character, pose);
  const t = interpolate(frame, [0, Math.max(1, duration)], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const scale = p.zoom[0] + (p.zoom[1] - p.zoom[0]) * t;
  const [d0, d1] = p.drift ?? [{ x: 0, y: 0 }, { x: 0, y: 0 }];
  const dx = d0.x + (d1.x - d0.x) * t;
  const dy = d0.y + (d1.y - d0.y) * t;
  const bob = 1 + 0.016 * talk;
  const lift = -7 * talk;
  const tilt = Math.sin(frame / 2.2) * 0.5 * talk;
  return (
    <div style={{ position: "absolute", left: 0, top: BAND.y, width: BAND.w, height: BAND.h, overflow: "hidden",
      borderRadius: 40, boxShadow: "0 24px 60px rgba(10,20,40,0.45)" }}>
      <div style={{ width: "100%", height: "100%",
        transformOrigin: `${p.focus.x * 100}% ${p.focus.y * 100}%`,
        transform: `translate(${dx}px, ${dy + lift}px) scale(${scale * bob}) rotate(${tilt}deg)` }}>
        <Img src={staticFile(p.image)} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
      </div>
    </div>
  );
};

export const Teacher: React.FC<CharacterProps> = (props) => <CharacterView character="teacher" {...props} />;
export const Student: React.FC<CharacterProps> = (props) => <CharacterView character="student" {...props} />;
