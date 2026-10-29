import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A logo/emoji/icon that pops in near the speaker in sync with a word -- the
 * WhatsApp/TikTok-Shop/Shopee/rocket/cart icons in the ADS ELIDA references
 * (real affiliate-marketing UGC, 2026-09 scouting pass). Give it an `emoji`
 * OR an image `src` (relative to remotion/public/, e.g. a brand logo PNG/SVG
 * the user provided). `x`/`y` is the CENTER in the 1080x1920 reference frame.
 * Two stickers side by side with an "x" text between them make the "A x B"
 * comparison header seen in the same references -- no separate component.
 */
export const Sticker: React.FC<{
  atMs: number;
  durationMs: number;
  x: number;
  y: number;
  emoji?: string;
  src?: string;
  size?: number;
  rotate?: number;
}> = ({ atMs, durationMs, x, y, emoji, src, size = 200, rotate = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const localFrame = frame - Math.round((atMs / 1000) * fps);
  const scale = spring({ frame: localFrame, fps, config: { damping: 9, stiffness: 230, mass: 0.6 } });
  const wobble = interpolate(localFrame, [0, 6, 12], [-8, 6, 0], { extrapolateRight: "clamp" });
  const opacity = interpolate(nowMs - atMs, [0, 1, durationMs - 180, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      <div
        style={{
          position: "absolute",
          left: x - size / 2,
          top: y - size / 2,
          width: size,
          height: size,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: size * 0.8,
          lineHeight: 1,
          transform: `scale(${scale}) rotate(${rotate + wobble}deg)`,
          filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.45))",
        }}
      >
        {src ? <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "contain" }} /> : emoji}
      </div>
    </AbsoluteFill>
  );
};
