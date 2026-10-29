import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export type ListSidebarItem = { atMs: number; emoji?: string; src?: string; label?: string };

/**
 * A numbered list down the left edge (1, 2, 3 ...) whose slots fill with an
 * icon as each item is spoken -- the "8 ways to sell" sidebar in a real ADS
 * ELIDA reference (numbers stay, an app icon pops next to each number when
 * that item is named). `startMs`..`endMs` is how long the numbers are on
 * screen; each item's icon pops at its own `atMs`. Slots are numbered
 * 1..items.length in order.
 */
export const ListSidebar: React.FC<{
  items: ListSidebarItem[];
  startMs: number;
  endMs: number;
  x?: number;
  y?: number;
  gap?: number;
}> = ({ items, startMs, endMs, x = 30, y = 250, gap = 96 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < startMs || nowMs > endMs) return null;

  const fade = interpolate(nowMs, [startMs, startMs + 250, endMs - 250, endMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      {items.map((item, i) => {
        const shown = nowMs >= item.atMs;
        const local = frame - Math.round((item.atMs / 1000) * fps);
        const pop = shown ? spring({ frame: local, fps, config: { damping: 10, stiffness: 220 } }) : 0;
        return (
          <div key={i} style={{ position: "absolute", left: x, top: y + i * gap, display: "flex", alignItems: "center", gap: 14 }}>
            <span
              style={{
                fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
                fontWeight: 900,
                fontSize: 54,
                color: "#fff",
                WebkitTextStroke: "3px #000",
                paintOrder: "stroke fill",
                width: 44,
              }}
            >
              {i + 1}
            </span>
            <div style={{ transform: `scale(${pop})`, fontSize: 56, lineHeight: 1, width: 70, height: 70, display: "flex", alignItems: "center" }}>
              {item.src ? <Img src={staticFile(item.src)} style={{ width: 66, height: 66, objectFit: "contain" }} /> : item.emoji}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
