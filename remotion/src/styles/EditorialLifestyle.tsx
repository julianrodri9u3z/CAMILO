import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { EDITORIAL_LIFESTYLE } from "./config";

export const EditorialLifestyle: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={EDITORIAL_LIFESTYLE} />
);
