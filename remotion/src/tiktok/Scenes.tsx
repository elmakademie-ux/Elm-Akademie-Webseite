import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT_BLACK, FONT_BOLD } from "../fonts";
import { AmpelLight, Bike, Building, C, Cup, Person, Silhouette } from "./art";

export type SceneProps = { lines: { relStart: number; relEnd: number }[]; duration: number };

const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const usePop = (delay: number, damping = 10, stiffness = 220) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - delay, fps, config: { damping, stiffness, mass: 0.6 } });
};
const Svg: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0 }}>{children}</svg>
);
const Txt: React.FC<{ x: number; y: number; size: number; color?: string; children: React.ReactNode; anchor?: "middle" | "start" | "end"; weight?: "black" | "bold"; rot?: number; stroke?: string; sw?: number; opacity?: number; scale?: number }> =
  ({ x, y, size, color = "#fff", children, anchor = "middle", weight = "black", rot = 0, stroke, sw = 0, opacity = 1, scale = 1 }) => (
    <text x={x} y={y} fontSize={size} fill={color} textAnchor={anchor} fontFamily={weight === "black" ? FONT_BLACK : FONT_BOLD}
      transform={`rotate(${rot} ${x} ${y}) translate(${x} ${y}) scale(${scale}) translate(${-x} ${-y})`} stroke={stroke} strokeWidth={sw} paintOrder="stroke" opacity={opacity} strokeLinejoin="round">
      {children}
    </text>
  );

/** Große Nummer (1, 2, 3) links oben. */
const Badge: React.FC<{ n: string; at: number }> = ({ n, at }) => {
  const p = usePop(at, 8, 200);
  return (
    <g transform={`translate(150 300) scale(${Math.max(0.01, p)}) rotate(${(1 - p) * -40})`}>
      <circle r={110} fill={C.yellow} stroke="#0b0b10" strokeWidth={10} />
      <Txt x={0} y={52} size={150} color="#0b0b10">{n}</Txt>
    </g>
  );
};

// ================================================================ Szene 1: Straßen-Montage
const sky = (id: string, a: string, b: string) => (
  <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={a} /><stop offset="1" stopColor={b} /></linearGradient></defs>
);
const skyline = (offset: number, color: string, base: number, hs: number, seed: number) =>
  Array.from({ length: 9 }).map((_, i) => {
    const w = 190 + ((i * 53 + seed) % 90), h = (260 + ((i * 97 + seed * 13) % 300)) * hs;
    return <rect key={i} x={((i * 230 + offset) % 2100) - 220} y={base - h} width={w} height={h} fill={color} />;
  });

