import React from "react";
import { Composition } from "remotion";
import { Episode } from "./Episode";
import { EPISODES } from "./episodes";

export const Root: React.FC = () => (
  <>
    {Object.entries(EPISODES).map(([id, e]) => (
      <Composition key={id} id={id} component={Episode} defaultProps={{ id }}
        durationInFrames={e.timeline.totalFrames} fps={30} width={1080} height={1920} />
    ))}
  </>
);
