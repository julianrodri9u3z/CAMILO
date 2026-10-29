import React from "react";
import { AbsoluteFill, Img, interpolate, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A circular picture-in-picture bubble (a testimonial face, a reaction shot,
 * a phone-call inset) -- seen in a loose reference as a round cutout of a
 * client/other person appearing over the main speaker while they're
 * mentioned. `src` is an image or video (.mp4/.mov/.webm) relative to
 * remotion/public/; videos play muted from their start. `x`/`y` is the
 * CENTER of the circle in the 1080x1920 frame.
 */
export const Bubble: React.FC<{
  src: string;
  atMs: number;
  durationMs: number;
  x: number;
  y: number;
  size?: number;
  borderColor?: string;
}> = ({ src, atMs, durationMs, x, y, size = 300, borderColor = "#FFFFFF" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const local = frame - Math.round((atMs / 1000) * fps);
  const pop = spring({ frame: local, fps, config: { damping: 12, stiffness: 210 } });
  const opacity = interpolate(nowMs - atMs, [0, 1, durationMs - 200, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const isVideo = /\.(mp4|mov|webm)$/i.test(src);

  return (
    <AbsoluteFill style={{ opacity }}>
      <div
        style={{
          position: "absolute",
          left: x - size / 2,
          top: y - size / 2,
          width: size,
          height: size,
          borderRadius: "50%",
          overflow: "hidden",
          border: `6px solid ${borderColor}`,
          boxShadow: "0 10px 28px rgba(0,0,0,0.5)",
          transform: `scale(${pop})`,
        }}
      >
        {isVideo ? (
          <OffthreadVideo muted src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        )}
      </div>
    </AbsoluteFill>
  );
};
