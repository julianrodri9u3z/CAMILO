import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A persistent channel/brand mark in a top corner ("Gaia Original" + show
 * logo in the ADS GAIA references) -- the "this is a produced brand piece"
 * cue, absent from UGC. Give it `text` and/or a logo image `src` (relative to
 * remotion/public/). Omit `atMs`/`durationMs` for the whole video.
 */
export const BrandBug: React.FC<{
  text?: string;
  src?: string;
  position?: "top-left" | "top-right";
  atMs?: number;
  durationMs?: number;
  height?: number;
}> = ({ text, src, position = "top-right", atMs = 0, durationMs, height = 44 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  const endMs = durationMs !== undefined ? atMs + durationMs : (durationInFrames / fps) * 1000;
  if (nowMs < atMs || nowMs > endMs) return null;
  const opacity = interpolate(nowMs, [atMs, atMs + 300, endMs - 300, endMs], [0, 0.95, 0.95, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const isLeft = position === "top-left";

  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: isLeft ? "flex-start" : "flex-end", opacity }}>
      <div
        style={{
          margin: "70px 48px 0 48px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          color: "#fff",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontWeight: 600,
          fontSize: height * 0.75,
          textShadow: "0 2px 10px rgba(0,0,0,0.6)",
        }}
      >
        {src ? <Img src={staticFile(src)} style={{ height, objectFit: "contain" }} /> : null}
        {text}
      </div>
    </AbsoluteFill>
  );
};
