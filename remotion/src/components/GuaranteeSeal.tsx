import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";

/**
 * Risk-reversal badge: "07 DIAS DE GARANTIA" over a checkmark that draws itself
 * (Vida Sem Dieta: dark card + glowing check + "Voce pode experimentar") or a gold
 * seal ("6 DIAS GARANTIA", FRANQUICIA IA). `big` is the headline ("07 DIAS"),
 * `small` the line under it ("DE GARANTIA"). Use only with a guarantee that
 * really exists in the offer and with its real length.
 */
export const GuaranteeSeal: React.FC<{
  atMs: number;
  durationMs: number;
  big: string;
  small?: string;
  caption?: string;
  look?: "dark" | "gold";
}> = ({ atMs, durationMs, big, small = "DE GARANTIA", caption, look = "dark" }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  const checkPath = "M 20 70 L 52 102 L 112 30";
  const memo = useMemo(() => checkPath, []);
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const local = nowMs - atMs;
  const scale = Math.min(width, height) / 1080;
  const pop = spring({ frame: Math.round((local / 1000) * fps), fps, config: { damping: 12, stiffness: 170 } });
  const draw = interpolate(local, [300, 900], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const { strokeDasharray, strokeDashoffset } = evolvePath(draw, memo);
  const opacity = interpolate(local, [0, 200, durationMs - 250, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const gold = look === "gold";

  return (
    <AbsoluteFill style={{ opacity, justifyContent: "center", alignItems: "center", background: gold ? "transparent" : "rgba(8,8,8,0.86)" }}>
      <div style={{ transform: `scale(${pop})`, textAlign: "center", fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
        {gold ? (
          <div
            style={{
              width: 520 * scale, height: 520 * scale, borderRadius: "50%",
              background: "radial-gradient(circle at 35% 30%, #FFE28A, #D9A21B 60%, #A8730B)",
              border: `${14 * scale}px solid #F6C744`, boxShadow: "0 18px 50px rgba(0,0,0,0.55)",
              display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", color: "#5A3A00",
            }}
          >
            <div style={{ fontSize: 150 * scale, fontWeight: 900, lineHeight: 1 }}>{big}</div>
            <div style={{ fontSize: 56 * scale, fontWeight: 900 }}>{small}</div>
          </div>
        ) : (
          <>
            <div style={{ color: "#fff", fontStyle: "italic", fontFamily: "Georgia, serif", fontSize: 120 * scale, fontWeight: 700 }}>{big}</div>
            <div style={{ color: "#DDD", fontSize: 44 * scale, letterSpacing: 4 }}>{small}</div>
            <svg width={340 * scale} height={260 * scale} viewBox="0 0 132 120" style={{ marginTop: 18 * scale, filter: "drop-shadow(0 0 16px rgba(255,255,255,0.7))" }}>
              <path d={checkPath} fill="none" stroke="#fff" strokeWidth={13} strokeLinecap="round" strokeLinejoin="round" style={{ strokeDasharray, strokeDashoffset }} />
            </svg>
          </>
        )}
        {caption ? <div style={{ color: "#fff", fontSize: 46 * scale, fontWeight: 700, marginTop: 24 * scale }}>{caption}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
