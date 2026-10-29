import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import type { Grade, Pulse } from "../EditPlan";

/**
 * One consistent look over ALL the picture layers (main footage + b-roll) so stock/TikTok
 * inserts stop reading as "pasted in": the same contrast/saturation curve, the same warm/cool
 * cast, lifted (filmic) blacks and a touch of animated grain. Overlays and captions are drawn
 * ABOVE this layer in Edit.tsx and stay untouched.
 *
 * Everything is a plain CSS filter / blend overlay (no WebGL), so it renders the same in
 * headless Chrome. Defaults are neutral (no-op). Typical subtle "premium" look:
 *   { contrast: 1.06, saturation: 1.05, temperature: 0.15, fade: 0.04, grain: 0.18 }
 * Keep every value mild -- a visible grade is a defect, a felt one is polish.
 */
export const GradeLayer: React.FC<{ grade?: Grade; pulses?: Pulse[]; children: React.ReactNode }> = ({ grade, pulses, children }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  // Beat pulses: sum of decaying envelopes of the pulses that fired in the last ~1.2 s.
  let pulseScale = 1;
  let flash = 0;
  let shakeX = 0;
  let shakeY = 0;
  for (const p of pulses ?? []) {
    const dt = nowMs - p.atMs;
    if (dt < 0 || dt > 1200) continue;
    const env = Math.exp(-dt / (p.decayMs ?? 220)) * (p.strength ?? 1);
    const kind = p.kind ?? "zoom";
    if (kind === "zoom") pulseScale += 0.045 * env;
    else if (kind === "flash") flash = Math.max(flash, 0.6 * env);
    else {
      const k = width / 1080;
      shakeX += Math.sin(frame * 7.3 + p.atMs) * 16 * k * env;
      shakeY += Math.cos(frame * 9.1 + p.atMs) * 12 * k * env;
    }
  }
  const pulseStyle: React.CSSProperties =
    pulseScale !== 1 || shakeX !== 0 || shakeY !== 0
      ? { transform: `translate(${shakeX}px, ${shakeY}px) scale(${pulseScale})`, transformOrigin: "50% 40%" }
      : {};
  const flashLayer =
    flash > 0.01 ? <AbsoluteFill style={{ pointerEvents: "none", backgroundColor: "#fff", opacity: flash, mixBlendMode: "screen" }} /> : null;
  if (!grade)
    return (
      <AbsoluteFill>
        <AbsoluteFill style={pulseStyle}>{children}</AbsoluteFill>
        {flashLayer}
      </AbsoluteFill>
    );
  const { contrast = 1, saturation = 1, brightness = 1, temperature = 0, fade = 0, grain = 0 } = grade;
  const filter = `contrast(${contrast}) saturate(${saturation}) brightness(${brightness})`;
  // Pseudo-random grain offset per frame (deterministic, so renders are reproducible).
  const gx = (frame * 97) % 512;
  const gy = (frame * 53) % 512;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter }}>
        <AbsoluteFill style={pulseStyle}>{children}</AbsoluteFill>
      </AbsoluteFill>
      {flashLayer}
      {temperature !== 0 ? (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            mixBlendMode: "soft-light",
            backgroundColor: temperature > 0 ? "#ff9a3c" : "#3c7bff",
            opacity: Math.min(1, Math.abs(temperature)) * 0.35,
          }}
        />
      ) : null}
      {fade > 0 ? (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            mixBlendMode: "lighten",
            backgroundColor: `rgb(${Math.round(fade * 255)},${Math.round(fade * 255)},${Math.round(fade * 255 + 2)})`,
          }}
        />
      ) : null}
      {grain > 0 ? (
        <AbsoluteFill
          style={{
            pointerEvents: "none",
            mixBlendMode: "overlay",
            opacity: Math.min(1, grain),
            backgroundImage: `url(${staticFile("fx/grain.png")})`,
            backgroundSize: "512px 512px",
            backgroundPosition: `${gx}px ${gy}px`,
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
