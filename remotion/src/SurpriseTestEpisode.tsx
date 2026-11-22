import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SurpriseTestScene } from "./SurpriseTestScene";
import timeline from "./timelines/surprise-test.json";

/** Komplette Episode "The Surprise Test": Szene 1 ist fertig, weitere Szenen hier hinten anreihen. */
const SCENES = [{ id: "scene-1", component: SurpriseTestScene, frames: timeline.totalFrames }];
export const SURPRISE_TEST_FRAMES = SCENES.reduce((a, s) => a + s.frames, 0);

export const SurpriseTestEpisode: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill>
      {SCENES.map((s) => {
        const Comp = s.component;
        const el = (
          <Sequence key={s.id} from={from} durationInFrames={s.frames}>
            <Comp />
          </Sequence>
        );
        from += s.frames;
        return el;
      })}
    </AbsoluteFill>
  );
};
