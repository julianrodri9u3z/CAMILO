import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Ellipse, makeEllipse } from "@remotion/shapes";
import { evolvePath } from "@remotion/paths";

/**
 * A hand-drawn-marker-style circle/ellipse that draws itself on around a
 * region of the frame -- circling a word, a face, a UI element on a
 * screenshot. Uses @remotion/shapes (already an installed dependency, unused
 * until now) for the ellipse path and @remotion/paths' evolvePath for the
 * stroke-draw-on animation, rather than hand-rolling SVG path math.
 *
 * `x`/`y` are the CENTER of the circle in the reference 1080x1920 frame;
 * `width`/`height` are the full bounding box (not radius) so it's easy to
 * eyeball straight from a paused frame of the source video.
 */
export const HighlightCircle: React.FC<{
  atMs: number;
  durationMs: number;
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  strokeWidth?: number;
}> = ({ atMs, durationMs, x, y, width, height, color = "#FF3B30", strokeWidth = 10 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  const rx = width / 2;
  const ry = height / 2;
  const { path } = useMemo(() => makeEllipse({ rx, ry }), [rx, ry]);

  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const localMs = nowMs - atMs;
  const drawMs = Math.min(500, durationMs * 0.5); // draw-on takes at most half the callout's life
  const drawProgress = interpolate(localMs, [0, drawMs], [0, 1], { extrapolateRight: "clamp" });
  const fadeOutStart = durationMs - 200;
  const opacity = interpolate(
    localMs,
    [0, 1, fadeOutStart, durationMs],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const { strokeDasharray, strokeDashoffset } = evolvePath(drawProgress, path);

  return (
    <AbsoluteFill style={{ opacity }}>
      <div style={{ position: "absolute", left: x - rx, top: y - ry, width, height }}>
        <Ellipse
          rx={rx}
          ry={ry}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}
          pathStyle={{ strokeDasharray, strokeDashoffset, filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.5))" }}
        />
      </div>
    </AbsoluteFill>
  );
};
