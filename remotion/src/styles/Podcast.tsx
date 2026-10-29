import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { PODCAST } from "./config";

export const Podcast: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={PODCAST} />
);
