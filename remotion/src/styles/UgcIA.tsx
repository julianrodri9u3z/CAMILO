import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { UGC_IA } from "./config";

export const UgcIA: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={UGC_IA} />
);
