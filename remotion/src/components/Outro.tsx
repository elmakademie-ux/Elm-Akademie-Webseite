import React from "react";
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT_BLACK, FONT_BOLD } from "../fonts";

/** Abspann: Logo, Titel, Aufforderung zum Folgen. */
export const Outro: React.FC<{ from: number; title: string; cta?: string }> = ({ from, title, cta: ctaText = "Folge der ELM Akademie" }) => {
  const frame = useCurrentFrame() - from;
  const { fps } = useVideoConfig();
  if (frame < 0) return null;
  const veil = interpolate(frame, [0, 10], [0, 0.96], { extrapolateRight: "clamp" });
  const logo = spring({ frame, fps, config: { damping: 12, stiffness: 140 } });
  const cta = spring({ frame: frame - 14, fps, config: { damping: 11, stiffness: 160 } });
  return (
    <div style={{ position: "absolute", inset: 0, background: `rgba(255,255,255,${veil})` }}>
      <div style={{ position: "absolute", left: 270, top: 560, width: 540, background: "#fff", borderRadius: 44, padding: 22,
        boxShadow: "0 20px 60px rgba(10,20,40,0.25)", transform: `scale(${0.8 + 0.2 * logo})`, opacity: Math.min(1, logo * 1.4) }}>
        <Img src={staticFile("assets/logo.png")} style={{ width: "100%", display: "block", borderRadius: 30 }} />
      </div>
      <div style={{ position: "absolute", top: 1000, width: 1080, textAlign: "center", fontFamily: FONT_BLACK, fontSize: 84,
        color: "#1b3668", opacity: interpolate(frame, [8, 20], [0, 1], { extrapolateRight: "clamp" }) }}>{title}</div>
      <div style={{ position: "absolute", top: 1160, width: 1080, display: "flex", justifyContent: "center",
        transform: `scale(${Math.max(0.01, cta)})` }}>
        <div style={{ background: "#ed8c14", color: "#fff", fontFamily: FONT_BOLD, fontSize: 56, padding: "24px 56px", borderRadius: 70 }}>
          {ctaText}
        </div>
      </div>
    </div>
  );
};
