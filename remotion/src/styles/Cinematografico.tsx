import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { CINEMATOGRAFICO } from "./config";

export const Cinematografico: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={CINEMATOGRAFICO} />
);
