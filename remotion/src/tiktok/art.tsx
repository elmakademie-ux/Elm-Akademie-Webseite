import React from "react";
import { useCurrentFrame } from "remotion";

export const C = {
  navy: "#0f1b3d", ink: "#080e22", teal: "#17b8a6", yellow: "#ffd23f", orange: "#ff7a45", pink: "#ff4d8d",
  white: "#ffffff", skin: "#c68e63", skinDark: "#a2704a", hair: "#17110f", hoodie: "#ff6b4a", hoodieDark: "#e5502f",
  jeans: "#2c3e6b", red: "#ff3b30", green: "#2ee66b",
};

export type Expr = "neutral" | "wow" | "confused" | "wait" | "happy" | "smirk";

/** Illustrierter Sprecher (Büste, optional ganzer Körper). Neutraler Flat-Look, bewusst ohne Klischees. */
export const Person: React.FC<{
  x: number; y: number; s?: number; expr?: Expr; look?: [number, number]; tilt?: number; bob?: number; full?: boolean; crossed?: boolean;
}> = ({ x, y, s = 1, expr = "neutral", look = [0, 0], tilt = 0, bob = 0, full = false, crossed = false }) => {
  const f = useCurrentFrame();
  const blink = f % 100 < 4;
  const ey = expr === "wow" ? 34 : blink ? 3 : 28;
  const brows: Record<Expr, [number, number, number, number]> = {   // [yLinks, yRechts, winkelLinks, winkelRechts]
    neutral: [-78, -78, 0, 0], wow: [-104, -104, -6, 6], confused: [-100, -72, -10, 14], wait: [-78, -78, 10, -10],
    happy: [-86, -86, -6, 6], smirk: [-94, -78, -6, 0],
  };
  const [bl, br, al, ar] = brows[expr];
  const mouth = {
    neutral: <path d="M-32,82 L32,82" stroke="#5a2d1c" strokeWidth={9} strokeLinecap="round" />,
    wow: <ellipse cx={0} cy={92} rx={24} ry={32} fill="#4a1a14" />,
    confused: <path d="M-40,88 Q-20,70 0,88 T40,88" stroke="#5a2d1c" strokeWidth={9} fill="none" strokeLinecap="round" />,
    wait: <path d="M-26,86 L34,80" stroke="#5a2d1c" strokeWidth={9} strokeLinecap="round" />,
    happy: <g><path d="M-52,66 Q0,134 52,66 Z" fill="#4a1a14" /><path d="M-40,70 Q0,92 40,70 L36,78 Q0,94 -36,78 Z" fill="#fff" /></g>,
    smirk: <path d="M-36,84 Q10,96 44,64" stroke="#5a2d1c" strokeWidth={9} fill="none" strokeLinecap="round" />,
  }[expr];
  const [lx, ly] = look;
  return (
    <g transform={`translate(${x},${y + bob}) rotate(${tilt}) scale(${s})`}>
      {full && (
        <g>
          <rect x={-150} y={640} width={130} height={470} rx={46} fill={C.jeans} />
          <rect x={20} y={640} width={130} height={470} rx={46} fill={C.jeans} />
          <ellipse cx={-98} cy={1128} rx={92} ry={36} fill="#fff" stroke="#0b1020" strokeWidth={8} />
          <ellipse cx={98} cy={1128} rx={92} ry={36} fill="#fff" stroke="#0b1020" strokeWidth={8} />
          <path d="M-232,330 C-222,215 -120,185 0,185 C120,185 222,215 232,330 L222,700 L-222,700 Z" fill={C.hoodie} />
        </g>
      )}
      <path d="M-232,330 C-222,215 -120,185 0,185 C120,185 222,215 232,330 L252,520 L-252,520 Z" fill={C.hoodie} />
      <path d="M-98,190 C-60,270 60,270 98,190 C70,170 -70,170 -98,190 Z" fill={C.hoodieDark} />
      <rect x={-46} y={96} width={92} height={110} rx={32} fill={C.skinDark} />
      {crossed && (
        <g>
          <rect x={-210} y={400} width={420} height={96} rx={48} fill="#ff8a6e" stroke={C.hoodieDark} strokeWidth={6} />
          <circle cx={-170} cy={448} r={40} fill={C.skin} /><circle cx={170} cy={448} r={40} fill={C.skin} />
        </g>
      )}
      <ellipse cx={-122} cy={10} rx={22} ry={34} fill={C.skinDark} /><ellipse cx={122} cy={10} rx={22} ry={34} fill={C.skinDark} />
      <ellipse cx={0} cy={0} rx={122} ry={140} fill={C.skin} />
      <path d="M-104,40 C-88,150 88,150 104,40 C70,98 -70,98 -104,40 Z" fill={C.hair} opacity={0.22} />
      <path d="M-128,-6 C-140,-152 -60,-172 0,-172 C70,-172 140,-152 128,-6 C102,-80 62,-106 0,-102 C-62,-106 -102,-80 -128,-6 Z" fill={C.hair} />
      <ellipse cx={-48} cy={-6} rx={25} ry={ey} fill="#fff" /><ellipse cx={48} cy={-6} rx={25} ry={ey} fill="#fff" />
      {!blink && <><circle cx={-48 + lx * 12} cy={-6 + ly * 12} r={12} fill="#1b1411" /><circle cx={48 + lx * 12} cy={-6 + ly * 12} r={12} fill="#1b1411" /></>}
      <g stroke={C.hair} strokeWidth={13} strokeLinecap="round">
        <line x1={-82} y1={bl + al * -1.5} x2={-22} y2={bl + al * 1.5} />
        <line x1={22} y1={br + ar * 1.5} x2={82} y2={br + ar * -1.5} />
      </g>
      <path d="M-8,8 Q-20,50 0,56 Q20,50 8,8" stroke={C.skinDark} strokeWidth={8} fill="none" strokeLinecap="round" />
      {mouth}
    </g>
  );
};

