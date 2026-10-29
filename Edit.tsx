import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { zoomBlur } from "@remotion/transitions/zoom-blur";
import { crossZoom } from "@remotion/transitions/cross-zoom";
import { wipe } from "@remotion/transitions/wipe";
import { iris } from "@remotion/transitions/iris";
import { filmBurn } from "@remotion/transitions/film-burn";
import { dreamyZoom } from "@remotion/transitions/dreamy-zoom";
import { pushCut } from "@remotion/transitions/push-cut";
import { DEFAULT_CTA_DURATION_IN_FRAMES, EditPlan, Reframe } from "../EditPlan";
import type { StyleConfig } from "../styles/config";
import { Captions } from "./Captions";
import { BrollLayer } from "./BrollLayer";
import { CountdownCTA } from "./CountdownCTA";
import { TitleBanner } from "./TitleBanner";
import { KeywordCallout } from "./KeywordCallout";
import { StatCallout } from "./StatCallout";
import { Badge } from "./Badge";
import { AnnotationArrow } from "./AnnotationArrow";
import { HighlightCircle } from "./HighlightCircle";
import { RevenueChart } from "./RevenueChart";
import { Vignette } from "./Vignette";
import { Sticker } from "./Sticker";
import { ListSidebar } from "./ListSidebar";
import { ImageCard } from "./ImageCard";
import { QuestionSticker } from "./QuestionSticker";
import { Bubble } from "./Bubble";
import { LowerThird } from "./LowerThird";
import { BrandBug } from "./BrandBug";
import { CtaButton } from "./CtaButton";
import { CountdownTimer } from "./CountdownTimer";
import { PriceStack } from "./PriceStack";
import { GuaranteeSeal } from "./GuaranteeSeal";
import { TitleCard } from "./TitleCard";
import { ProofStack } from "./ProofStack";
import { ComparisonTable } from "./ComparisonTable";
import { GradeLayer } from "./GradeLayer";
import { BehindTextSegment } from "./BehindText";

// "fade"/"slide"/"none" are hand-rolled (predate this map); the rest are
// @remotion/transitions' own presentations (already an installed dependency)
// -- see styles/config.ts's TransitionKind doc for which mood fits which.
// `iris` is the only one that needs the frame size (its wipe circle is sized
// in pixels), so this takes width/height even though most kinds ignore them.
// Return type is deliberately loose (`any`): each presentation has its OWN
// prop type (FadeProps vs. ZoomBlurProps vs. ...), and TransitionSeries.Transition
// infers its `presentation` prop generically per call site -- a precise union
// return type here fights that instead of helping it, for a value that's
// only ever passed straight through to <Transition presentation={...} />.
const presentationFor = (kind: StyleConfig["transition"], width: number, height: number): any => {
  if (kind === "fade") return fade();
  if (kind === "slide") return slide();
  if (kind === "zoomBlur") return zoomBlur({});
  if (kind === "crossZoom") return crossZoom({});
  if (kind === "wipe") return wipe({});
  if (kind === "iris") return iris({ width, height });
  if (kind === "filmBurn") return filmBurn({});
  if (kind === "dreamyZoom") return dreamyZoom({});
  if (kind === "pushCut") return pushCut({});
  return null;
};

/**
 * Punch-in zoom on the MAIN clip across its own duration -- the same idea
 * BrollLayer already applies to b-roll inserts, now available for the
 * primary footage too (`styleConfig.mainClipZoomPunch`). A cheap, big lever
 * for "energetic UGC" pacing that was previously broll-only.
 */
