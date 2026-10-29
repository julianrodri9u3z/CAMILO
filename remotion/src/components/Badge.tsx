import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

const POSITION_STYLE: Record<string, React.CSSProperties> = {
  "top-left": { justifyContent: "flex-start", alignItems: "flex-start", padding: "140px 0 0 56px" },
  "top-right": { justifyContent: "flex-start", alignItems: "flex-end", padding: "140px 56px 0 0" },
  "bottom-left": { justifyContent: "flex-end", alignItems: "flex-start", padding: "0 0 340px 56px" },
  "bottom-right": { justifyContent: "flex-end", alignItems: "flex-end", padding: "0 56px 340px 0" },
};

/**
 * A small rounded pill label that pops onto a corner of the frame -- an offer/
 * bonus tag ("Tu primera venta"), a countdown chip, a small credential badge.
 * Grounded in a real reference (VSL FRANQUICIA IA): a purple rounded pill with
 * an icon sat near the top-left while a bonus was mentioned. Distinct from
 * StatCallout (center, huge, one proof number) and TitleBanner (persistent,
 * wide, boxed headline) -- this is small, corner-anchored, and transient.
 */
export const Badge: React.FC<{
  text: string;
  atMs: number;
  durationMs: number;
  position?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  bg?: string;
  color?: string;
  icon?: string;
}> = ({ text, atMs, durationMs, position = "top-left", bg = "#7C3AED", color = "#FFFFFF", icon }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const localFrame = frame - Math.round((atMs / 1000) * fps);
  const scale = spring({ frame: localFrame, fps, config: { damping: 12, stiffness: 200 } });
  const fadeOutStart = durationMs - 200;
  const opacity = interpolate(
    nowMs - atMs,
    [0, 1, fadeOutStart, durationMs],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ ...POSITION_STYLE[position], opacity }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "14px 22px",
          borderRadius: 999,
          backgroundColor: bg,
          color,
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontWeight: 700,
          fontSize: 30,
          transform: `scale(${scale})`,
          boxShadow: "0 6px 20px rgba(0,0,0,0.45)",
        }}
      >
        {icon ? <span style={{ fontSize: 34, lineHeight: 1 }}>{icon}</span> : null}
        {text}
      </div>
    </AbsoluteFill>
  );
};
