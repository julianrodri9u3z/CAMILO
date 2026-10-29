import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { TIKTOK } from "./config";

export const TikTok: React.FC<EditPlan> = (props) => (
  <Edit editPlan={props} styleConfig={TIKTOK} />
);
