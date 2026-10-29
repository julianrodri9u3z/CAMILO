import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * The Instagram "question sticker" (black header pill + white rounded body
 * with the question) pinned on screen -- persistent through most of a
 * reel in two of the loose references (the "Hazme una pregunta" box). It's a
 * hook device: the video "answers" the question shown. `atMs`/`durationMs`
 * are optional -- omit both to keep it on screen for the whole video.
 * `x`/`y` is the CENTER in the 1080x1920 frame.
 */
export const QuestionSticker: React.FC<{
  text: string;
  header?: string;
  atMs?: number;
  durationMs?: number;
  x?: number;
  y?: number;
  width?: number;
}> = ({ text, header = "Hazme una pregunta", atMs = 0, durationMs, x = 540, y = 1180, width = 520 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  const endMs = durationMs !== undefined ? atMs + durationMs : (durationInFrames / fps) * 1000;
  if (nowMs < atMs || nowMs > endMs) return null;

  const local = frame - Math.round((atMs / 1000) * fps);
  const pop = spring({ frame: local, fps, config: { damping: 12, stiffness: 200 } });
  const opacity = interpolate(nowMs, [atMs, atMs + 1, endMs - 200, endMs], [0, 1, 1, 0], {
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
          transform: `translateY(-50%) scale(${pop})`,
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          filter: "drop-shadow(0 6px 14px rgba(0,0,0,0.35))",
        }}
      >
        <div style={{ background: "#111", color: "#fff", fontWeight: 700, fontSize: 30, textAlign: "center", padding: "14px 20px", borderRadius: "22px 22px 0 0" }}>
          {header}
        </div>
        <div style={{ background: "#fff", color: "#111", fontWeight: 700, fontSize: 36, lineHeight: 1.2, textAlign: "center", padding: "22px 26px", borderRadius: "0 0 22px 22px" }}>
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
