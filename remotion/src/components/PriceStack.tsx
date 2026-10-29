import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * The value-stack / price-anchor graphic of a VSL: the lines of what the
 * viewer gets (or what the alternatives cost) revealed one by one, then the
 * total. Two layouts seen:
 *  - "panel": full-screen solid panel ("SEM MSD: APLICATIVO DE TREINO R$397 /
 *    COMUNIDADE R$397 / ... TOTAL R$991", Vida Sem Dieta, on burgundy);
 *  - "overlay": right-aligned list over the presenter ("R$500 + R$300 +
 *    R$1500", underline, "R$2.300" -- what they already spent).
 * `lines[].price` are strings so the currency/format stays the user's ("R$
 * 397,00", "$97"). `strikeTotal` draws a strike-through on the total (the
 * "was R$997" anchor). ALL prices/values must come from the real offer: never
 * invent an "original value" that was never charged.
 */
export const PriceStack: React.FC<{
  atMs: number;
  durationMs: number;
  title?: string;
  lines: { label: string; price: string }[];
  totalLabel?: string;
  total?: string;
  strikeTotal?: boolean;
  layout?: "panel" | "overlay";
  bg?: string;
  accent?: string;
  staggerMs?: number;
}> = ({ atMs, durationMs, title, lines, totalLabel = "TOTAL", total, strikeTotal = false, layout = "panel", bg = "#7A0A1E", accent = "#FFFFFF", staggerMs = 450 }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;
  const local = nowMs - atMs;
  const scale = Math.min(width, height) / 1080;
  const opacity = interpolate(local, [0, 250, durationMs - 250, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const row = (i: number, label: string, price: string, big = false) => {
    const t = interpolate(local - (i + 1) * staggerMs, [0, 250], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return (
      <div
        key={i}
        style={{
          display: "flex",
          justifyContent: layout === "panel" ? "space-between" : "flex-end",
          gap: 30 * scale,
          opacity: t,
          transform: `translateY(${(1 - t) * 18}px)`,
          fontSize: (big ? 52 : 40) * scale,
          fontWeight: big ? 900 : 600,
          fontStyle: layout === "panel" ? "italic" : "normal",
          marginTop: 10 * scale,
        }}
      >
        <span>{label}</span>
        <span style={{ fontWeight: 800 }}>{price}</span>
      </div>
    );
  };
  const totalT = interpolate(local - (lines.length + 1) * staggerMs, [0, 300], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const totalPop = spring({ frame: Math.max(0, Math.round(((local - (lines.length + 1) * staggerMs) / 1000) * fps)), fps, config: { damping: 11, stiffness: 200 } });

  const content = (
    <div style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: accent, width: layout === "panel" ? "84%" : "auto", textShadow: layout === "overlay" ? "0 3px 14px rgba(0,0,0,0.7)" : "none" }}>
      {title ? <div style={{ textAlign: layout === "panel" ? "center" : "right", fontWeight: 800, fontSize: 46 * scale, marginBottom: 18 * scale }}>{title}</div> : null}
      {lines.map((l, i) => row(i, l.label, l.price))}
      {total ? (
        <div
          style={{
            opacity: totalT,
            transform: `scale(${0.9 + totalPop * 0.1})`,
            transformOrigin: layout === "panel" ? "center" : "right center",
            marginTop: 22 * scale,
            paddingTop: 14 * scale,
            borderTop: `${5 * scale}px solid ${accent}`,
            display: "flex",
            justifyContent: layout === "panel" ? "space-between" : "flex-end",
            gap: 30 * scale,
            fontSize: 62 * scale,
            fontWeight: 900,
            textDecoration: strikeTotal ? "line-through" : "none",
            textDecorationThickness: 6 * scale,
          }}
        >
          <span>{totalLabel}</span>
          <span>{total}</span>
        </div>
      ) : null}
    </div>
  );

  if (layout === "panel") {
    return (
      <AbsoluteFill style={{ opacity, background: bg, justifyContent: "center", alignItems: "center" }}>
        {content}
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ opacity, justifyContent: "center", alignItems: "flex-end", paddingRight: 46 * scale }}>
      {content}
    </AbsoluteFill>
  );
};
