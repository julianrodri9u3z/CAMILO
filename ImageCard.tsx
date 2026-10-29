import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A screenshot/proof image pinned on screen as a floating card -- the
 * payment-notification lockscreens, Kiwify/Nubank transfers and sales
 * dashboards used as proof in the ADS ELIDA references (and the "Dashboard /
 * Total faturado" card in the same set). `src` is relative to
 * remotion/public/. `x`/`y` is the card CENTER in the 1080x1920 frame,
 * `width` its width in px (height follows the image's aspect ratio).
 * Never fabricate proof: only use screenshots the user actually provides.
 */
export const ImageCard: React.FC<{
  src: string;
  atMs: number;
  durationMs: number;
  x: number;
  y: number;
  width?: number;
  rotate?: number;
}> = ({ src, atMs, durationMs, x, y, width = 520, rotate = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const local = frame - Math.round((atMs / 1000) * fps);
  const pop = spring({ frame: local, fps, config: { damping: 13, stiffness: 170 } });
  const opacity = interpolate(nowMs - atMs, [0, 1, durationMs - 200, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      <div
        style={{
          position: "absolute",
          left: x - width / 2,
          top: y,
          width,
          transform: `translateY(-50%) scale(${0.85 + pop * 0.15}) rotate(${rotate}deg)`,
          transformOrigin: "center",
          borderRadius: 18,
          overflow: "hidden",
          boxShadow: "0 14px 34px rgba(0,0,0,0.5)",
          backgroundColor: "#fff",
        }}
      >
        <Img src={staticFile(src)} style={{ width: "100%", display: "block" }} />
      </div>
    </AbsoluteFill>
  );
};
