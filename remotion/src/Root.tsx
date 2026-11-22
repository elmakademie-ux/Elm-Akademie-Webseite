import React from "react";
import { Composition } from "remotion";
import { ClassroomComedy, TOTAL_FRAMES } from "./ClassroomComedy";

export const Root: React.FC = () => (
  <Composition id="ClassroomComedy" component={ClassroomComedy} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} />
);
