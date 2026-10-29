import React from "react";
import type { EditPlan } from "../EditPlan";
import { Edit } from "../components/Edit";
import { VSL } from "./config";

export const Vsl: React.FC<EditPlan> = (props) => <Edit editPlan={props} styleConfig={VSL} />;