const ZoomPunchVideo: React.FC<{
  src: string;
  startFrom: number;
  endAt: number;
  durationInFrames: number;
  zoomPunch: boolean;
  staticZoom?: number;
  zoomOrigin?: "top" | "center" | "bottom";
  /** Source seconds at this clip's first frame (needed to sample the reframe track). */
  clipStartSeconds?: number;
  reframe?: Reframe;
}> = ({ src, startFrom, endAt, durationInFrames, zoomPunch, staticZoom = 1, zoomOrigin = "center", clipStartSeconds = 0, reframe }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const scale =
    staticZoom *
    (zoomPunch ? interpolate(frame, [0, durationInFrames], [1.06, 1], { extrapolateRight: "clamp" }) : 1);

  if (reframe && reframe.points.length > 0) {
    // Virtual camera: keep the tracked focus point at (targetX, targetY) of the frame, never showing outside the source.
    const t = clipStartSeconds + frame / fps;
    const pts = reframe.points;
    let i = 0;
    while (i < pts.length - 1 && pts[i + 1].t <= t) i++;
    const a = pts[i];
    const b = pts[Math.min(i + 1, pts.length - 1)];
    const k = b.t > a.t ? Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t))) : 0;
    const fx = a.x + (b.x - a.x) * k;
    const fy = a.y + (b.y - a.y) * k;
    const fz = (a.z ?? 1) + ((b.z ?? 1) - (a.z ?? 1)) * k;
    const s0 = Math.max(width / reframe.srcW, height / reframe.srcH);
    const s = s0 * fz * scale;
    const dispW = reframe.srcW * s;
    const dispH = reframe.srcH * s;
    const tx = (reframe.targetX ?? 0.5) * width;
    const ty = (reframe.targetY ?? 0.4) * height;
    const left = Math.min(0, Math.max(width - dispW, tx - fx * dispW));
    const top = Math.min(0, Math.max(height - dispH, ty - fy * dispH));
    return (
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <OffthreadVideo
          src={staticFile(src)}
          startFrom={startFrom}
          endAt={endAt}
          style={{ position: "absolute", left, top, width: dispW, height: dispH }}
        />
      </AbsoluteFill>
    );
  }
  return (
    <OffthreadVideo
      src={staticFile(src)}
      startFrom={startFrom}
      endAt={endAt}
      style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, transformOrigin: zoomOrigin === "top" ? "50% 20%" : zoomOrigin === "bottom" ? "50% 100%" : "50% 50%" }}
    />
  );
};

const DUCK_PAD_MS = 200;

/**
 * Merges word-level captions into continuous speech intervals (+ padding),
 * so background music can duck under dialogue and come back up in silence --
 * "priority to the voice" instead of one flat low volume for the whole edit.
 */
const buildSpeechIntervals = (captions: EditPlan["captions"]): [number, number][] => {
  if (captions.length === 0) return [];
  const sorted = [...captions].sort((a, b) => a.startMs - b.startMs);
  const intervals: [number, number][] = [];
  let curStart = sorted[0].startMs - DUCK_PAD_MS;
  let curEnd = sorted[0].endMs + DUCK_PAD_MS;
  for (let i = 1; i < sorted.length; i++) {
    const w = sorted[i];
    if (w.startMs - DUCK_PAD_MS <= curEnd) {
      curEnd = Math.max(curEnd, w.endMs + DUCK_PAD_MS);
    } else {
      intervals.push([curStart, curEnd]);
      curStart = w.startMs - DUCK_PAD_MS;
      curEnd = w.endMs + DUCK_PAD_MS;
    }
  }
  intervals.push([curStart, curEnd]);
  return intervals;
};

const isSpeakingAt = (intervals: [number, number][], ms: number): boolean => {
  let lo = 0;
  let hi = intervals.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const [start, end] = intervals[mid];
    if (ms < start) hi = mid - 1;
    else if (ms > end) lo = mid + 1;
    else return true;
  }
  return false;
};