/** Neutraler Passant als Silhouette. */
export const Silhouette: React.FC<{ x: number; y: number; s?: number; color?: string }> = ({ x, y, s = 1, color = "#1d2a52" }) => (
  <g transform={`translate(${x},${y}) scale(${s})`} fill={color}>
    <circle cx={0} cy={0} r={58} />
    <path d="M-110,260 C-100,110 -60,78 0,78 C60,78 100,110 110,260 L110,520 L-110,520 Z" />
  </g>
);

export const Building: React.FC<{ x: number; y: number; w: number; h: number; color: string; win?: string; roof?: string }> = ({ x, y, w, h, color, win = "#ffe9a8", roof }) => {
  const cols = Math.max(2, Math.floor(w / 70)), rows = Math.max(2, Math.floor(h / 90));
  return (
    <g transform={`translate(${x},${y})`}>
      {roof && <path d={`M-10,0 L${w / 2},-90 L${w + 10},0 Z`} fill={roof} />}
      <rect width={w} height={h} fill={color} />
      {Array.from({ length: rows * cols }).map((_, i) => (
        <rect key={i} x={20 + (i % cols) * ((w - 40) / cols)} y={26 + Math.floor(i / cols) * ((h - 40) / rows)} width={(w - 40) / cols - 20}
          height={((h - 40) / rows) - 28} rx={6} fill={win} opacity={(i * 7) % 5 === 0 ? 0.35 : 0.9} />
      ))}
    </g>
  );
};

