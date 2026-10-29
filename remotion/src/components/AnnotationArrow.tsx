import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Arrow } from "@remotion/shapes";

/**
 * A pointer arrow that pops in with a small bounce and gently pulses, aimed
 * at something on screen -- a UI element on a screenshot insert, a price, a
 * face. Uses @remotion/shapes' Arrow (already an installed dependency).
 * A solid filled shape reads better with a scale/bounce entrance than a
 * stroke draw-on (which HighlightCircle uses instead, appropriate for an
 * outline shape, not a filled one).
 *
 * `x`/`y` is the TIP of the arrow (the pointed end, where attention should
 * land) in the reference 1080x1920 frame -- easier to eyeball against a
 * screenshot than the tail.
 */
export const AnnotationArrow: React.FC<{
  atMs: number;
  durationMs: number;
  x: number;
  y: number;
  direction?: "up" | "down" | "left" | "right";
  length?: number;
  color?: string;
}> = ({ atMs, durationMs, x, y, direction = "up", length = 140, color = "#FFD400" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const localFrame = frame - Math.round((atMs / 1000) * fps);
  const localMs = nowMs - atMs;
  const pop = spring({ frame: localFrame, fps, config: { damping: 10, stiffness: 220 } });
  // Subtle continuous pulse after the entrance so it keeps drawing the eye
  // without being distracting -- +/-6% scale, ~1.2s cycle.
  const pulse = 1 + Math.sin((localMs / 1200) * Math.PI * 2) * 0.06;
  const scale = pop * (localMs < 400 ? 1 : pulse);
  const fadeOutStart = durationMs - 200;
  const opacity = interpolate(
    localMs,
    [0, 1, fadeOutStart, durationMs],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Offset so (x, y) lands on the TIP regardless of direction, since Arrow
  // itself is drawn from its shaft origin along `direction`.
  const offset =
    direction === "up" ? { left: x - 40, top: y }
    : direction === "down" ? { left: x - 40, top: y - length }
    : direction === "left" ? { left: x, top: y - 40 }
    : { left: x - length, top: y - 40 };

  return (
    <AbsoluteFill style={{ opacity }}>
      <div style={{ position: "absolute", ...offset, transform: `scale(${scale})`, transformOrigin: "center" }}>
        <Arrow
          length={length}
          direction={direction}
          headWidth={70}
          headLength={44}
          shaftWidth={26}
          cornerRadius={4}
          fill={color}
          style={{ filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.55))" }}
        />
      </div>
    </AbsoluteFill>
  );
};
