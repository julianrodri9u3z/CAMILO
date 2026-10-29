import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { VOZ_EN_OFF_UGC } from "./config";

export const VozEnOffUgc: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={VOZ_EN_OFF_UGC} />
);
