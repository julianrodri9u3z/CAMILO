import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";

/**
 * An animated line/area chart that draws itself left to right with a glowing
 * dot chasing the line and a floating counter box showing the current value
 * -- the "proof of results" shot common in business/money VSLs. Grounded
 * directly in a real reference (VSL FRANQUICIA IA): a green revenue line
 * graph with a big glowing "$2.883" counter box tracking the line's current
 * point. Purpose-built rather than assembled from a charting library -- the
 * whole point is the hand-drawn-feeling reveal + counter sync, which a
 * generic chart component doesn't give for free.
 *
 * `points` is any list of values (not normalized) -- e.g. daily revenue over
 * the period shown. Chart box is centered at `x`/`y` (in the reference
 * 1080x1920 frame) with the given `width`/`height`.
 */
export const RevenueChart: React.FC<{
  atMs: number;
  durationMs: number;
  points: number[];
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  color?: string;
  counterPrefix?: string;
  counterSuffix?: string;
  label?: string;
}> = ({
  atMs,
  durationMs,
  points,
  x = 540,
  y = 700,
  width = 820,
  height = 360,
  color = "#39FF6A",
  counterPrefix = "$",
  counterSuffix = "",
  label,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  const { path, coords } = useMemo(() => {
    const min = Math.min(...points);
    const max = Math.max(...points);
    const span = max - min || 1;
    const coords = points.map((v, i) => ({
      px: (i / (points.length - 1 || 1)) * width,
      py: height - ((v - min) / span) * height,
    }));
    const path = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.px.toFixed(2)} ${c.py.toFixed(2)}`).join(" ");
    return { path, coords };
  }, [points, width, height]);

  if (nowMs < atMs || nowMs > atMs + durationMs || points.length < 2) return null;

  const localMs = nowMs - atMs;
  const drawMs = Math.max(600, durationMs - 400);
  const progress = interpolate(localMs, [0, drawMs], [0, 1], { extrapolateRight: "clamp" });
  const fadeOutStart = durationMs - 200;
  const opacity = interpolate(
    localMs,
    [0, 1, fadeOutStart, durationMs],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const { strokeDasharray, strokeDashoffset } = evolvePath(progress, path);

  // Where along the polyline `progress` currently sits, for the dot + counter.
  const totalSegs = coords.length - 1;
  const segPos = progress * totalSegs;
  const segIndex = Math.min(totalSegs - 1, Math.floor(segPos));
  const segT = segPos - segIndex;
  const a = coords[segIndex];
  const b = coords[segIndex + 1] ?? a;
  const dotX = a.px + (b.px - a.px) * segT;
  const dotY = a.py + (b.py - a.py) * segT;
  const currentValue = points[segIndex] + (points[segIndex + 1] - points[segIndex]) * segT;

  return (
    <AbsoluteFill style={{ opacity }}>
      <div style={{ position: "absolute", left: x - width / 2, top: y - height / 2, width, height }}>
        <svg width={width} height={height} style={{ overflow: "visible" }}>
          <path
            d={path}
            fill="none"
            stroke={color}
            strokeWidth={7}
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ strokeDasharray, strokeDashoffset, filter: `drop-shadow(0 0 10px ${color}99)` }}
          />
          <circle cx={dotX} cy={dotY} r={11} fill={color} style={{ filter: `drop-shadow(0 0 12px ${color})` }} />
        </svg>
        <div
          style={{
            position: "absolute",
            left: dotX + 26,
            top: Math.max(0, dotY - 70),
            transform: dotX > width - 220 ? "translateX(-100%)" : "none",
            padding: "10px 18px",
            borderRadius: 10,
            backgroundColor: "rgba(0,0,0,0.72)",
            border: `2px solid ${color}`,
            color,
            fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
            fontWeight: 900,
            fontSize: 38,
            whiteSpace: "nowrap",
            textShadow: `0 0 16px ${color}`,
          }}
        >
          {counterPrefix}
          {currentValue.toLocaleString("es-CO", { maximumFractionDigits: 0 })}
          {counterSuffix}
        </div>
        {label ? (
          <div
            style={{
              position: "absolute",
              left: 0,
              bottom: -46,
              color: "#DDDDDD",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontWeight: 600,
              fontSize: 26,
              textShadow: "0 2px 8px rgba(0,0,0,0.7)",
            }}
          >
            {label}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
