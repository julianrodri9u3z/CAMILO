import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A big, bold proof/stat number punched onto the screen -- "$10,000", "30%",
 * "+10,000 alumnos". Grounded directly in real reference footage (2026-09
 * scouting pass over the user's ~/Documents/ESTILOS DE EDICIÓN ADS folder):
 * both a UGC "day in the life" ad (JUAN CARRIZO) and a business VSL
 * (FRANQUICIA IA) lean hard on a single huge stat slammed onto the frame,
 * distinct from KeywordCallout (a THEME word, smaller, top-of-frame, no
 * punch) and from the running word captions (spoken dialogue, not a proof
 * point). Center-of-frame by default because that's where the eye already is
 * when a number needs to land.
 *
 * `countFrom`/`countTo` optionally animate a numeric count-up (money/results
 * ticking up) instead of a static number appearing -- use this for a dollar
 * amount or percentage that's meant to feel like it's climbing in real time;
 * leave both unset for a plain punch-in (e.g. non-numeric text stats).
 */
export const StatCallout: React.FC<{
  text: string;
  atMs: number;
  durationMs: number;
  countFrom?: number;
  countTo?: number;
  prefix?: string;
  suffix?: string;
  color?: string;
  /** Optional CENTER position in the composition (default: dead center). */
  x?: number;
  y?: number;
  /** Font size in px at 1080 wide (default 108). */
  size?: number;
  /** Neon glow around the digits -- the green money labels of FRANQUICIA IA / ELIDA. */
  glow?: boolean;
}> = ({ text, atMs, durationMs, countFrom, countTo, prefix = "", suffix = "", color = "#39FF6A", x, y, size = 108, glow = false }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const localFrame = frame - Math.round((atMs / 1000) * fps);
  const scale = spring({ frame: localFrame, fps, config: { damping: 11, stiffness: 210, mass: 0.6 } });
  const fadeOutStart = durationMs - 250;
  const opacity = interpolate(
    nowMs - atMs,
    [0, 1, fadeOutStart, durationMs],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const isCounting = countFrom !== undefined && countTo !== undefined;
  let display = text;
  if (isCounting) {
    // Counts up over the first ~60% of the callout's life, then holds --
    // matches the "climbing" feel without racing past the eye before it reads.
    const countDurationMs = durationMs * 0.6;
    const raw = interpolate(nowMs - atMs, [0, countDurationMs], [countFrom!, countTo!], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const rounded = Number.isInteger(countTo) ? Math.round(raw) : Math.round(raw * 100) / 100;
    display = `${prefix}${rounded.toLocaleString("es-CO")}${suffix}`;
  }

  return (
    <AbsoluteFill style={{ justifyContent: x === undefined && y === undefined ? "center" : "flex-start", alignItems: x === undefined && y === undefined ? "center" : "flex-start", opacity }}>
      <div
        style={{
          fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
          fontWeight: 900,
          fontSize: size * (Math.min(width, height) / 1080),
          color,
          whiteSpace: "nowrap",
          position: x === undefined && y === undefined ? "static" : "absolute",
          left: x,
          top: y,
          transform: x === undefined && y === undefined ? `scale(${scale})` : `translate(-50%, -50%) scale(${scale})`,
          textShadow: glow
            ? `0 0 14px ${color}, 0 0 36px ${color}AA, 0 6px 0 rgba(0,0,0,0.5)`
            : "0 6px 0 rgba(0,0,0,0.5), 0 10px 40px rgba(0,0,0,0.6)",
          WebkitTextStroke: "3px rgba(0,0,0,0.55)",
          paintOrder: "stroke fill",
        }}
      >
        {display}
      </div>
    </AbsoluteFill>
  );
};
