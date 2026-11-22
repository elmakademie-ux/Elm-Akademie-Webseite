import React from "react";
import { Composition } from "remotion";
import { Episode } from "./Episode";
import { EPISODES } from "./episodes";
import { SurpriseTestScene } from "./SurpriseTestScene";
import { SURPRISE_TEST_FRAMES, SurpriseTestEpisode } from "./SurpriseTestEpisode";
import surprise from "./timelines/surprise-test.json";

export const Root: React.FC = () => (
  <>
    {Object.entries(EPISODES).map(([id, e]) => (
      <Composition key={id} id={id} component={Episode} defaultProps={{ id }}
        durationInFrames={e.timeline.totalFrames} fps={30} width={1080} height={1920} />
    ))}
    <Composition id="surprise-test" component={SurpriseTestEpisode} durationInFrames={SURPRISE_TEST_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="surprise-test-scene1" component={SurpriseTestScene} durationInFrames={surprise.totalFrames} fps={30} width={1080} height={1920} />
  </>
);
