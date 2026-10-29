import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { TRAILER_DOCUMENTAL } from "./config";

export const TrailerDocumental: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={TRAILER_DOCUMENTAL} />
);