export const Scene1: React.FC<SceneProps> = ({ duration }) => {
  const f = useCurrentFrame();
  const cuts = [0, 38, 77, 116, duration];
  const shot = cuts.findIndex((c, i) => f >= c && f < cuts[i + 1]);
  const lf = f - cuts[shot], len = cuts[shot + 1] - cuts[shot];
  const tx = interpolate(lf, [0, 6], [220, 0], { extrapolateRight: "clamp" });
  const blur = interpolate(lf, [0, 6], [16, 0], { extrapolateRight: "clamp" });
  const shake = Math.sin(f * 1.9) * 5;
  const zoom = 1 + 0.1 * (lf / len);
  const tram = interpolate(lf, [0, len], [-900, 1400]);
  const badge = usePop(12, 8, 200);
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <AbsoluteFill style={{ transform: `translate(${tx + shake}px, ${Math.cos(f * 2.3) * 4}px) scale(${zoom})`, filter: `blur(${blur}px)` }}>
        {shot === 0 && (
          <Svg>
            {sky("s0", "#ff9a5a", "#7cc4ff")}
            <rect width={1080} height={1920} fill="url(#s0)" />
            <circle cx={820} cy={420} r={120} fill="#fff1c2" opacity={0.9} />
            {skyline(-lf * 2, "#6f86b8", 1150, 1.1, 1)}
            {skyline(-lf * 5, "#40558a", 1250, 1, 4)}
            {skyline(-lf * 9, "#22305c", 1400, 0.9, 7)}
            <rect y={1180} width={1080} height={740} fill="#1a2447" />
            <line x1={0} y1={1260} x2={1080} y2={1260} stroke="#8aa0d6" strokeWidth={8} />
            <line x1={0} y1={640} x2={1080} y2={600} stroke="#0b0f20" strokeWidth={5} />
            <g transform={`translate(${tram} 960)`}>
              <rect width={640} height={230} rx={34} fill="#f4f6ff" /><rect y={120} width={640} height={52} fill="#d62839" />
              {[0, 1, 2, 3].map((i) => <rect key={i} x={30 + i * 150} y={28} width={118} height={78} rx={10} fill="#243a73" />)}
              <rect x={290} y={-64} width={60} height={64} fill="#0b0f20" /><circle cx={110} cy={238} r={30} fill="#0b0f20" /><circle cx={530} cy={238} r={30} fill="#0b0f20" />
            </g>
          </Svg>
        )}
        {shot === 1 && (
          <Svg>
            {sky("s1", "#ffd9a0", "#fff3dc")}
            <rect width={1080} height={1920} fill="url(#s1)" />
            {[0, 1, 2, 3].map((i) => {
              const x = ((i * 460 - lf * 7 + 480) % 1840) - 460;
              const names = ["BÄCKEREI", "APOTHEKE", "SUPERMARKT", "CAFÉ"];
              const cols = ["#ff8a3d", "#e8f1ff", "#2ec27e", "#c9743a"];
              return (
                <g key={i} transform={`translate(${x} 430)`}>
                  <rect width={440} height={700} fill={i % 2 ? "#8c97b8" : "#b8946a"} />
                  <rect x={30} y={330} width={380} height={340} rx={8} fill="#243a73" opacity={0.85} />
                  <path d={`M-10,250 L450,250 L430,330 L10,330 Z`} fill={cols[i]} />
                  <Txt x={220} y={296} size={52} color={i === 1 ? "#d62839" : "#fff"}>{names[i]}</Txt>
                  {[0, 1].map((k) => <rect key={k} x={50 + k * 200} y={40} width={150} height={150} rx={10} fill="#ffe9a8" />)}
                </g>
              );
            })}
            <rect y={1130} width={1080} height={790} fill="#46506e" />
            <rect y={1130} width={1080} height={16} fill="#a8b2d1" />
            <Bike x={interpolate(lf, [0, len], [1500, -500])} y={1500} s={1.5} spin={lf * 22} color="#ff4d8d" />
            <Bike x={interpolate(lf, [0, len], [1900, -100])} y={1330} s={0.9} spin={lf * 20} color="#17b8a6" />
            <Silhouette x={interpolate(lf, [0, len], [200, -200])} y={720} s={1.3} color="#1d2a52" />
          </Svg>
        )}
        {shot === 2 && (
          <Svg>
            <rect width={1080} height={1920} fill="#0b1230" />
            {Array.from({ length: 18 }).map((_, i) => (
              <rect key={i} x={0} y={(i * 120 + lf * 36) % 2000 - 80} width={1080} height={6} fill="#2a3a7a" opacity={0.7} />
            ))}
            <g transform={`translate(540 640) scale(${0.5 + 0.5 * usePopStatic(lf, 0)})`}>
              <rect x={-230} y={-230} width={460} height={460} rx={46} fill="#0e5cc9" stroke="#fff" strokeWidth={14} />
              <Txt x={0} y={120} size={400} color="#fff">U</Txt>
            </g>
            <rect x={120} y={940} width={840} height={130} rx={18} fill="#fff" />
            <Txt x={540} y={1034} size={72} color="#0b0b10" weight="bold">Hauptbahnhof</Txt>
            {[0, 1, 2].map((i) => <Silhouette key={i} x={((i * 420 + lf * 12) % 1500) - 200} y={1160} s={0.9} color="#05081a" />)}
          </Svg>
        )}
        {shot === 3 && (
          <Svg>
            {sky("s3", "#7cc4ff", "#e8f4ff")}
            <rect width={1080} height={1920} fill="url(#s3)" />
            <Building x={-30} y={300} w={360} h={820} color="#c4986b" roof="#8a3b2e" />
            <Building x={760} y={380} w={340} h={740} color="#8c97b8" />
            <path d="M0,1920 L0,1060 L1080,1060 L1080,1920 Z" fill="#4a5470" />
            <path d="M380,1060 L700,1060 L1180,1920 L-100,1920 Z" fill="#2f3650" />
            {Array.from({ length: 7 }).map((_, i) => {
              const t = ((i * 0.15 + lf * 0.02) % 1), y = 1060 + t * t * 860, w = 8 + t * 40, h = 18 + t * 120;
              return <rect key={i} x={540 - w / 2} y={y} width={w} height={h} fill="#fff" opacity={0.9} />;
            })}
            <g transform={`translate(${interpolate(lf, [0, 12], [-700, 540], { extrapolateRight: "clamp" })} 520)`}>
              <rect x={-330} y={-80} width={660} height={160} rx={16} fill="#fff" stroke="#0b0b10" strokeWidth={8} />
              <Txt x={0} y={26} size={92} color="#0b0b10" weight="bold">Hauptstraße</Txt>
            </g>
            <Bike x={interpolate(lf, [0, len], [1500, -300])} y={1560} s={1.6} spin={lf * 24} />
          </Svg>
        )}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(5,8,24,0.55) 0%, rgba(5,8,24,0) 30%, rgba(5,8,24,0) 62%, rgba(5,8,24,0.65) 100%)" }} />
      <Svg>
        <g transform={`translate(540 330) scale(${Math.max(0.01, badge)}) rotate(${(1 - badge) * 30})`}>
          <circle r={150} fill={C.yellow} stroke="#0b0b10" strokeWidth={12} />
          <Txt x={0} y={78} size={230} color="#0b0b10">3</Txt>
        </g>
        <Txt x={540} y={560} size={64} color="#fff" weight="bold" stroke="#0b0b10" sw={10} opacity={clamp((f - 16) / 6)}>ÜBERRASCHUNGEN</Txt>
        <Txt x={540} y={634} size={52} color={C.yellow} weight="bold" stroke="#0b0b10" sw={9} opacity={clamp((f - 20) / 6)}>IN DEUTSCHLAND</Txt>
      </Svg>
    </AbsoluteFill>
  );
};
const usePopStatic = (lf: number, delay: number) => clamp((lf - delay) / 8);

