import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Big all-caps keyword flashed briefly near the top of frame to emphasize a
 * theme word (e.g. "PROTECTOR", "CLARIDAD") -- seen in a real podcast-format
 * reference ("Los 7 arcángeles de Dios"), one per archangel. Distinct from
 * the running word-by-word Captions (those track actual spoken dialogue;
 * this is a separate emphasis layer, not tied 1:1 to a spoken word) and from
 * TitleBanner (persistent/boxed; this is a plain, ephemeral flash).
 */
export const KeywordCallout: React.FC<{
  text: string;
  atMs: number;
  durationMs: number;
}> = ({ text, atMs, durationMs }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const localMs = nowMs - atMs;
  const fadeMs = 200;
  const opacity = interpolate(
    localMs,
    [0, fadeMs, durationMs - fadeMs, durationMs],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const translateY = interpolate(localMs, [0, fadeMs], [10, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          marginTop: 160,
          padding: "0 40px",
          textAlign: "center",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontWeight: 800,
          fontSize: 52,
          textTransform: "uppercase",
          color: "#FFFFFF",
          opacity,
          transform: `translateY(${translateY}px)`,
          textShadow: "0 3px 20px rgba(0,0,0,0.7)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
