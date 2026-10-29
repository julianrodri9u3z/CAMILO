import React from "react";
import { AbsoluteFill } from "remotion";

/**
 * Title/hook banner -- covers two looks seen in real references:
 * (1) the "POV: ..." TikTok UGC style: white rounded box, black text, near
 *     the top, persistent for the whole video.
 * (2) an opening title-card style seen in a podcast-format reference ("LOS 7
 *     ARCÁNGELES DE DIOS"): black rounded box, white text, lower-third,
 *     shown only for the first few seconds.
 * `position`/`bg` pick between these two looks; default matches (1) for
 * backward compatibility with jobs that don't set them.
 */
export const TitleBanner: React.FC<{
  text: string;
  position?: "top" | "lower" | "topEdge";
  bg?: "white" | "black" | "none";
  color?: string;
  /** Exact distance from the top (px at 1080x1920), overriding `position` -- to keep the title off the face. */
  topPx?: number;
}> = ({ text, position: pos = "top", bg = "white", color, topPx }) => {
  const position = topPx !== undefined ? "top" : pos;
  const isLower = position === "lower";
  const top = topPx ?? 540;
  const isBlack = bg === "black";

  if (bg === "none") {
    // Unboxed "POV: ..." line pinned to the very top: small bold text, no
    // background, shadow for legibility -- the title of the ADS ELIDA UGC
    // references (white in the kitchen/affiliate ones, yellow in the car skits).
    return (
      <AbsoluteFill style={{ justifyContent: isLower ? "flex-end" : "flex-start", alignItems: "center" }}>
        <div
          style={{
            marginTop: position === "topEdge" ? 90 : isLower ? 0 : top,
            marginBottom: isLower ? 420 : 0,
            maxWidth: "90%",
            textAlign: "center",
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            fontWeight: 700,
            fontSize: 38,
            lineHeight: 1.15,
            color: color ?? "#FFFFFF",
            whiteSpace: "pre-line",
            textShadow: "0 2px 10px rgba(0,0,0,0.85), 0 0 3px rgba(0,0,0,0.9)",
          }}
        >
          {text}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: isLower ? "flex-end" : "flex-start",
        alignItems: "center",
      }}
    >
      <div
        style={{
          // "top": sits just above the subject's head (calibrated against a
          // typical selfie/talking-head framing). "lower": sits in the same
          // rough band as word captions, matching the podcast-reference title
          // card's position.
          marginTop: isLower ? 0 : position === "topEdge" ? 90 : top,
          marginBottom: isLower ? 420 : 0,
          maxWidth: "88%",
          padding: "16px 28px",
          borderRadius: 14,
          backgroundColor: isBlack ? "#000000" : "#FFFFFF",
          color: color ?? (isBlack ? "#FFFFFF" : "#000000"),
          textAlign: "center",
          fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
          fontWeight: 900,
          fontSize: 40,
          lineHeight: 1.15,
          textTransform: isBlack ? "none" : "uppercase",
          whiteSpace: "pre-line",
          boxShadow: "0 4px 16px rgba(0,0,0,0.35)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
