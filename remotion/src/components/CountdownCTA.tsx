import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const RING_RADIUS = 175;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;
const RING_BOX = 430;
const RING_CENTER = RING_BOX / 2;

/**
 * Generic downward-chevron mark (three stacked chevrons, teal-to-purple
 * gradient) -- an original shape inspired by the "scroll/tap down" motif
 * common to these CTA templates, not a copy of any specific brand's logo.
 */
const ChevronMark: React.FC<{ opacity: number }> = ({ opacity }) => (
  <svg width="210" height="186" viewBox="0 0 122 108" style={{ opacity }}>
    <defs>
      <linearGradient id="chevronGradient" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#2FE8D6" />
        <stop offset="100%" stopColor="#8B5CF6" />
      </linearGradient>
    </defs>
    {[0, 32, 64].map((y, i) => (
      <polyline
        key={i}
        points={`14,${y} 61,${y + 27} 108,${y}`}
        fill="none"
        stroke="url(#chevronGradient)"
        strokeWidth={9}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={1 - i * 0.28}
      />
    ))}
  </svg>
);

export const CountdownCTA: React.FC<{
  text: string;
  backgroundSrc: string;
  musicSrc?: string;
  durationInFrames: number;
}> = ({ text, backgroundSrc, musicSrc, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const secondsLeft = Math.max(1, Math.ceil((durationInFrames - frame) / fps));
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });
  const dashOffset = RING_CIRCUMFERENCE * progress;

  const entrance = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const chevronPulse = 0.6 + 0.4 * Math.abs(Math.sin(frame / 12));

  const lines = text.split("\n");

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0A" }}>
      <AbsoluteFill>
        <OffthreadVideo
          src={staticFile(backgroundSrc)}
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(3px) brightness(0.55)" }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.35) 45%, rgba(0,0,0,0.7) 100%)",
        }}
      />

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 140, opacity: entrance }}>
        <div
          style={{
            textAlign: "center",
            padding: "0 60px",
            fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
            fontWeight: 900,
            fontSize: 58,
            lineHeight: 1.12,
            color: "#FFFFFF",
            textTransform: "uppercase",
            textShadow: "0 3px 0 rgba(0,0,0,0.4), 0 8px 30px rgba(0,0,0,0.6)",
          }}
        >
          {lines.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: entrance }}>
        <svg width={RING_BOX} height={RING_BOX} viewBox={`0 0 ${RING_BOX} ${RING_BOX}`}>
          <circle cx={RING_CENTER} cy={RING_CENTER} r={RING_RADIUS} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={8} />
          <circle
            cx={RING_CENTER}
            cy={RING_CENTER}
            r={RING_RADIUS}
            fill="none"
            stroke="#2FE8D6"
            strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={RING_CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${RING_CENTER} ${RING_CENTER})`}
            style={{ filter: "drop-shadow(0 0 10px #2FE8D6)" }}
          />
          <text
            x={RING_CENTER}
            y={RING_CENTER + 50}
            textAnchor="middle"
            fontSize={150}
            fontWeight={900}
            fontFamily="'Arial Black', 'Helvetica Neue', sans-serif"
            fill="#FFFFFF"
          >
            {secondsLeft}
          </text>
        </svg>
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 160 }}>
        <ChevronMark opacity={chevronPulse} />
      </AbsoluteFill>

      {musicSrc ? <Audio src={staticFile(musicSrc)} volume={0.35} /> : null}
    </AbsoluteFill>
  );
};
