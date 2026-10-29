import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { CODIGOS_VOZ_OFF } from "./config";

export const CodigosVozOff: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={CODIGOS_VOZ_OFF} />
);
