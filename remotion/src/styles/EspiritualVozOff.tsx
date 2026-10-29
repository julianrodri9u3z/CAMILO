import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { ESPIRITUAL_VOZ_OFF } from "./config";

export const EspiritualVozOff: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={ESPIRITUAL_VOZ_OFF} />
);
