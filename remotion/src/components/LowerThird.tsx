import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Name + credential tag for an interviewee/expert ("GREGG BRADEN / Geólogo y
 * autor de Best Sellers del New York Times") -- standard in the ADS GAIA
 * documentary trailers (7 references), absent from every UGC style. Slides in
 * from the left over a dark translucent bar with a thin accent line.
 */
export const LowerThird: React.FC<{
  name: string;
  subtitle?: string;
  atMs: number;
  durationMs: number;
  accent?: string;
  bottomPx?: number;
}> = ({ name, subtitle, atMs, durationMs, accent = "#C9A24B", bottomPx = 360 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const local = nowMs - atMs;
  const slide = interpolate(local, [0, 350], [-80, 0], { extrapolateRight: "clamp" });
  const opacity = interpolate(local, [0, 300, durationMs - 300, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", opacity }}>
      <div
        style={{
          marginLeft: 48,
          marginBottom: bottomPx,
          transform: `translateX(${slide}px)`,
          padding: "14px 26px 14px 22px",
          background: "linear-gradient(90deg, rgba(0,0,0,0.78), rgba(0,0,0,0.35))",
          borderLeft: `5px solid ${accent}`,
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
        }}
      >
        <div style={{ color: "#fff", fontWeight: 800, fontSize: 38, letterSpacing: 1, textTransform: "uppercase" }}>{name}</div>
        {subtitle ? <div style={{ color: accent, fontWeight: 500, fontSize: 28, marginTop: 4 }}>{subtitle}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
