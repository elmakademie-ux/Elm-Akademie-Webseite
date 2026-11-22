/**
 * Figuren-Register. Die sechs Szenenbilder aus dem Storyboard sind die verbindliche Vorlage:
 * Das Aussehen von Lehrer und Schüler wird nur durch Auswahl dieser Bilder (Posen) bestimmt,
 * nie durch neue Figurenbilder. Neue Episoden fügen weitere Posen hier hinzu.
 */
export type CharacterId = "teacher" | "student" | "teacher_f" | "student_y";

export type Pose = {
  /** Bild in public/ */
  image: string;
  /** Kamera hält den Fokus (Gesicht) in der Bildmitte */
  center?: boolean;
  /** Mundbereich (Anteile 0..1): wird beim Sprechen mit der Stimme verformt */
  mouth?: { x: number; y: number; rx: number; ry: number };
  /** optional: animierter Clip (aus dem Bild erzeugt), ersetzt das Standbild; Länge in Frames */
  clip?: string;
  clipFrames?: number;
  /** Kamera-Fokus im Bild (0..1) */
  focus: { x: number; y: number };
  /** Zoom am Anfang und am Ende der Einstellung */
  zoom: [number, number];
  /** leichte Kamerafahrt in Pixeln (von, nach) */
  drift?: [{ x: number; y: number }, { x: number; y: number }];
};

export type CharacterDef = {
  name: string;
  /** Farbe des Namensschilds und des Untertitel-Texts */
  color: string;
  textColor: string;
  poses: Record<string, Pose>;
};

export const CHARACTERS = {
  teacher: {
    name: "LEHRER",
    color: "#2b4a8c",
    textColor: "#ffffff",
    poses: {
      pointing: { image: "assets/scene-01.png", focus: { x: 0.22, y: 0.32 }, zoom: [1.0, 1.4], drift: [{ x: 0, y: 0 }, { x: 14, y: 0 }] },
      glasses: { image: "assets/scene-03.png", focus: { x: 0.74, y: 0.3 }, zoom: [1.04, 1.22], drift: [{ x: 14, y: 0 }, { x: -8, y: -6 }] },
      shocked: { image: "assets/scene-05.png", focus: { x: 0.56, y: 0.34 }, zoom: [1.0, 1.24] },
      tired: { image: "assets/scene-06.png", focus: { x: 0.5, y: 0.4 }, zoom: [1.16, 1.0] },
    },
  },
  student: {
    name: "ALI",
    color: "#d93232",
    textColor: "#ffd640",
    poses: {
      explaining: { image: "assets/scene-02.png", focus: { x: 0.5, y: 0.36 }, zoom: [1.0, 1.2], drift: [{ x: -10, y: 0 }, { x: 10, y: -6 }] },
      thumb: { image: "assets/scene-04.png", focus: { x: 0.45, y: 0.34 }, zoom: [1.22, 1.0], drift: [{ x: 8, y: 0 }, { x: -6, y: 0 }] },
      satisfied: { image: "assets/scene-06.png", focus: { x: 0.7, y: 0.45 }, zoom: [1.0, 1.25] },
      arms_crossed: { image: "assets/scene-01.png", focus: { x: 0.7, y: 0.45 }, zoom: [1.0, 1.3] },
    },
  },
} as unknown as Record<CharacterId, CharacterDef>;

/** Zweite Besetzung (Storyboard "Surprise Test"): Lehrerin mit lockigen roten Haaren, Schüler im gelben Hoodie. */
CHARACTERS.teacher_f = {
  name: "TEACHER",
  color: "#2f7d4a",
  textColor: "#ffffff",
  poses: {
    pointing: { image: "assets/surprise-test/scene-01.png", focus: { x: 0.33, y: 0.27 }, zoom: [1.1, 1.65], center: true,
      mouth: { x: 0.341, y: 0.361, rx: 0.05, ry: 0.042 } },
    thinking: { image: "assets/surprise-test/scene-03.png", focus: { x: 0.45, y: 0.3 }, zoom: [1.0, 1.3], center: true,
      drift: [{ x: -22, y: 0 }, { x: 22, y: -6 }] },
    surprised: { image: "assets/surprise-test/scene-05.png", focus: { x: 0.45, y: 0.35 }, zoom: [1.0, 1.25], center: true },
    arms_crossed: { image: "assets/surprise-test/scene-06.png", focus: { x: 0.25, y: 0.36 }, zoom: [1.5, 1.68], center: true },
  },
};
CHARACTERS.student_y = {
  name: "STUDENT",
  color: "#d4a017",
  textColor: "#ffd640",
  poses: {
    shrugging: { image: "assets/surprise-test/scene-02.png", focus: { x: 0.5, y: 0.35 }, zoom: [1.0, 1.2], center: true },
    idea: { image: "assets/surprise-test/scene-04.png", focus: { x: 0.45, y: 0.35 }, zoom: [1.0, 1.2], center: true },
    laughing: { image: "assets/surprise-test/scene-06.png", focus: { x: 0.75, y: 0.4 }, zoom: [1.2, 1.4], center: true },
    worried: { image: "assets/surprise-test/scene-01.png", focus: { x: 0.75, y: 0.45 }, zoom: [1.1, 1.4], center: true },
  },
};

/** src/clips.json: { "teacher/pointing": { "file": "assets/clips/teacher-pointing.mp4", "frames": 90 }, ... } */
import clips from "./clips.json";
const CLIPS = clips as Record<string, { file: string; frames: number }>;

export const getPose = (who: CharacterId, pose: string): Pose => {
  const p = CHARACTERS[who].poses[pose] ?? Object.values(CHARACTERS[who].poses)[0];
  const c = CLIPS[`${who}/${pose}`];
  return c ? { ...p, clip: c.file, clipFrames: c.frames } : p;
};
