import React from "react";
import { Img, staticFile } from "remotion";
import { FONT_BOLD } from "../fonts";

/** ELM-Logo oben links (liegt unterhalb der Plattform-Leiste) und Folgen-Abzeichen oben rechts. */
export const Header: React.FC<{ badge: string }> = ({ badge }) => (
  <>
    <div style={{ position: "absolute", left: 30, top: 70, width: 290, background: "#fff", borderRadius: 26, padding: 12,
      boxShadow: "0 8px 22px rgba(10,20,40,0.35)" }}>
      <Img src={staticFile("assets/logo.png")} style={{ width: "100%", display: "block", borderRadius: 18 }} />
    </div>
    <div style={{ position: "absolute", right: 36, top: 116, background: "#ed8c14", color: "#fff", fontFamily: FONT_BOLD,
      fontSize: 42, padding: "12px 34px", borderRadius: 44, border: "5px solid #111" }}>{badge}</div>
  </>
);
