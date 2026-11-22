import classroomEpisode from "./episodes/classroom-comedy.json";
import classroomTimeline from "./timelines/classroom-comedy.json";
import homeworkEpisode from "./episodes/homework-excuse.json";
import homeworkTimeline from "./timelines/homework-excuse.json";
import type { Timeline } from "./Episode";

type EpisodeInfo = { id: string; title: string; badge: string };

/** Neue Episode: JSON in src/episodes/, `npm run audio -- <id>`, hier eintragen. */
export const EPISODES: Record<string, { episode: EpisodeInfo; timeline: Timeline }> = {
  "classroom-comedy": { episode: classroomEpisode as EpisodeInfo, timeline: classroomTimeline as unknown as Timeline },
  "homework-excuse": { episode: homeworkEpisode as EpisodeInfo, timeline: homeworkTimeline as unknown as Timeline },
};
