import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { CHISME } from "./config";

export const Chisme: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={CHISME} />
);