export const Bike: React.FC<{ x: number; y: number; s?: number; spin: number; color?: string }> = ({ x, y, s = 1, spin, color = "#ff4d8d" }) => (
  <g transform={`translate(${x},${y}) scale(${s})`}>
    {[-95, 95].map((cx) => (
      <g key={cx} transform={`translate(${cx},0)`}>
        <circle r={78} fill="none" stroke="#111" strokeWidth={10} />
        <g transform={`rotate(${spin})`}><line x1={-78} y1={0} x2={78} y2={0} stroke="#555" strokeWidth={4} /><line x1={0} y1={-78} x2={0} y2={78} stroke="#555" strokeWidth={4} /></g>
      </g>
    ))}
    <path d="M-95,0 L-20,-110 L70,-110 L95,0 M-20,-110 L20,0 L-95,0 M70,-110 L60,-150 M70,-150 L110,-150" stroke={color} strokeWidth={12} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx={-30} cy={-250} r={34} fill="#1d2a52" />
    <path d="M-50,-215 L-20,-110 M-20,-205 L48,-150" stroke="#1d2a52" strokeWidth={30} strokeLinecap="round" />
  </g>
);

export const Cup: React.FC<{ x: number; y: number; s?: number; steam?: boolean }> = ({ x, y, s = 1, steam = true }) => {
  const f = useCurrentFrame();
  return (
    <g transform={`translate(${x},${y}) scale(${s})`}>
      <ellipse cx={0} cy={150} rx={190} ry={36} fill="#ffffff" opacity={0.9} />
      <path d="M-120,0 L120,0 L96,140 Q0,176 -96,140 Z" fill="#ffffff" stroke="#e7dccf" strokeWidth={6} />
      <path d="M118,22 C190,22 190,110 104,108" fill="none" stroke="#ffffff" strokeWidth={22} strokeLinecap="round" />
      <ellipse cx={0} cy={4} rx={118} ry={22} fill="#5a2d1c" />
      <ellipse cx={0} cy={4} rx={86} ry={12} fill="#7a4126" />
      {steam && [-50, 0, 50].map((dx, i) => (
        <path key={i} d={`M${dx},-30 q-22,-40 0,-80 q22,-40 0,-80`} stroke="#ffffff" strokeWidth={14} fill="none" strokeLinecap="round"
          opacity={0.6 - 0.25 * ((f / 12 + i) % 2)} transform={`translate(${Math.sin(f / 9 + i) * 10},${-((f * 2 + i * 30) % 50)})`} />
      ))}
    </g>
  );
};

/** Fußgängerampel mit Ampelmännchen (rot = stehend, grün = gehend). */
export const AmpelLight: React.FC<{ x: number; y: number; s?: number; green?: boolean; glow?: number }> = ({ x, y, s = 1, green = false, glow = 1 }) => {
  const col = green ? C.green : C.red;
  return (
    <g transform={`translate(${x},${y}) scale(${s})`}>
      <rect x={-14} y={0} width={28} height={700} fill="#2b3350" />
      <rect x={-110} y={-420} width={220} height={430} rx={34} fill="#0b0f20" stroke="#394068" strokeWidth={8} />
      <circle cx={0} cy={-210} r={150 * glow} fill={col} opacity={0.18} />
      <g fill={col} stroke={col} strokeWidth={4}>
        <circle cx={0} cy={-340} r={26} />
        <rect x={-14} y={-300} width={28} height={100} rx={8} />
        {green ? (
          <><line x1={-8} y1={-200} x2={-62} y2={-120} strokeWidth={24} strokeLinecap="round" /><line x1={8} y1={-200} x2={56} y2={-110} strokeWidth={24} strokeLinecap="round" />
            <line x1={-40} y1={-290} x2={-70} y2={-230} strokeWidth={18} strokeLinecap="round" /><line x1={40} y1={-290} x2={64} y2={-236} strokeWidth={18} strokeLinecap="round" /></>
        ) : (
          <><line x1={-8} y1={-200} x2={-18} y2={-110} strokeWidth={24} strokeLinecap="round" /><line x1={8} y1={-200} x2={18} y2={-110} strokeWidth={24} strokeLinecap="round" />
            <line x1={-14} y1={-285} x2={-92} y2={-282} strokeWidth={18} strokeLinecap="round" /><line x1={14} y1={-285} x2={92} y2={-282} strokeWidth={18} strokeLinecap="round" /></>
        )}
        <rect x={-34} y={-372} width={68} height={10} rx={5} />
      </g>
    </g>
  );
};
