import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Full-frame kinetic text card used as a chapter break / punch line in VSLs:
 * "COMO SAIR", "TUDO", "CALMA" (white on red), "ACESSO DE 01 ANO" (white on
 * green), "DESATIVAR", "DIETAS TRADICIONAIS DESTROEM" over dimmed b-roll (Vida Sem
 * Dieta), "Is Where YOU Come In" in bold serif (UpLevel), italic-serif quotes
 * over black-and-white footage ("ABACATE TEM GORDURA", "NA SEGUNDA EU COMECO").
 *  - `bg`: solid color or CSS gradient. Omit + set `dim` (0-1) to darken the
 *    footage underneath instead of covering it.
 *  - `text`: `\n` breaks lines; each line pops in in sequence.
 *  - `look`: "sans" (default, heavy caps), "serif" (bold serif), "quote" (italic
 *    serif in quotation marks, lighter).
 * One short idea per card (1-4 words per line, 1-2.5s). More text than that is
 * a caption, not a card.
 */
export const TitleCard: React.FC<{
  text: string;
  atMs: number;
  durationMs: number;
  bg?: string;
  dim?: number;
  color?: string;
  look?: "sans" | "serif" | "quote";
  fontSize?: number;
  position?: "center" | "top" | "bottom";
}> = ({ text, atMs, durationMs, bg, dim, color = "#FFFFFF", look = "sans", fontSize, position = "center" }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const local = nowMs - atMs;
  const scale = Math.min(width, height) / 1080;
  const lines = text.split("\n");
  const size = (fontSize ?? (look === "quote" ? 84 : 132)) * scale;
  const fade = interpolate(local, [0, 120, durationMs - 200, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const family =
    look === "sans" ? "'Arial Black', 'Helvetica Neue', sans-serif" : "Georgia, 'Times New Roman', serif";

  return (
    <AbsoluteFill
      style={{
        opacity: fade,
        background: bg ?? (dim !== undefined ? `rgba(0,0,0,${dim})` : "transparent"),
        justifyContent: position === "top" ? "flex-start" : position === "bottom" ? "flex-end" : "center",
        alignItems: "center",
        padding: `${(position === "center" ? 0 : 220) * scale}px ${60 * scale}px`,
      }}
    >
      <div style={{ textAlign: "center", color, fontFamily: family, lineHeight: 1.02 }}>
        {lines.map((line, i) => {
          const p = spring({ frame: Math.max(0, Math.round(((local - i * 140) / 1000) * fps)), fps, config: { damping: 12, stiffness: 190, mass: 0.7 } });
          const shown = local >= i * 140;
          return (
            <div
              key={i}
              style={{
                fontSize: size,
                fontWeight: look === "quote" ? 400 : 900,
                fontStyle: look === "quote" ? "italic" : "normal",
                textTransform: look === "sans" ? "uppercase" : "none",
                letterSpacing: look === "sans" ? -1 : 0,
                transform: `scale(${shown ? 0.85 + p * 0.15 : 0.85})`,
                opacity: shown ? 1 : 0,
                textShadow: bg ? "none" : "0 6px 30px rgba(0,0,0,0.65)",
              }}
            >
              {look === "quote" ? `“${line}”` : line}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
