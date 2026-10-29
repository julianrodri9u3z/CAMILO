import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { PODCAST_CLIP } from "./config";

export const PodcastClip: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={PODCAST_CLIP} />
);
