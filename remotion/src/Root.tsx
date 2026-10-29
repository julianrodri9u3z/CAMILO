import React from "react";
import { Composition } from "remotion";
import { Cinematografico } from "./styles/Cinematografico";
import { UgcIA } from "./styles/UgcIA";
import { TikTok } from "./styles/TikTok";
import { Chisme } from "./styles/Chisme";
import { Podcast } from "./styles/Podcast";
import { VozEnOffUgc } from "./styles/VozEnOffUgc";
import { EspiritualVozOff } from "./styles/EspiritualVozOff";
import { CodigosVozOff } from "./styles/CodigosVozOff";
import { UgcCreador } from "./styles/UgcCreador";
import { EditorialLifestyle } from "./styles/EditorialLifestyle";
import { TrailerDocumental } from "./styles/TrailerDocumental";
import { Vsl } from "./styles/Vsl";
import { PodcastClip } from "./styles/PodcastClip";
import { DEFAULT_CTA_DURATION_IN_FRAMES, defaultEditPlan, EditPlan } from "./EditPlan";

const calculateMetadata = async ({ props }: { props: EditPlan }) => ({
  durationInFrames:
    props.totalDurationInFrames + (props.cta ? props.cta.durationInFrames ?? DEFAULT_CTA_DURATION_IN_FRAMES : 0),
  fps: props.fps,
  width: props.width,
  height: props.height,
});

const compositions: Array<{ id: string; component: React.FC<EditPlan> }> = [
  { id: "Cinematografico", component: Cinematografico },
  { id: "UgcIA", component: UgcIA },
  { id: "TikTok", component: TikTok },
  { id: "Chisme", component: Chisme },
  { id: "Podcast", component: Podcast },
  { id: "VozEnOffUgc", component: VozEnOffUgc },
  { id: "EspiritualVozOff", component: EspiritualVozOff },
  { id: "CodigosVozOff", component: CodigosVozOff },
  { id: "UgcCreador", component: UgcCreador },
  { id: "EditorialLifestyle", component: EditorialLifestyle },
  { id: "TrailerDocumental", component: TrailerDocumental },
  { id: "Vsl", component: Vsl },
  { id: "PodcastClip", component: PodcastClip },
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {compositions.map(({ id, component }) => (
        <Composition
          key={id}
          id={id}
          component={component}
          durationInFrames={defaultEditPlan.totalDurationInFrames}
          fps={defaultEditPlan.fps}
          width={defaultEditPlan.width}
          height={defaultEditPlan.height}
          defaultProps={defaultEditPlan}
          calculateMetadata={calculateMetadata}
        />
      ))}
    </>
  );
};
