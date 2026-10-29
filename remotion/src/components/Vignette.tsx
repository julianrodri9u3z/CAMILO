import React from "react";
import { AbsoluteFill } from "remotion";

/**
 * A dark radial vignette + faint grain wash for a dramatic/documentary
 * section -- grounded in a real reference (ADS GAIA): heavy vignette + glow
 * over AI-generated symbolic b-roll for the conspiracy/mystical angle of that
 * ad. Reusable across ANY style (not tied to "cinematografico") for whichever
 * section of a video needs that heavier, more serious mood -- see the
 * `vignette` field on EditPlan for how to scope it to just part of the video.
 * `intensity` 0-1, default 0.5.
 */
export const Vignette: React.FC<{ intensity?: number }> = ({ intensity = 0.5 }) => {
  const edge = Math.min(0.95, 0.35 + intensity * 0.5);
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 35%, rgba(0,0,0,${edge}) 100%)`,
      }}
    />
  );
};
