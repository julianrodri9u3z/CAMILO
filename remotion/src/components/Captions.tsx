import React, { useMemo } from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CaptionWord } from "../EditPlan";
import type { CaptionVariant } from "../styles/config";

type Line = { words: CaptionWord[]; startMs: number; endMs: number };

const groupIntoLines = (
  words: CaptionWord[],
  maxGapMs = 500,
  maxWordsPerLine = 7
): Line[] => {
  const lines: Line[] = [];
  let current: CaptionWord[] = [];
  // the plan marked phrase starts by hand (by meaning): honor only those, never the word cap
  const explicit = words.some((w) => w.phraseStart);

  for (const word of words) {
    const prev = current[current.length - 1];
    const gapTooBig = prev ? word.startMs - prev.endMs > maxGapMs : false;
    const brk = explicit ? !!word.phraseStart : gapTooBig || current.length >= maxWordsPerLine;
    if (current.length > 0 && brk) {
      lines.push({
        words: current,
        startMs: current[0].startMs,
        // transcripts sometimes give several words the same timestamp; a line shorter than ~300 ms would make the
        // fade interpolations non-monotonic and crash the render ("inputRange must be strictly monotonically increasing")
        endMs: Math.max(current[current.length - 1].endMs, current[0].startMs + 300),
      });
      current = [];
    }
    current.push(word);
  }
  if (current.length > 0) {
    lines.push({
      words: current,
      startMs: current[0].startMs,
      endMs: Math.max(current[current.length - 1].endMs, current[0].startMs + 300),
    });
  }
  return lines;
};