export const Edit: React.FC<{ editPlan: EditPlan; styleConfig: StyleConfig }> = ({
  editPlan,
  styleConfig,
}) => {
  const { fps, width, height } = useVideoConfig();
  const transitionDurationMs =
    editPlan.transitionDurationMs ?? styleConfig.transitionDurationMs;
  const transitionFrames = Math.max(1, Math.round((transitionDurationMs / 1000) * fps));
  const presentation = presentationFor(styleConfig.transition, width, height);

  const clipDurations = editPlan.clips.map((c) =>
    Math.max(1, Math.round((c.endAtSeconds - c.startFromSeconds) * fps))
  );

  // Hard-cut timeline offsets (only meaningful when presentation === null, i.e. transition "none").
  const clipStarts = clipDurations.map((_, i) => clipDurations.slice(0, i).reduce((a, b) => a + b, 0));
  const behindSegments = (editPlan.behindText ?? []).flatMap((item, k) => {
    if (presentation) return []; // timeline overlaps under transitions would misalign the matte
    const winStart = Math.round((item.atMs / 1000) * fps);
    const winEnd = winStart + Math.round((item.durationMs / 1000) * fps);
    return editPlan.clips.flatMap((clip, i) => {
      const a = Math.max(clipStarts[i], winStart);
      const b = Math.min(clipStarts[i] + clipDurations[i], winEnd);
      if (b <= a) return [];
      return [{ key: `bt-${k}-${i}`, item, clip, clipStartFrame: clipStarts[i], clipDurationFrames: clipDurations[i], segFrom: a, segDuration: b - a }];
    });
  });

  const speechIntervals = buildSpeechIntervals(editPlan.captions);
  const fullVolume = editPlan.musicFullVolume ?? styleConfig.musicFullVolume;
  const duckedVolume = editPlan.musicDuckedVolume ?? styleConfig.musicDuckedVolume;
  const musicVolume = (frame: number) => {
    const nowMs = (frame / fps) * 1000;
    return isSpeakingAt(speechIntervals, nowMs) ? duckedVolume : fullVolume;
  };

  return (
    <>
    <Sequence from={0} durationInFrames={editPlan.totalDurationInFrames}>
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <GradeLayer grade={editPlan.grade} pulses={editPlan.pulses}>
      {editPlan.clips.length === 0 ? (
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            color: "#888",
            fontFamily: "sans-serif",
            fontSize: 32,
          }}
        >
          Sin clips en el EditPlan -- fixture de previsualizacion.
        </AbsoluteFill>
      ) : presentation ? (
        <TransitionSeries>
          {editPlan.clips.flatMap((clip, i) => {
            const startFrom = Math.round(clip.startFromSeconds * fps);
            const endAt = Math.round(clip.endAtSeconds * fps);
            const sequence = (
              <TransitionSeries.Sequence key={`clip-${i}`} durationInFrames={clipDurations[i]}>
                <ZoomPunchVideo
                  src={clip.src}
                  startFrom={startFrom}
                  endAt={endAt}
                  durationInFrames={clipDurations[i]}
                  zoomPunch={styleConfig.mainClipZoomPunch}
                  staticZoom={clip.zoom}
                  zoomOrigin={clip.zoomOrigin}
                  clipStartSeconds={clip.startFromSeconds}
                  reframe={editPlan.reframe}
                />
              </TransitionSeries.Sequence>
            );
            const isLast = i === editPlan.clips.length - 1;
            if (isLast) return [sequence];
            return [
              sequence,
              <TransitionSeries.Transition
                key={`transition-${i}`}
                presentation={presentation}
                timing={linearTiming({ durationInFrames: transitionFrames })}
              />,
            ];
          })}
        </TransitionSeries>
      ) : (
        // "none": hard cuts, no overlap between clips.
        editPlan.clips.map((clip, i) => {
          const from = clipDurations.slice(0, i).reduce((a, b) => a + b, 0);
          const startFrom = Math.round(clip.startFromSeconds * fps);
          const endAt = Math.round(clip.endAtSeconds * fps);
          return (
            <Sequence key={i} from={from} durationInFrames={clipDurations[i]}>
              <ZoomPunchVideo
                src={clip.src}
                startFrom={startFrom}
                endAt={endAt}
                durationInFrames={clipDurations[i]}
                zoomPunch={styleConfig.mainClipZoomPunch}
                staticZoom={clip.zoom}
                zoomOrigin={clip.zoomOrigin}
                clipStartSeconds={clip.startFromSeconds}
                reframe={editPlan.reframe}
              />
            </Sequence>
          );
        })
      )}

      {behindSegments.map((sg) => (
        <Sequence key={sg.key} from={sg.segFrom} durationInFrames={sg.segDuration}>
          <BehindTextSegment
            item={sg.item}
            clip={sg.clip}
            clipStartFrame={sg.clipStartFrame}
            clipDurationFrames={sg.clipDurationFrames}
            segFrom={sg.segFrom}
            segDuration={sg.segDuration}
            zoomPunch={styleConfig.mainClipZoomPunch}
          />
        </Sequence>
      ))}

      <BrollLayer
        inserts={editPlan.broll}
        fps={fps}
        fadeMs={styleConfig.brollFadeMs}
        zoomPunchIn={styleConfig.brollZoomPunchIn}
      />
      </GradeLayer>

      {editPlan.vignette ? (
        editPlan.vignette.atMs !== undefined && editPlan.vignette.durationMs !== undefined ? (
          <Sequence
            from={Math.round((editPlan.vignette.atMs / 1000) * fps)}
            durationInFrames={Math.round((editPlan.vignette.durationMs / 1000) * fps)}
          >
            <Vignette intensity={editPlan.vignette.intensity} />
          </Sequence>
        ) : (
          <Vignette intensity={editPlan.vignette.intensity} />
        )
      ) : null}

      {editPlan.title ? (
        editPlan.title.startMs !== undefined && editPlan.title.durationMs !== undefined ? (
          <Sequence
            from={Math.round((editPlan.title.startMs / 1000) * fps)}
            durationInFrames={Math.round((editPlan.title.durationMs / 1000) * fps)}
          >
            <TitleBanner text={editPlan.title.text} position={editPlan.title.position} bg={editPlan.title.bg} color={editPlan.title.color} />
          </Sequence>
        ) : (
          <TitleBanner text={editPlan.title.text} position={editPlan.title.position} bg={editPlan.title.bg} color={editPlan.title.color} />
        )
      ) : null}

      {(editPlan.keywordCallouts ?? []).map((kw, i) => (
        <KeywordCallout key={i} text={kw.text} atMs={kw.atMs} durationMs={kw.durationMs} />
      ))}

      {(editPlan.statCallouts ?? []).map((s, i) => (
        <StatCallout
          key={i}
          text={s.text}
          atMs={s.atMs}
          durationMs={s.durationMs}
          countFrom={s.countFrom}
          countTo={s.countTo}
          prefix={s.prefix}
          suffix={s.suffix}
          color={s.color}
          x={s.x}
          y={s.y}
          size={s.size}
          glow={s.glow}
        />
      ))}

      {(editPlan.badges ?? []).map((b, i) => (
        <Badge
          key={i}
          text={b.text}
          atMs={b.atMs}
          durationMs={b.durationMs}
          position={b.position}
          bg={b.bg}
          color={b.color}
          icon={b.icon}
        />
      ))}

      {(editPlan.arrows ?? []).map((a, i) => (
        <AnnotationArrow
          key={i}
          atMs={a.atMs}
          durationMs={a.durationMs}
          x={a.x}
          y={a.y}
          direction={a.direction}
          length={a.length}
          color={a.color}
        />
      ))}

      {(editPlan.highlightCircles ?? []).map((h, i) => (
        <HighlightCircle
          key={i}
          atMs={h.atMs}
          durationMs={h.durationMs}
          x={h.x}
          y={h.y}
          width={h.width}
          height={h.height}
          color={h.color}
          strokeWidth={h.strokeWidth}
        />
      ))}

      {editPlan.revenueChart ? (
        <RevenueChart
          atMs={editPlan.revenueChart.atMs}
          durationMs={editPlan.revenueChart.durationMs}
          points={editPlan.revenueChart.points}
          x={editPlan.revenueChart.x}
          y={editPlan.revenueChart.y}
          width={editPlan.revenueChart.width}
          height={editPlan.revenueChart.height}
          color={editPlan.revenueChart.color}
          counterPrefix={editPlan.revenueChart.counterPrefix}
          counterSuffix={editPlan.revenueChart.counterSuffix}
          label={editPlan.revenueChart.label}
        />
      ) : null}

      {(editPlan.brandBugs ?? []).map((b, i) => (
        <BrandBug key={i} text={b.text} src={b.src} position={b.position} atMs={b.atMs} durationMs={b.durationMs} height={b.height} />
      ))}

      {(editPlan.questionStickers ?? []).map((q, i) => (
        <QuestionSticker key={i} text={q.text} header={q.header} atMs={q.atMs} durationMs={q.durationMs} x={q.x} y={q.y} width={q.width} />
      ))}

      {(editPlan.imageCards ?? []).map((c, i) => (
        <ImageCard key={i} src={c.src} atMs={c.atMs} durationMs={c.durationMs} x={c.x} y={c.y} width={c.width} rotate={c.rotate} />
      ))}

      {(editPlan.bubbles ?? []).map((b, i) => (
        <Bubble key={i} src={b.src} atMs={b.atMs} durationMs={b.durationMs} x={b.x} y={b.y} size={b.size} borderColor={b.borderColor} />
      ))}

      {editPlan.listSidebar ? (
        <ListSidebar
          items={editPlan.listSidebar.items}
          startMs={editPlan.listSidebar.startMs}
          endMs={editPlan.listSidebar.endMs}
          x={editPlan.listSidebar.x}
          y={editPlan.listSidebar.y}
          gap={editPlan.listSidebar.gap}
        />
      ) : null}

      {(editPlan.stickers ?? []).map((st, i) => (
        <Sticker key={i} atMs={st.atMs} durationMs={st.durationMs} x={st.x} y={st.y} emoji={st.emoji} src={st.src} size={st.size} rotate={st.rotate} />
      ))}

      {(editPlan.lowerThirds ?? []).map((l, i) => (
        <LowerThird key={i} name={l.name} subtitle={l.subtitle} atMs={l.atMs} durationMs={l.durationMs} accent={l.accent} bottomPx={l.bottomPx} />
      ))}

      {(editPlan.proofStacks ?? []).map((p, i) => (
        <ProofStack key={i} images={p.images} atMs={p.atMs} durationMs={p.durationMs} backdrop={p.backdrop} staggerMs={p.staggerMs} cardWidth={p.cardWidth} />
      ))}

      {(editPlan.comparisonTables ?? []).map((t, i) => (
        <ComparisonTable key={i} atMs={t.atMs} durationMs={t.durationMs} title={t.title} columns={t.columns} rows={t.rows} highlightFirst={t.highlightFirst} staggerMs={t.staggerMs} />
      ))}

      {(editPlan.priceStacks ?? []).map((p, i) => (
        <PriceStack key={i} atMs={p.atMs} durationMs={p.durationMs} title={p.title} lines={p.lines} totalLabel={p.totalLabel} total={p.total} strikeTotal={p.strikeTotal} layout={p.layout} bg={p.bg} accent={p.accent} staggerMs={p.staggerMs} />
      ))}

      {(editPlan.titleCards ?? []).map((c, i) => (
        <TitleCard key={i} text={c.text} atMs={c.atMs} durationMs={c.durationMs} bg={c.bg} dim={c.dim} color={c.color} look={c.look} fontSize={c.fontSize} position={c.position} />
      ))}

      {(editPlan.guaranteeSeals ?? []).map((g, i) => (
        <GuaranteeSeal key={i} atMs={g.atMs} durationMs={g.durationMs} big={g.big} small={g.small} caption={g.caption} look={g.look} />
      ))}

      {editPlan.countdownTimer ? (
        <CountdownTimer
          startMs={editPlan.countdownTimer.startMs}
          endMs={editPlan.countdownTimer.endMs}
          fromSeconds={editPlan.countdownTimer.fromSeconds}
          label={editPlan.countdownTimer.label}
          style={editPlan.countdownTimer.style}
          withHours={editPlan.countdownTimer.withHours}
          color={editPlan.countdownTimer.color}
        />
      ) : null}

      {(editPlan.ctaButtons ?? []).map((b, i) => (
        <CtaButton key={i} text={b.text} atMs={b.atMs} durationMs={b.durationMs} y={b.y} color={b.color} textColor={b.textColor} chevrons={b.chevrons} chevronColor={b.chevronColor} />
      ))}

      {/* Captions render last so overlays (cards, stickers, question box) never cover them. */}
      <Captions
        words={editPlan.captions}
        variant={styleConfig.captionVariant}
        color={styleConfig.captionColor}
        highlightColor={styleConfig.captionHighlightColor}
        fontFamily={styleConfig.captionFontFamily}
        bottomPx={editPlan.captionBottomPx ?? styleConfig.captionPositionFromBottom}
      />

      {editPlan.musicPath ? (
        (editPlan.musicOffsetSeconds ?? 0) < 0 ? (
          <Sequence from={Math.round(-(editPlan.musicOffsetSeconds ?? 0) * fps)}>
            <Audio src={staticFile(editPlan.musicPath)} volume={(f) => musicVolume(f + Math.round(-(editPlan.musicOffsetSeconds ?? 0) * fps))} />
          </Sequence>
        ) : (
          <Audio
            src={staticFile(editPlan.musicPath)}
            startFrom={Math.round((editPlan.musicOffsetSeconds ?? 0) * fps)}
            volume={musicVolume}
          />
        )
      ) : null}

      {(editPlan.sfx ?? []).map((hit, i) => (
        <Sequence key={`sfx-${i}`} from={Math.max(0, Math.round((hit.atMs / 1000) * fps))}>
          <Audio src={staticFile(hit.src)} volume={hit.volume ?? 0.5} />
        </Sequence>
      ))}
    </AbsoluteFill>
    </Sequence>

    {editPlan.cta ? (
      <Sequence
        from={editPlan.totalDurationInFrames}
        durationInFrames={editPlan.cta.durationInFrames ?? DEFAULT_CTA_DURATION_IN_FRAMES}
      >
        <CountdownCTA
          text={editPlan.cta.text}
          backgroundSrc={editPlan.cta.backgroundSrc}
          musicSrc={editPlan.cta.musicSrc}
          durationInFrames={editPlan.cta.durationInFrames ?? DEFAULT_CTA_DURATION_IN_FRAMES}
        />
      </Sequence>
    ) : null}
    </>
  );
};