// ================================================================ Szene 2: Kaffee-Termin
const WEEKS = [
  { w: 49, rows: ["Meeting", "Zahnarzt", "Sport", "Elternabend", "Amt"] },
  { w: 50, rows: ["Arzt", "Meeting", "Yoga", "Umzug", "Meeting"] },
  { w: 51, rows: ["Meeting", "Kaffee  14:00", "Sport", "Familie", "Amt"] },
];
const DAYS = ["Mo", "Di", "Mi", "Do", "Fr"];

export const Scene2: React.FC<SceneProps> = ({ lines }) => {
  const f = useCurrentFrame();
  const [br, main, rea] = lines;
  const bubble = usePop(main.relStart, 9, 200);
  const flipFrom = main.relEnd, step = 11;
  const wk = clamp(Math.floor((f - flipFrom) / step), 0, 2);
  const flipping = f >= flipFrom && f < flipFrom + 3 * step;
  const booked = f >= flipFrom + 45;
  const busy = usePop(main.relStart - 6, 12, 120);
  const react = usePop(rea.relStart, 9, 180);
  const calIn = clamp((f - 4) / 10);
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #2a1646 0%, #0f1b3d 70%)" }}>
      <Svg>
        <Badge n="1" at={br.relStart} />
        {/* Chat */}
        <g transform={`translate(560 240) scale(${Math.max(0.01, bubble)})`}>
          <rect x={-270} y={-60} width={540} height={110} rx={50} fill="#fff" />
          <Txt x={0} y={12} size={46} color="#0b0b10" weight="bold">Kaffee heute Abend?</Txt>
        </g>
        <g transform={`translate(900 260) scale(${Math.max(0.01, bubble) * 0.5})`}><Cup x={0} y={0} /></g>
        {/* Kalender */}
        <g transform={`translate(60 ${380 + (1 - calIn) * 300})`} opacity={calIn}>
          <rect width={900} height={640} rx={36} fill="#fff" />
          <path d="M0,36 Q0,0 36,0 L864,0 Q900,0 900,36 L900,110 L0,110 Z" fill={C.red} />
          <Txt x={450} y={78} size={64} color="#fff">{flipping || booked ? `WOCHE ${WEEKS[wk].w}` : "WOCHE 49"}</Txt>
          {WEEKS[wk].rows.map((r, i) => {
            const show = clamp((f - (br.relStart + 10) - i * 3) / 6);
            const kaffee = wk === 2 && i === 1;
            return (
              <g key={i} transform={`translate(0 ${130 + i * 100})`} opacity={show}>
                <Txt x={40} y={60} size={50} color="#33405f" anchor="start" weight="bold">{DAYS[i]}</Txt>
                <rect x={150} y={8} width={710} height={80} rx={20} fill={kaffee ? C.green : ["#cfe0ff", "#d6f5e3", "#ffe2c9", "#f3d6ff", "#ffd6dd"][i]} />
                <Txt x={185} y={64} size={46} color={kaffee ? "#04210f" : "#1d2a52"} anchor="start" weight="bold">{kaffee ? (booked ? "Kaffee  14:00  ✓" : "frei …") : r}</Txt>
              </g>
            );
          })}
        </g>
        {/* BELEGT / bestätigt */}
        {f >= flipFrom + 30 && f < flipFrom + 45 && <Txt x={540} y={760} size={150} color={C.red} stroke="#fff" sw={14} rot={-8}>ALLES VOLL!</Txt>}
        {booked && f < rea.relStart && <g transform={`translate(400 1020) rotate(-4) scale(${Math.max(0.01, usePopStatic(f, flipFrom + 45))})`}>
          <rect x={-290} y={-56} width={580} height={104} rx={24} fill={C.green} stroke="#0b0b10" strokeWidth={8} />
          <Txt x={0} y={18} size={52} color="#04210f">TERMIN BESTÄTIGT</Txt></g>}
        {/* Reaktion */}
        {f >= rea.relStart && <g transform={`translate(${800 + (1 - react) * 500} 860) rotate(${(1 - react) * 20})`}><Person x={0} y={0} s={0.7} expr="wow" look={[-0.6, 0.3]} bob={Math.sin(f / 4) * 6} /></g>}
        <Txt x={310} y={1075} size={80} color={C.yellow} stroke="#0b0b10" sw={12} rot={-6} scale={Math.max(0.01, react)} opacity={f >= rea.relStart ? 1 : 0}>3 WOCHEN?!</Txt>
      </Svg>
    </AbsoluteFill>
  );
};