export const Captions: React.FC<{
  words: CaptionWord[];
  variant: CaptionVariant;
  color: string;
  highlightColor: string;
  fontFamily: string;
  bottomPx: number;
}> = ({ words, variant, color, highlightColor, fontFamily, bottomPx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  const lines = useMemo(() => groupIntoLines(words), [words]);
  // karaoke's reference (a real spiritual/angelical b-roll ad) shows tight
  // 2-3 word bursts, not the 7-word default -- a separate grouping so the
  // other variants (which DO want the looser default) are unaffected.
  const karaokeLines = useMemo(() => groupIntoLines(words, 450, 3), [words]);
  // Phrase groups of up to 4 words for the wordBox / kinetic variants.
  const phraseLines = useMemo(() => groupIntoLines(words, 450, 4), [words]);

  if (variant === "highlight") {
    // Short phrase (2-4 words) on a solid rounded highlighter-color box
    // behind bold black text, mixed case (not forced uppercase) -- matches
    // a real "highlighter marker" caption style seen on real UGC footage
    // (hand-written numerology content), distinct from "bold" (no box, just
    // colored/stroked text) and "karaoke" (progressive per-word highlight,
    // no box). One phrase group shown at a time, same fade as "elegant".
    const line = karaokeLines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 250);
    if (!line) return null;
    const fadeInMs = 150;
    const opacity = interpolate(
      nowMs,
      [line.startMs, line.startMs + fadeInMs, line.endMs, line.endMs + 200],
      [0, 1, 1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    return (
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
        <div
          style={{
            marginTop: bottomPx,
            padding: "10px 22px",
            textAlign: "center",
            fontFamily,
            fontSize: 50,
            fontWeight: 800,
            color: "#000000",
            backgroundColor: highlightColor,
            borderRadius: 10,
            opacity,
          }}
        >
          {line.words.map((w) => w.text).join(" ")}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "active") {
    // The most common creator-UGC caption in the ADS ELIDA / loose references
    // (about a third of them): a 3-4 word phrase stays on screen, mixed case as
    // spoken, heavy sans with a black outline, and only the word being spoken
    // right now switches to highlightColor (yellow in most). Same idea as
    // "karaoke" but bottom-anchored and NOT forced uppercase (karaoke is
    // top-anchored uppercase, built for a different reference).
    const line = phraseLines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 200);
    if (!line) return null;
    const opacity = interpolate(nowMs, [line.startMs, line.startMs + 80, line.endMs, line.endMs + 200], [0, 1, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "0 50px",
            textAlign: "center",
            fontFamily,
            fontSize: 58,
            fontWeight: 900,
            lineHeight: 1.15,
            opacity,
          }}
        >
          {line.words.map((w, i) => {
            const isActive = nowMs >= w.startMs && nowMs <= w.endMs;
            return (
              <span
                key={i}
                style={{
                  color: isActive ? highlightColor : color,
                  WebkitTextStroke: "4px #000000",
                  paintOrder: "stroke fill",
                  textShadow: "0 3px 10px rgba(0,0,0,0.45)",
                }}
              >
                {w.text}
                {i < line.words.length - 1 ? " " : ""}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "chip") {
    // Short phrase (1-3 words) on a solid rounded chip, white bold mixed-case
    // text -- the red chip captions of the ADS ELIDA references (highlightColor
    // = chip color; orange-text-on-dark variant is the same idea recolored).
    const line = karaokeLines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 200);
    if (!line) return null;
    const local = frame - Math.round((line.startMs / 1000) * fps);
    const pop = spring({ frame: local, fps, config: { damping: 12, stiffness: 240, mass: 0.5 } });
    const opacity = interpolate(nowMs, [line.endMs, line.endMs + 200], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "8px 22px",
            borderRadius: 12,
            backgroundColor: highlightColor,
            color,
            fontFamily,
            fontSize: 44,
            fontWeight: 800,
            transform: `scale(${pop})`,
            opacity,
            boxShadow: "0 4px 12px rgba(0,0,0,0.35)",
          }}
        >
          {line.words.map((w) => w.text).join(" ")}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "wordBox") {
    // Uppercase white bold text with a colored rounded box on the emphasized
    // word(s): `emphasis: true` on a CaptionWord, or -- if the phrase has none
    // flagged -- the word being spoken right now. Seen with magenta boxes
    // (ELIDA) and purple boxes (GAIA); highlightColor = box color.
    const line = phraseLines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 200);
    if (!line) return null;
    // once the plan flags its words of weight anywhere, unflagged phrases get no box at all (only words of weight
    // are highlighted -- reglas de Antonio); with no flags at all, fall back to boxing the spoken word
    const anyFlagged = words.some((w) => w.emphasis);
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "0 90px",
            textAlign: "center",
            fontFamily,
            // subtle (user, 2026-10-29: "sutiles, un poco más pequeños, nunca tan separados"): normal word spacing,
            // no per-word padding/margin and no heavy outline (it visually spreads the letters); a soft shadow instead
            fontSize: 44,
            fontWeight: 800,
            letterSpacing: 0,
            wordSpacing: 0,
            textTransform: "uppercase",
            lineHeight: 1.3,
            color,
            textShadow: "0 2px 6px rgba(0,0,0,0.75), 0 0 2px rgba(0,0,0,0.9)",
            // a phrase that wraps splits into even lines, never one lonely word underneath (reglas de Antonio)
            ...({ textWrap: "balance" } as React.CSSProperties),
          }}
        >
          {line.words.map((w, i) => {
            const boxed = anyFlagged ? !!w.emphasis : nowMs >= w.startMs && nowMs <= w.endMs;
            return (
              <React.Fragment key={i}>
                {boxed ? (
                  // only the word of weight gets a box; its padding is cancelled by a negative margin so the gap to
                  // the neighbouring words stays a normal space
                  <span
                    style={{
                      padding: "0 7px",
                      margin: "0 -4px",
                      borderRadius: 7,
                      backgroundColor: highlightColor,
                      textShadow: "none",
                      boxDecorationBreak: "clone",
                    }}
                  >
                    {w.text}
                  </span>
                ) : (
                  w.text
                )}
                {i < line.words.length - 1 ? " " : ""}
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "native") {
    // The captions Instagram/TikTok generate themselves: whole phrase,
    // lowercase as spoken, medium-weight sans, white with a soft shadow, no
    // stroke/box/animation. Grounded in a loose TikTok reference and the
    // Instagram Q&A reels -- the low-production, "native app" look.
    const line = lines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 150);
    if (!line) return null;
    const opacity = interpolate(nowMs, [line.startMs, line.startMs + 100, line.endMs, line.endMs + 150], [0, 1, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "0 90px",
            textAlign: "center",
            fontFamily,
            fontSize: 42,
            fontWeight: 600,
            lineHeight: 1.2,
            color,
            opacity,
            textShadow: "0 2px 8px rgba(0,0,0,0.75)",
          }}
        >
          {line.words.map((w) => w.text).join(" ")}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "boxed") {
    // Whole sentence on a tight white box with black text (color = text color,
    // highlightColor = box color) -- the broadcast-style subtitle of the ADS
    // GAIA trailers, distinct from "bar" (full-width dark band).
    const line = lines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 200);
    if (!line) return null;
    const opacity = interpolate(nowMs, [line.startMs, line.startMs + 120, line.endMs, line.endMs + 200], [0, 1, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div style={{ marginBottom: bottomPx, maxWidth: "84%", textAlign: "center", opacity }}>
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 700,
              lineHeight: 1.5,
              color,
              backgroundColor: highlightColor,
              padding: "4px 14px",
              boxDecorationBreak: "clone",
              WebkitBoxDecorationBreak: "clone",
            }}
          >
            {line.words.map((w) => w.text).join(" ")}
          </span>
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "kinetic") {
    // Editorial kinetic typography: words stack up one per line as they're
    // spoken, left-aligned, lowercase, tight leading; a word flagged
    // `emphasis: true` is set much bigger and heavier than the rest. Grounded
    // in the JUAN CARRIZO lifestyle reels ("tu / **negocio** / no crece").
    const line = phraseLines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 250);
    if (!line) return null;
    const fadeOut = interpolate(nowMs, [line.endMs, line.endMs + 250], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const visible = line.words.filter((w) => nowMs >= w.startMs - 30);
    // per-phrase placement chosen by scripts/dodge_captions.py (first word decides)
    const anchor = line.words[0].anchor ?? "left";
    const lift = line.words[0].liftPx ?? 0;
    return (
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: anchor === "left" ? "flex-start" : anchor === "right" ? "flex-end" : "center",
          opacity: fadeOut,
        }}
      >
        <div
          style={{
            marginBottom: bottomPx + lift,
            marginLeft: anchor === "left" ? 70 : 0,
            marginRight: anchor === "right" ? 70 : 0,
            textAlign: anchor,
            fontFamily,
            color,
            lineHeight: 0.92,
            letterSpacing: -1.5,
          }}
        >
          {visible.map((w, i) => {
            const local = frame - Math.round((w.startMs / 1000) * fps);
            const rise = interpolate(local, [0, 5], [14, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const op = interpolate(local, [0, 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <div
                key={i}
                style={{
                  fontSize: w.emphasis ? 104 : 54,
                  fontWeight: w.emphasis ? 800 : 500,
                  transform: `translateY(${rise}px)`,
                  opacity: op,
                  textShadow: "0 3px 16px rgba(0,0,0,0.5)",
                }}
              >
                {w.text}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "bar") {
    // Full-width solid lower-third bar, the whole current line at once -- not
    // a floating word. Grounded in a real reference (VSL FRANQUICIA IA): a
    // solid black bar across the bottom carrying the spoken line, distinct
    // from every other variant here (all floating text with no background
    // band). Common in talking-head/interview-style ads where a persistent
    // caption strip reads as more "produced" than word-by-word hype text.
    const line = lines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 250);
    if (!line) return null;
    const opacity = interpolate(
      nowMs,
      [line.startMs, line.startMs + 120, line.endMs, line.endMs + 200],
      [0, 1, 1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "stretch" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "22px 48px",
            textAlign: "center",
            fontFamily,
            fontSize: 42,
            fontWeight: 700,
            color,
            backgroundColor: "rgba(0,0,0,0.78)",
            opacity,
          }}
        >
          {line.words.map((w) => w.text).join(" ")}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "elegant") {
    const line = lines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 250);
    if (!line) return null;
    const fadeInMs = 200;
    const fadeOutStart = line.endMs;
    const opacity = interpolate(
      nowMs,
      [line.startMs, line.startMs + fadeInMs, fadeOutStart, fadeOutStart + 250],
      [0, 1, 1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "0 60px",
            textAlign: "center",
            fontFamily,
            fontSize: 46,
            fontWeight: 400,
            letterSpacing: 0.5,
            color,
            opacity,
            textShadow: "0 2px 18px rgba(0,0,0,0.65)",
          }}
        >
          {line.words.map((w) => w.text).join(" ")}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "karaoke") {
    // Whole short phrase (2-3 words) stays on screen; only the word being
    // spoken right now lights up in highlightColor while the rest stay in
    // `color` -- distinct from "bold" (one giant word at a time, nothing
    // else visible) and "elegant" (whole line, single color, no per-word
    // highlight). Thick black stroke + heavy weight is the real reference's
    // look, not a subtle caption -- a first pass without the stroke read as
    // "a caption", not as this specific style, even with the right color
    // logic and word grouping.
    const line = karaokeLines.find((l) => nowMs >= l.startMs && nowMs <= l.endMs + 250);
    if (!line) return null;
    return (
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
        <div
          style={{
            marginTop: bottomPx,
            padding: "0 50px",
            textAlign: "center",
            fontFamily,
            fontSize: 64,
            fontWeight: 900,
            textTransform: "uppercase",
            letterSpacing: 0.5,
          }}
        >
          {line.words.map((w, i) => {
            const isActive = nowMs >= w.startMs && nowMs <= w.endMs;
            return (
              <span
                key={i}
                style={{
                  color: isActive ? highlightColor : color,
                  WebkitTextStroke: "3px #000000",
                  paintOrder: "stroke fill",
                  textShadow: "0 3px 10px rgba(0,0,0,0.5)",
                }}
              >
                {w.text}
                {i < line.words.length - 1 ? " " : ""}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  // bold / bouncy / plain: one active word at a time.
  const activeWord = words.find((w) => nowMs >= w.startMs && nowMs <= w.endMs);
  if (!activeWord) return null;

  const wordFrame = frame - Math.round((activeWord.startMs / 1000) * fps);

  if (variant === "plain") {
    // Quick fade+settle, no stroke, no uppercase, no bounce -- a plain
    // spoken-word caption rather than a "hype" TikTok-style one.
    const opacity = interpolate(wordFrame, [0, 4], [0, 1], { extrapolateRight: "clamp" });
    const translateY = interpolate(wordFrame, [0, 6], [6, 0], { extrapolateRight: "clamp" });
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
        <div
          style={{
            marginBottom: bottomPx,
            padding: "0 60px",
            textAlign: "center",
            fontFamily,
            fontSize: 44,
            fontWeight: 700,
            color,
            opacity,
            transform: `translateY(${translateY}px)`,
            textShadow: "0 2px 14px rgba(0,0,0,0.6)",
          }}
        >
          {activeWord.text}
        </div>
      </AbsoluteFill>
    );
  }

  const scale =
    variant === "bouncy"
      ? spring({ frame: wordFrame, fps, config: { damping: 9, stiffness: 220, mass: 0.5 } })
      : spring({ frame: wordFrame, fps, config: { damping: 14, stiffness: 180 } });
  const rotate =
    variant === "bouncy"
      ? interpolate(wordFrame, [0, 6, 12], [-4, 4, 0], { extrapolateRight: "clamp" })
      : 0;

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
      <div
        style={{
          marginBottom: bottomPx,
          padding: "0 40px",
          textAlign: "center",
          fontFamily,
          fontSize: 72,
          fontWeight: 900,
          textTransform: "uppercase",
          color: highlightColor,
          WebkitTextStroke: `2px ${color}`,
          transform: `scale(${scale}) rotate(${rotate}deg)`,
          textShadow: "0 4px 24px rgba(0,0,0,0.75)",
        }}
      >
        {activeWord.text}
      </div>
    </AbsoluteFill>
  );
};
