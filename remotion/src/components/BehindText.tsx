import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { BehindTextItem, Clip } from "../EditPlan";

/**
 * "Text behind the person": the signature depth effect of premium short-form edits.
 * Three layers, bottom to top:  (1) the normal footage (drawn by Edit.tsx, below),
 * (2) the big headline text drawn HERE, (3) a second copy of the same footage masked with the person's
 * alpha matte (per-frame PNGs from scripts/vision_analyze.py) so the presenter's head/shoulders sit IN FRONT of
 * the text. The copy gets the exact same crop/zoom as the base clip so the matte stays registered.
 *
 * Rendered once per source clip the window overlaps (a hard cut inside the window just starts a new segment).
 * Hard-cut styles only (transition "none"); with overlapping transitions the timeline offsets differ.
 * Only schedule it while the presenter is on screen and mostly steady -- never over b-roll.
 */
export const BehindTextSegment: React.FC<{
  item: BehindTextItem;
  clip: Clip;
  clipStartFrame: number; // global frame where this clip starts
  clipDurationFrames: number;
  segFrom: number; // global frame where this segment starts
  segDuration: number;
  zoomPunch: boolean;
}> = ({ item, clip, clipStartFrame, clipDurationFrames, segFrom, segDuration, zoomPunch }) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const g = segFrom + f;
  const winStart = Math.round((item.atMs / 1000) * fps);
  const winDur = Math.max(1, Math.round((item.durationMs / 1000) * fps));
  const w = g - winStart;

  const inP = interpolate(w, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outP = interpolate(w, [winDur - 9, winDur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ease = (x: number) => 1 - Math.pow(1 - x, 3);
  const opacity = Math.min(ease(inP), outP) * (item.opacity ?? 1);
  const anim = item.anim ?? "rise";
  const drift = 1 + 0.035 * Math.min(1, Math.max(0, w / winDur)); // never a dead hold
  const rise = anim === "rise" ? (1 - ease(inP)) * 70 : 0;
  const popScale = anim === "scale" ? 1.12 - 0.12 * ease(inP) : 1;

  // matte frame for THIS source time (the matte folder is indexed by source frame)
  const srcTime = clip.startFromSeconds + (g - clipStartFrame) / fps;
  const idx = Math.max(1, Math.round((srcTime - item.matte.firstT) * item.matte.fps) + 1);
  const maskUrl = staticFile(`${item.matte.dir}/m_${String(idx).padStart(6, "0")}.png`);

  const clipLocal = g - clipStartFrame;
  const scale =
    (clip.zoom ?? 1) * (zoomPunch ? interpolate(clipLocal, [0, clipDurationFrames], [1.06, 1], { extrapolateRight: "clamp" }) : 1);
  const origin = clip.zoomOrigin === "top" ? "50% 20%" : "50% 50%";
  const startFromFrame = Math.round((clip.startFromSeconds + (segFrom - clipStartFrame) / fps) * fps);

  const k = Math.min(width, height) / 1080;
  const lines = item.text.split("\n");
  const size = (item.size ?? 360) * k;
  const cy = item.y ?? 600;
  const cx = item.x ?? width / 2;

  return (
    <AbsoluteFill>
      {/* preload the matte frame: Remotion waits for <Img>, so the CSS mask below is never drawn half-loaded */}
      <Img src={maskUrl} style={{ position: "absolute", width: 1, height: 1, opacity: 0 }} />
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: cx,
            top: cy,
            transform: `translate(-50%, -50%) translateY(${rise}px) scale(${popScale * drift})`,
            opacity,
            textAlign: "center",
            fontFamily: item.font ?? "Impact, 'Arial Narrow Bold', 'Arial Black', 'Helvetica Neue', sans-serif",
            fontWeight: item.weight ?? 900,
            fontSize: size,
            lineHeight: item.lineHeight ?? 0.92,
            letterSpacing: (item.letterSpacing ?? 0) * k,
            color: item.color ?? "#FFFFFF",
            textTransform: "uppercase",
            whiteSpace: "nowrap",
            textShadow: item.shadow === false ? "none" : "0 8px 40px rgba(0,0,0,0.25)",
          }}
        >
          {lines.map((l, i) => (
            <div key={i}>{l}</div>
          ))}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: origin }}>
        <AbsoluteFill
          style={{
            WebkitMaskImage: `url(${maskUrl})`,
            maskImage: `url(${maskUrl})`,
            WebkitMaskSize: "100% 100%",
            maskSize: "100% 100%",
            WebkitMaskRepeat: "no-repeat",
            maskRepeat: "no-repeat",
          }}
        >
          <OffthreadVideo
            src={staticFile(clip.src)}
            startFrom={startFromFrame}
            endAt={startFromFrame + segDuration}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
