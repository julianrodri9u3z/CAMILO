import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * The buy/apply button that hovers over the presenter in a VSL ("Entrar ahora"
 * with animated chevrons in FRANQUICIA IA, "Apply For UpLevel Consulting ->" in
 * UpLevel). In real VSLs it is NOT shown once: FRANQUICIA IA re-launches it at
 * ~21:20, 28:16, 31:15 and 31:35 (four times in the last third), because the
 * page's real button is what converts and the overlay reminds the viewer it is
 * below. Use several entries in `ctaButtons`, one per CTA moment in the script.
 * Purely visual -- the real, clickable button lives on the page that hosts the
 * video; never imply the overlay itself is clickable.
 * `y` is the vertical CENTER in the 1080x1920 reference frame (or the equivalent
 * fraction of a 16:9 frame: pass y in the actual composition's pixels).
 */
export const CtaButton: React.FC<{
  text: string;
  atMs: number;
  durationMs: number;
  y?: number;
  color?: string;
  textColor?: string;
  chevrons?: boolean;
  chevronColor?: string;
}> = ({ text, atMs, durationMs, y, color = "#4ADE80", textColor = "#0B3D1E", chevrons = true, chevronColor = "#A855F7" }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;

  const local = frame - Math.round((atMs / 1000) * fps);
  const pop = spring({ frame: local, fps, config: { damping: 12, stiffness: 190 } });
  const pulse = 1 + Math.sin((nowMs / 900) * Math.PI * 2) * 0.03;
  const bounce = Math.sin((nowMs / 500) * Math.PI * 2) * 8;
  const opacity = interpolate(nowMs - atMs, [0, 200, durationMs - 250, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fontSize = Math.round(Math.max(height * 0.024, width * 0.03));
  const chev = (dir: 1 | -1) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `translateY(${bounce * dir}px)` }}>
      {[0, 1].map((i) => (
        <svg key={i} width={fontSize * 1.6} height={fontSize * 0.9} viewBox="0 0 40 22" style={{ marginTop: i ? -fontSize * 0.35 : 0 }}>
          <path d="M4 3 L20 18 L36 3" fill="none" stroke={chevronColor} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ))}
    </div>
  );

  return (
    <AbsoluteFill style={{ opacity, justifyContent: "flex-start", alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: (y ?? height * 0.84) - fontSize * 2,
          display: "flex",
          alignItems: "center",
          gap: fontSize * 0.9,
          transform: `scale(${pop * pulse})`,
        }}
      >
        {chevrons ? chev(1) : null}
        <div
          style={{
            background: color,
            color: textColor,
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            fontWeight: 800,
            fontSize,
            padding: `${fontSize * 0.55}px ${fontSize * 1.8}px`,
            borderRadius: fontSize * 0.7,
            boxShadow: `0 8px 26px rgba(0,0,0,0.45), 0 0 0 3px ${color}66`,
            whiteSpace: "nowrap",
          }}
        >
          {text}
        </div>
        {chevrons ? chev(-1) : null}
      </div>
    </AbsoluteFill>
  );
};
