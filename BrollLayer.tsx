import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import type { BrollInsert } from "../EditPlan";

const BrollClip: React.FC<{
  insert: BrollInsert;
  fps: number;
  fadeMs: number;
  zoomPunchIn: boolean;
}> = ({ insert, fps, fadeMs, zoomPunchIn }) => {
  const frame = useCurrentFrame();
  const durationFrames = Math.round((insert.durationMs / 1000) * fps);
  const fadeFrames = Math.max(1, Math.round((fadeMs / 1000) * fps));

  const opacity = interpolate(
    frame,
    [0, fadeFrames, durationFrames - fadeFrames, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const isImage = /\.(png|jpe?g|webp)$/i.test(insert.src);
  // Stills (celebrity photos, press screenshots) get a slow Ken Burns push-in so they don't read as frozen video.
  const baseZoom = insert.zoom ?? 1;
  const scale0 = isImage
    ? interpolate(frame, [0, durationFrames], [1, 1.08], { extrapolateRight: "clamp" })
    : zoomPunchIn
    ? interpolate(frame, [0, durationFrames], [1.08, 1], { extrapolateRight: "clamp" })
    : 1;
  const scale = scale0 * baseZoom;

  const g = insert.grade;
  const matchFilter = g
    ? `contrast(${g.contrast ?? 1}) saturate(${g.saturation ?? 1}) brightness(${g.brightness ?? 1})`
    : undefined;
  return (
    <AbsoluteFill style={{ opacity, filter: matchFilter }}>
      {isImage ? (
        <Img src={staticFile(insert.src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, transformOrigin: insert.zoomOrigin === "top" ? "50% 0%" : insert.zoomOrigin === "bottom" ? "50% 100%" : "50% 50%" }} />
      ) : (
        <OffthreadVideo
          muted
          src={staticFile(insert.src)}
          style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, transformOrigin: insert.zoomOrigin === "top" ? "50% 0%" : insert.zoomOrigin === "bottom" ? "50% 100%" : "50% 50%" }}
        />
      )}
      {insert.scrim ? (
        // Darkens the lower half so white captions stay readable over bright stock clips.
        <AbsoluteFill
          style={{ background: `linear-gradient(to bottom, rgba(0,0,0,0) 40%, rgba(0,0,0,${insert.scrim}) 100%)` }}
        />
      ) : null}
    </AbsoluteFill>
  );
};

export const BrollLayer: React.FC<{
  inserts: BrollInsert[];
  fps: number;
  fadeMs: number;
  zoomPunchIn: boolean;
}> = ({ inserts, fps, fadeMs, zoomPunchIn }) => {
  return (
    <>
      {inserts.map((insert, i) => {
        const from = Math.round((insert.atMs / 1000) * fps);
        const durationInFrames = Math.round((insert.durationMs / 1000) * fps);
        return (
          <Sequence key={i} from={from} durationInFrames={durationInFrames}>
            <BrollClip insert={insert} fps={fps} fadeMs={fadeMs} zoomPunchIn={zoomPunchIn} />
          </Sequence>
        );
      })}
    </>
  );
};
