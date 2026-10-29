import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { UGC_CREADOR } from "./config";

export const UgcCreador: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={UGC_CREADOR} />
);