// ================================================================ Szene 3: "Das ist interessant."
const Thumb: React.FC = () => (
  <g>
    <rect x={-70} y={-10} width={140} height={150} rx={28} fill={C.skin} stroke="#0b0b10" strokeWidth={8} />
    <rect x={-40} y={-120} width={64} height={130} rx={30} fill={C.skin} stroke="#0b0b10" strokeWidth={8} transform="rotate(-12)" />
  </g>
);

export const Scene3: React.FC<SceneProps> = ({ lines }) => {
  const f = useCurrentFrame();
  const [br, main, rea] = lines;
  const quoteAt = Math.round(main.relStart + (main.relEnd - main.relStart) * 0.42);
  const bubble = usePop(quoteAt, 9, 200);
  const card = clamp((f - main.relEnd) / 12);
  const flip = spring({ frame: f - main.relEnd, fps: 30, config: { damping: 12, stiffness: 160, mass: 0.7 } });
  const showCard = f >= main.relEnd && f < rea.relStart + 6;
  const reaP = usePop(rea.relStart, 9, 170);
  const confused = f >= quoteAt && f < rea.relStart;
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #3b1f7a 0%, #101a46 75%)" }}>
      <Svg>
        <Badge n="2" at={br.relStart} />
        {!(f >= rea.relStart) && (
          <>
            <Silhouette x={210} y={640} s={1.15} color="#171f45" />
            <g transform={`translate(560 320) scale(${Math.max(0.01, bubble)})`}>
              <path d="M-170,60 L-250,190 L-90,60 Z" fill="#fff" />
              <rect x={-280} y={-70} width={560} height={140} rx={46} fill="#fff" />
              <Txt x={0} y={16} size={46} color="#0b0b10" weight="bold">Das ist interessant.</Txt>
            </g>
            <Person x={770} y={760} s={0.95} expr={confused ? "confused" : "neutral"} look={[-0.7, 0.2]} tilt={confused ? Math.sin(f / 6) * 6 : 0} bob={Math.sin(f / 5) * 4} />
            {confused && [0, 1, 2].map((i) => {
              const t = ((f + i * 14) % 42) / 42;
              return <Txt key={i} x={650 + i * 120} y={600 - t * 50 - i * 14} size={96 + i * 16} color={C.yellow} stroke="#0b0b10" sw={10} opacity={1 - t * 0.6} rot={i * 12 - 12}>?</Txt>;
            })}
          </>
        )}
        {showCard && (
          <g transform={`translate(540 800) scale(${Math.max(0.01, card)})`}>
            <g transform={`scale(${Math.abs(Math.cos((1 - clamp(flip)) * Math.PI / 2))} 1)`}>
              <rect x={-420} y={-260} width={840} height={520} rx={44} fill="#fff" stroke="#0b0b10" strokeWidth={10} />
              <Txt x={0} y={-150} size={54} color="#5a6690" weight="bold">Gemeint ist eigentlich:</Txt>
              <Txt x={0} y={-30} size={78} color="#d62839">„Das gefällt mir</Txt>
              <Txt x={0} y={64} size={78} color="#d62839">nicht so.“</Txt>
              {f >= main.relEnd + 34 && <g transform={`translate(0 170) scale(${Math.max(0.01, usePopStatic(f, main.relEnd + 34))})`}>
                <circle r={50} fill="#d62839" /><path d="M-24,-24 L24,24 M24,-24 L-24,24" stroke="#fff" strokeWidth={14} strokeLinecap="round" /></g>}
            </g>
          </g>
        )}
        {f >= rea.relStart && (
          <g transform={`translate(540 760) scale(${Math.max(0.01, reaP)})`}>
            <Person x={0} y={0} s={1.15} expr="happy" bob={Math.sin(f / 5) * 5} />
            <g transform="translate(290 300) rotate(12) scale(1.1)"><Thumb /></g>
            <Txt x={-300} y={-200} size={120} color={C.yellow} stroke="#0b0b10" sw={12} rot={-8}>Super!</Txt>
          </g>
        )}
      </Svg>
    </AbsoluteFill>
  );
};

