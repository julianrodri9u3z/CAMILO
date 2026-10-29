import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Rating / counter card at the top of the safe zone: a dark rounded box with a short label and a big colored score
 * chip -- the "Magnesios 2 formas 4/10" / "Forte Max 10/10" cards of the winning "doctor rates from 1 to 10" ads,
 * and the "3/13" counter of the "13 questions" ones. Colors follow the color psychology rule: bad = red,
 * mid = orange, good = green (money/positive always green), neutral = brand yellow.
 */
const TONE: Record<string, string> = { bad: "#E53935", mid: "#F59E0B", good: "#16A34A", neutral: "#F5C400" };

export const ScoreCard: React.FC<{
  label?: string;
  score?: string;
  tone?: "bad" | "mid" | "good" | "neutral";
  durationMs: number;
  /** Top of the card in px at 1080x1920 (default 250: below the TikTok/Reels top UI). */
  y?: number;
}> = ({ label, score, tone = "neutral", durationMs, y = 250 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = Math.round((durationMs / 1000) * fps);
  const pop = spring({ frame, fps, config: { damping: 14, stiffness: 220, mass: 0.6 } });
  const out = interpolate(frame, [total - 6, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const scorePop = spring({ frame: frame - 5, fps, config: { damping: 9, stiffness: 260, mass: 0.5 } });
  const chipColor = TONE[tone] ?? TONE.neutral;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          marginTop: y,
          maxWidth: "86%",
          display: "flex",
          alignItems: "center",
          gap: 22,
          padding: "16px 22px 16px 30px",
          borderRadius: 22,
          backgroundColor: "rgba(12,16,28,0.88)",
          boxShadow: "0 8px 28px rgba(0,0,0,0.4)",
          transform: `translateY(${(1 - pop) * -40}px) scale(${0.9 + 0.1 * pop})`,
          opacity: Math.min(pop, out),
        }}
      >
        {label ? (
          <div
            style={{
              color: "#FFFFFF",
              fontFamily: "Montserrat, 'Arial Black', 'Helvetica Neue', sans-serif",
              fontWeight: 800,
              fontSize: 44,
              lineHeight: 1.15,
              textTransform: "uppercase",
              whiteSpace: "pre-line",
              ...({ textWrap: "balance" } as React.CSSProperties),
            }}
          >
            {label}
          </div>
        ) : null}
        {score ? (
          <div
            style={{
              flexShrink: 0,
              padding: "6px 22px",
              borderRadius: 16,
              backgroundColor: chipColor,
              color: tone === "neutral" ? "#000000" : "#FFFFFF",
              fontFamily: "Montserrat, 'Arial Black', sans-serif",
              fontWeight: 900,
              fontSize: 64,
              transform: `scale(${0.6 + 0.4 * Math.min(1.15, scorePop)})`,
            }}
          >
            {score}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
