import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

const TONE: Record<string, string> = { good: "#22C55E", mid: "#EAB308", bad: "#EF4444", neutral: "#6B7280" };

/**
 * A comparison table ("Franquicia IA vs Otros negocios": rows = business models,
 * columns = price / potential / profitability / time, cells colored green /
 * yellow / red) revealed row by row -- FRANQUICIA IA at ~26:17. Cells are
 * `{ text, tone? }`; tone: "good" | "mid" | "bad" | "neutral". First row of
 * `rows` may be the highlighted own option (`highlightFirst`). Every comparison
 * must be honest and defensible: the claims are the user's, confirm them.
 */
export const ComparisonTable: React.FC<{
  atMs: number;
  durationMs: number;
  title?: string;
  columns: string[];
  rows: { label: string; cells: { text: string; tone?: keyof typeof TONE }[] }[];
  highlightFirst?: boolean;
  staggerMs?: number;
}> = ({ atMs, durationMs, title, columns, rows, highlightFirst = true, staggerMs = 650 }) => {
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

  return (
    <AbsoluteFill style={{ opacity, background: "rgba(6,6,14,0.94)", justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: "92%", fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#fff" }}>
        {title ? <div style={{ fontSize: 50 * scale, fontWeight: 800, textAlign: "center", marginBottom: 28 * scale }}>{title}</div> : null}
        <div style={{ display: "grid", gridTemplateColumns: `1.4fr ${columns.map(() => "1fr").join(" ")}`, gap: 8 * scale, fontSize: 28 * scale }}>
          <div />
          {columns.map((c, i) => (
            <div key={i} style={{ textAlign: "center", fontWeight: 800, background: "#5B21B6", padding: `${12 * scale}px ${6 * scale}px`, borderRadius: 8 * scale }}>{c}</div>
          ))}
          {rows.map((r, ri) => {
            const t = interpolate(local - (ri + 1) * staggerMs, [0, 250], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const own = highlightFirst && ri === 0;
            return (
              <React.Fragment key={ri}>
                <div style={{ opacity: t, fontWeight: 800, padding: `${16 * scale}px ${10 * scale}px`, background: own ? "#7C3AED" : "#1F1F2E", borderRadius: 8 * scale, fontSize: 30 * scale }}>{r.label}</div>
                {r.cells.map((c, ci) => (
                  <div
                    key={ci}
                    style={{
                      opacity: t,
                      textAlign: "center",
                      fontWeight: 700,
                      padding: `${16 * scale}px ${6 * scale}px`,
                      borderRadius: 8 * scale,
                      background: TONE[c.tone ?? "neutral"],
                      color: c.tone === "mid" ? "#1F1A00" : "#fff",
                    }}
                  >
                    {c.text}
                  </div>
                ))}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