// ================================================================ Szene 4: Rote Ampel nachts
export const Scene4: React.FC<SceneProps> = ({ lines, duration }) => {
  const f = useCurrentFrame();
  const [br, main, rea] = lines;
  const greenAt = rea.relEnd + 8;
  const green = f >= greenAt;
  const walk = interpolate(f, [greenAt, greenAt + 34], [0, 560], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stamp = usePop(rea.relStart + 6, 9, 200);
  const mins = 47 + Math.floor(f / 45);
  const look: [number, number] = [Math.sin(f / 14) > 0 ? 0.8 : -0.8, 0];
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #05081c 0%, #0f1b3d 70%)" }}>
      <Svg>
        {Array.from({ length: 28 }).map((_, i) => <circle key={i} cx={(i * 197) % 1080} cy={130 + ((i * 131) % 520)} r={2 + (i % 3)} fill="#fff" opacity={0.35 + 0.5 * Math.abs(Math.sin(f / 18 + i))} />)}
        <circle cx={860} cy={320} r={90} fill="#fff6d6" /><circle cx={890} cy={300} r={80} fill="#05081c" opacity={0.18} />
        <Building x={-20} y={560} w={300} h={540} color="#111a3d" win="#ffd23f" />
        <Building x={780} y={620} w={320} h={480} color="#111a3d" win="#ffd23f" />
        <rect y={1090} width={1080} height={30} fill="#3a4470" />
        <rect y={1120} width={1080} height={300} fill="#161c36" />
        {Array.from({ length: 8 }).map((_, i) => <rect key={i} x={i * 160 - 20} y={1260} width={90} height={12} fill="#c9cee6" opacity={0.7} />)}
        <Badge n="3" at={br.relStart} />
        {/* Uhr und Autozähler */}
        <g transform="translate(610 250)">
          <rect x={-230} y={-60} width={380} height={96} rx={20} fill="#0b0f20" stroke="#394068" strokeWidth={6} />
          <Txt x={-40} y={14} size={70} color={C.green} weight="bold">{`02:${String(mins).padStart(2, "0")}`}</Txt>
          <rect x={170} y={-60} width={200} height={96} rx={20} fill="#0b0f20" stroke="#394068" strokeWidth={6} />
          <Txt x={270} y={-10} size={30} color="#9aa5d6" weight="bold">AUTOS</Txt>
          <Txt x={270} y={26} size={56} color={C.yellow} weight="bold">0</Txt>
        </g>
        <AmpelLight x={470} y={700} s={0.62} green={green} glow={1 + 0.06 * Math.sin(f / 4)} />
        <Person x={230 + walk} y={540} s={0.5} full expr={green ? "happy" : "wait"} look={look} crossed={!green} bob={green ? Math.abs(Math.sin(f / 3)) * -10 : 0} />
        {f >= rea.relStart + 6 && !green && (
          <g transform={`translate(740 640) rotate(-7) scale(${Math.max(0.01, stamp)})`}>
            <rect x={-250} y={-70} width={500} height={140} rx={26} fill={C.red} stroke="#fff" strokeWidth={10} />
            <Txt x={0} y={34} size={80} color="#fff">ROT = STOPP</Txt>
          </g>
        )}
      </Svg>
    </AbsoluteFill>
  );
};

