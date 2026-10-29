import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

const fmt = (totalSeconds: number, withHours: boolean) => {
  const s = Math.max(0, Math.ceil(totalSeconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return withHours ? `${pad(h)}:${pad(m)}:${pad(sec)}` : `${pad(m + h * 60)}:${pad(sec)}`;
};

/**
 * A real, decreasing timer running through the closing section of a VSL. Two
 * looks seen in the references:
 *  - "bar": full-width red strip at the top with the label on the left and the
 *    digits on the right ("OFERTA POR TIEMPO LIMITADO 00:09:50", Vida Sem Dieta,
 *    shown for the whole checkout/close, ~1:40 real time compressed to 10:00);
 *  - "corner": bold digits in the top-right corner (FRANQUICIA IA: a 15-minute
 *    timer that starts at ~21:20 of the video and is visible until the end).
 * `fromSeconds` is the value shown at `startMs`; it counts down in real time
 * and stops at 00:00. IMPORTANT (honesty): a timer that promises "the offer
 * ends at 00:00" must correspond to a real deadline on the sales page -- only
 * use it if the offer really changes when it hits zero.
 */
export const CountdownTimer: React.FC<{
  startMs: number;
  endMs: number;
  fromSeconds: number;
  label?: string;
  style?: "bar" | "corner";
  withHours?: boolean;
  color?: string;
}> = ({ startMs, endMs, fromSeconds, label = "OFERTA POR TIEMPO LIMITADO", style = "corner", withHours = false, color }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < startMs || nowMs > endMs) return null;

  const remaining = fromSeconds - (nowMs - startMs) / 1000;
  const opacity = interpolate(nowMs, [startMs, startMs + 300, endMs - 300, endMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const urgent = remaining < 60;
  const scale = Math.min(width, height) / 1080;

  if (style === "bar") {
    return (
      <AbsoluteFill style={{ opacity, justifyContent: "flex-start" }}>
        <div
          style={{
            background: color ?? "#C81E2B",
            color: "#fff",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: `${18 * scale}px ${34 * scale}px`,
            fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
            fontWeight: 900,
            fontSize: 30 * scale,
            letterSpacing: 1,
          }}
        >
          <span>{label}</span>
          <span style={{ fontVariantNumeric: "tabular-nums", fontSize: 38 * scale }}>{fmt(remaining, true)}</span>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ opacity, justifyContent: "flex-start", alignItems: "flex-end" }}>
      <div
        style={{
          margin: `${40 * scale}px ${44 * scale}px 0 0`,
          color: color ?? (urgent ? "#FF4D4D" : "#FFFFFF"),
          fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
          fontWeight: 900,
          fontSize: 44 * scale,
          fontVariantNumeric: "tabular-nums",
          textShadow: "0 3px 12px rgba(0,0,0,0.75)",
        }}
      >
        {fmt(remaining, withHours)}
      </div>
    </AbsoluteFill>
  );
};
