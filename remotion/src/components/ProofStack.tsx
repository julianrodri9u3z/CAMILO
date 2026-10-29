import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A fan of proof screenshots (social posts, chat messages, bank statements)
 * dropped one after another over a dark gradient backdrop -- the way UpLevel
 * presents its three client results (X/Facebook posts stacked and fanned on a
 * dark-blue gradient, captions of the presenter still visible below). One image
 * per beat of the script ("Anne-Marie got paid $3,000... or James... or Layla...").
 * `images` are files relative to remotion/public/ that the USER provided. Never
 * fabricate or alter screenshots; blur private data (names, numbers not being
 * claimed) BEFORE bringing the image in.
 * `backdrop`: "blue" (default), "purple", "dark". Cards land at `staggerMs`
 * intervals and stay until the stack ends.
 */
export const ProofStack: React.FC<{
  images: string[];
  atMs: number;
  durationMs: number;
  backdrop?: "blue" | "purple" | "dark";
  staggerMs?: number;
  cardWidth?: number;
}> = ({ images, atMs, durationMs, backdrop = "blue", staggerMs = 1400, cardWidth }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  if (nowMs < atMs || nowMs > atMs + durationMs) return null;
  const local = nowMs - atMs;
  const bg = {
    blue: "radial-gradient(ellipse at 50% 100%, #1B3FBF 0%, #0A1236 55%, #04060F 100%)",
    purple: "radial-gradient(ellipse at 50% 100%, #6D28D9 0%, #1E0B3E 55%, #07030F 100%)",
    dark: "radial-gradient(ellipse at 50% 60%, #222 0%, #0A0A0A 100%)",
  }[backdrop];
  const opacity = interpolate(local, [0, 250, durationMs - 250, durationMs], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const w = cardWidth ?? Math.min(width * 0.68, height * 0.62);

  return (
    <AbsoluteFill style={{ opacity, background: bg, justifyContent: "center", alignItems: "center" }}>
      {images.map((src, i) => {
        const t = local - i * staggerMs;
        if (t < 0) return null;
        const p = spring({ frame: Math.round((t / 1000) * fps), fps, config: { damping: 13, stiffness: 150 } });
        const fan = (i - (images.length - 1) / 2) * 5; // degrees
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              width: w,
              transform: `translate(${(i - (images.length - 1) / 2) * w * 0.12}px, ${(1 - p) * 90 - i * 10}px) rotate(${fan}deg) scale(${0.92 + p * 0.08})`,
              opacity: p,
              borderRadius: 18,
              overflow: "hidden",
              boxShadow: "0 22px 60px rgba(0,0,0,0.6)",
              background: "#fff",
            }}
          >
            <Img src={staticFile(src)} style={{ width: "100%", display: "block" }} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