// ================================================================ Szene 5: Kommentare
const ANSWERS = ["Mülltrennung!", "Pfandflaschen!", "Sonntags alles zu!", "Pünktlichkeit!"];

export const Scene5: React.FC<SceneProps> = ({ lines }) => {
  const f = useCurrentFrame();
  const [main] = lines;
  const intro = usePop(4, 10, 200);
  const box = usePop(main.relEnd - 40, 11, 190);
  const t0 = main.relEnd - 30;
  const idx = Math.floor(Math.max(0, f - t0) / 40) % ANSWERS.length;
  const typed = Math.min(ANSWERS[idx].length, Math.floor(((Math.max(0, f - t0) % 40) / 24) * ANSWERS[idx].length));
  const arrow = Math.sin(f / 4) * 18;
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #ff4d8d 0%, #ff7a45 60%, #ffd23f 100%)" }}>
      <Svg>
        <g transform={`translate(${270 - (1 - intro) * 500} 620)`}><Person x={0} y={0} s={1.15} expr="happy" bob={Math.sin(f / 5) * 6} tilt={Math.sin(f / 9) * 4} /></g>
        <g transform={`translate(740 360) rotate(-8) scale(${Math.max(0.01, intro)})`}>
          <rect x={-210} y={-120} width={420} height={240} rx={50} fill="#fff" stroke="#0b0b10" strokeWidth={10} />
          <Txt x={0} y={-10} size={150} color={C.pink}>?!</Txt>
          <Txt x={0} y={80} size={44} color="#0b0b10" weight="bold">Und du?</Txt>
        </g>
        <g transform={`translate(${470} ${1000 + (1 - box) * 400}) scale(${Math.max(0.01, box)})`} opacity={clamp(box)}>
          <rect x={-400} y={-90} width={800} height={180} rx={90} fill="#fff" stroke="#0b0b10" strokeWidth={10} />
          <circle cx={-315} cy={0} r={46} fill={C.teal} />
          <Txt x={-245} y={22} size={64} color="#0b0b10" anchor="start" weight="bold">{ANSWERS[idx].slice(0, typed)}{f % 16 < 9 ? "|" : ""}</Txt>
        </g>
        <g transform={`translate(${900 + arrow} 1000) scale(0.75)`} opacity={clamp(box)}>
          <path d="M-70,-40 h80 v-50 l120,110 l-120,110 v-50 h-80 Z" fill="#0b0b10" />
          <path d="M-60,-30 h80 v-40 l96,90 l-96,90 v-40 h-80 Z" fill={C.yellow} />
        </g>
      </Svg>
    </AbsoluteFill>
  );
};
