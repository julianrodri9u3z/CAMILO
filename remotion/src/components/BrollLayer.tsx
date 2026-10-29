import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import type { BrollInsert } from "../EditPlan";

const BrollClip: React.FC<{
  insert: BrollInsert;
  fps: number;
  fadeMs: number;
  zoomPunchIn: boolean;
  /** Frames this insert is held past its end because the next insert crossfades in over it (no flash of A-roll). */
  holdFrames?: number;
}> = ({ insert, fps, fadeMs, zoomPunchIn, holdFrames = 0 }) => {
  const frame = useCurrentFrame();
  const durationFrames = Math.round((insert.durationMs / 1000) * fps);
  const fadeFrames = Math.max(1, Math.round((fadeMs / 1000) * fps));
  const total = durationFrames + holdFrames;

  // when the next insert overlaps, stay fully opaque underneath it instead of fading out to the A-roll
  const opacity = holdFrames
    ? interpolate(frame, [0, fadeFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : interpolate(frame, [0, fadeFrames, durationFrames - fadeFrames, durationFrames], [0, 1, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  // soft entry/exit: arrives slightly blurred and pushed in, leaves the same way -- a transition, not a jump
  const softIn = interpolate(frame, [0, fadeFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const softOut = holdFrames
    ? 0
    : interpolate(frame, [durationFrames - fadeFrames, durationFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const softBlur = 10 * Math.max(softIn, softOut);
  const softScale = 1 + 0.06 * softIn + 0.04 * softOut;
  const isImage = /\.(png|jpe?g|webp)$/i.test(insert.src);
  // Stills (celebrity photos, press screenshots) get a slow Ken Burns push-in so they don't read as frozen video.
  const baseZoom = insert.zoom ?? 1;
  const scale0 = isImage
    ? interpolate(frame, [0, total], [1, 1.08], { extrapolateRight: "clamp" })
    : zoomPunchIn
    ? interpolate(frame, [0, total], [1.08, 1], { extrapolateRight: "clamp" })
    : 1;
  const scale = scale0 * baseZoom * softScale;

  const g = insert.grade;
  const filters = [
    g ? `contrast(${g.contrast ?? 1}) saturate(${g.saturation ?? 1}) brightness(${g.brightness ?? 1})` : "",
    softBlur > 0.05 ? `blur(${softBlur.toFixed(2)}px)` : "",
  ].filter(Boolean);
  const matchFilter = filters.length ? filters.join(" ") : undefined;
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
        // back-to-back inserts: hold this one under the next until the next has fully faded in (crossfade b-roll ->
        // b-roll, never b-roll -> A-roll flash -> b-roll)
        const fadeFrames = Math.max(1, Math.round((fadeMs / 1000) * fps));
        const next = inserts
          .map((n) => Math.round((n.atMs / 1000) * fps))
          .filter((f) => f > from && f <= from + durationInFrames + fadeFrames)
          .sort((a, b) => a - b)[0];
        const holdFrames = next !== undefined ? Math.max(0, next + fadeFrames - (from + durationInFrames)) : 0;
        return (
          <Sequence key={i} from={from} durationInFrames={durationInFrames + holdFrames}>
            <BrollClip insert={insert} fps={fps} fadeMs={fadeMs} zoomPunchIn={zoomPunchIn} holdFrames={next !== undefined ? Math.max(1, holdFrames) : 0} />
          </Sequence>
        );
      })}
    </>
  );
};
