/**
 * Shape of the JSON job file passed to `remotion render` via --props=job.json.
 * Claude builds one of these per edit, after transcribing the raw footage
 * (word-level timestamps -> captions) and running scripts/fetch_broll.py
 * (-> broll). Timestamps are absolute milliseconds from the start of the
 * final edit, not from the source clip.
 */
import type { CaptionVariant } from "./styles/config";

export type Clip = {
  /**
   * Path relative to remotion/public/ (Remotion only serves local media from
   * there -- absolute paths and file:// URLs are rejected at render time).
   * Copy/symlink the real source file into public/jobs/<job-slug>/ before
   * building the EditPlan and use that relative path here.
   */
  src: string;
  /** Trim points inside the source file, in seconds. */
  startFromSeconds: number;
  endAtSeconds: number;
  /**
   * Optional static crop-in for this clip (1 = as filmed, 1.12 = 12% tighter).
   * The VSL "punch cut": one continuous take is split into several clips at
   * sentence boundaries (startFromSeconds continuing exactly where the previous
   * clip ended) and alternate clips get zoom 1 / 1.1-1.15 -- a hard cut that
   * hides the jump and re-frames the presenter, seen in UpLevel and the ADS
   * talking heads. Combines with the style's mainClipZoomPunch.
   */
  zoom?: number;
  /** Vertical anchor of the zoom crop: "top" keeps the head in frame when zooming in. Default "center". */
  zoomOrigin?: "top" | "center" | "bottom";
  /**
   * How the cut INTO this clip looks, overriding the plan's `cutTransition` (e.g. "none" for a pause trimmed inside
   * the same take -- a jump cut hidden by alternating `zoom` -- and the default blurZoom for real scene changes).
   */
  cut?: "blurZoom" | "none";
  /** 0-1 volume of this clip's own audio (default 1). 0 for text-only ads whose generated clips carry babble. */
  volume?: number;
};

export type CaptionWord = {
  text: string;
  startMs: number;
  endMs: number;
  /**
   * Optional: mark a word as the one to emphasize. Used by the "wordBox" and
   * "kinetic" caption variants (a highlight box / a bigger, bolder word). If
   * no word in a phrase is flagged, "wordBox" falls back to boxing the word
   * being spoken right now. Other variants ignore it.
   */
  emphasis?: boolean;
  /**
   * Optional per-phrase placement (set by scripts/dodge_captions.py so subtitles avoid faces/hands). The anchor
   * of the FIRST word of a phrase decides where that whole phrase sits. Used by the "kinetic" variant.
   */
  anchor?: "left" | "center" | "right";
  /** Extra px to lift this phrase above the style's default baseline (at 1080x1920). */
  liftPx?: number;
  /**
   * Starts a new on-screen phrase here. If ANY word in `captions` sets it, phrases are cut only at these marks (cut
   * by meaning, never leaving a lone short word on screen -- reglas de Antonio) instead of the variant's word cap.
   */
  phraseStart?: boolean;
};

export type BrollInsert = {
  /** Path relative to remotion/public/ -- see Clip.src. */
  src: string;
  /** When this insert starts, in ms from the start of the final edit. */
  atMs: number;
  durationMs: number;
  /** 0-1: opacity of a bottom-up dark gradient so captions stay legible over bright stock. Default off. */
  scrim?: number;
  /** Static crop-in for this insert (1.35 pushes burned-in bottom captions of a borrowed clip off-screen). */
  zoom?: number;
  zoomOrigin?: "top" | "center" | "bottom";
  /** Extra per-clip correction (from scripts/match_broll_grade.py) so this insert matches the main footage. */
  grade?: Pick<Grade, "contrast" | "saturation" | "brightness" | "temperature">;
};

/**
 * Look applied to every PICTURE layer (main clips + b-roll) -- not to overlays/captions.
 * All fields optional; 1 / 0 = neutral. See components/GradeLayer.tsx. Keep values subtle.
 */
export type Grade = {
  contrast?: number;     // 1 = as filmed, 1.05-1.12 typical
  saturation?: number;   // 1 = as filmed
  brightness?: number;   // 1 = as filmed
  temperature?: number;  // -1 (cool) .. 1 (warm); 0.1-0.25 is a gentle warm cast
  fade?: number;         // 0-0.12 lifted blacks (filmic matte look)
  grain?: number;        // 0-0.35 animated film grain
};

/** Reference to a folder of per-frame person mattes made by scripts/vision_analyze.py. */
export type MatteRef = {
  /** Folder relative to remotion/public/ containing m_000001.png ... (RGBA, alpha = person). */
  dir: string;
  /** Source fps of the analyzed video (zones.json `fps`). */
  fps: number;
  /** Source time (s) of matte frame 1 (zones.json `firstT`). */
  firstT: number;
};

export type BehindTextItem = {
  /** Headline; "\n" for lines. Rendered uppercase. */
  text: string;
  atMs: number;
  durationMs: number;
  matte: MatteRef;
  /** Center in the 1080x1920 frame. Default x = centered, y = 600. Put the text where the head OVERLAPS it. */
  x?: number;
  y?: number;
  /** Font size px at 1080 wide (default 360). */
  size?: number;
  color?: string;
  weight?: number;
  font?: string;
  letterSpacing?: number;
  lineHeight?: number;
  opacity?: number;
  anim?: "rise" | "scale" | "none";
  shadow?: boolean;
};

/**
 * Smart reframing of a WIDE source into the (usually vertical) frame: a virtual camera that follows the subject.
 * Points are sampled by SOURCE time; x/y = the point of the source frame (0-1) to keep at the frame's focus point,
 * z = extra zoom (1 = just cover the frame). Made by scripts/make_reframe.py from vision_analyze.py zones.
 */
export type Reframe = {
  srcW: number;
  srcH: number;
  /** Where the focus point sits in the output frame, as fractions (default x 0.5, y 0.4: face in the upper third). */
  targetX?: number;
  targetY?: number;
  points: { t: number; x: number; y: number; z?: number }[];
};

/** Beat-driven punch: a decaying zoom / white flash / shake on the picture layers at a given time. */
export type Pulse = {
  atMs: number;
  kind?: "zoom" | "flash" | "shake";
  /** 0-1.5, default 1. */
  strength?: number;
  /** Decay time constant in ms (default 220). */
  decayMs?: number;
};

export type SfxHit = {
  /** Path relative to remotion/public/ (e.g. "sfx/whoosh_soft.wav"). */
  src: string;
  atMs: number;
  /** 0-1, default 0.5. Sound effects sit UNDER the voice; keep them quiet. */
  volume?: number;
};

export type EditPlan = {
  fps: number;
  width: number;
  height: number;
  clips: Clip[];
  captions: CaptionWord[];
  /** Per-job caption look, overriding the style's (e.g. "wordBox" so only the words of weight get the box). */
  captionVariant?: CaptionVariant;
  captionColor?: string;
  captionHighlightColor?: string;
  broll: BrollInsert[];
  /** Path relative to remotion/public/, once a track is picked from the user's bank. Omit to render silent (music brief goes in the chat/report instead). */
  /** Overrides the style's caption distance from the bottom edge (px at 1080x1920). Lower = captions sit lower, clear of mid-frame graphics. */
  captionBottomPx?: number;
  musicPath?: string;
  /** 0-1, level under dialogue. Style defaults apply if omitted. */
  musicDuckedVolume?: number;
  /** 0-1, level with no dialogue on screen. Style defaults apply if omitted. */
  musicFullVolume?: number;
  /** Overrides the style's default transition duration. */
  transitionDurationMs?: number;
  /**
   * How HARD cuts between main clips are softened, without overlapping them (the voice lives in the clips, so an
   * overlapping transition would double the audio and drift the captions). "blurZoom" (default): the outgoing clip
   * blurs and pushes in over its last frames, the incoming one arrives blurred and settles -- reads as a smooth
   * transition with a whoosh on top. "none": raw hard cut. The user wants no abrupt jumps: keep the default.
   */
  cutTransition?: "blurZoom" | "none";
  /** Overrides the style's b-roll fade (ms). Never below 250 ms: b-roll must not pop in/out abruptly. */
  brollFadeMs?: number;
  /** Rating / counter cards at the top of the safe zone (components/ScoreCard.tsx): "SUPLEMENTOS DEL SÚPER 1/10", "3/13". */
  scoreCards?: { label?: string; score?: string; tone?: "bad" | "mid" | "good" | "neutral"; atMs: number; durationMs: number; y?: number }[];
  /**
   * Optional title/hook banner (e.g. "POV: ..." style seen in real TikTok
   * UGC, or an opening title card like "LOS 7 ARCÁNGELES DE DIOS"). `text`
   * supports `\n` for a manual line break. By default it's a white rounded
   * box with bold black uppercase text, positioned near the top, shown for
   * the entire main-content duration -- override any of that with the
   * optional fields below to match a specific reference:
   * - `startMs`/`durationMs`: show it only for a window (e.g. just the
   *   opening ~3s hook line) instead of the whole video. Omit both for the
   *   original persistent-whole-video behavior.
   * - `position`: "top" (default, above the subject's head), "lower"
   *   (lower-third, roughly where word captions usually sit -- used when the
   *   reference's title card lives there instead) or "topEdge" (pinned to the
   *   very top of the frame, the "POV: ..." line of real TikTok/ELIDA UGC).
   * - `bg`: "white" (default, white box/black text), "black" (black
   *   box/white text) or "none" (no box: plain small bold text with a shadow,
   *   the unboxed POV title of the ADS ELIDA references; set `color` for the
   *   yellow variant seen in the car-skit ones).
   */
  title?: {
    text: string;
    startMs?: number;
    durationMs?: number;
    position?: "top" | "lower" | "topEdge";
    bg?: "white" | "black" | "none";
    /** Text color override. Default: black on white, white on black/none. */
    color?: string;
    /** Exact distance from the top in px (1080x1920), overriding `position` -- keep it off the face and in the safe zone. */
    topPx?: number;
  };
  /**
   * Optional big all-caps keyword callouts that flash briefly over the video
   * (e.g. "PROTECTOR", "CLARIDAD") to emphasize a theme word -- distinct from
   * the running word-by-word `captions`, and from the persistent/windowed
   * `title` above. Positioned near the top of the frame.
   */
  keywordCallouts?: {
    text: string;
    atMs: number;
    durationMs: number;
  }[];
  /**
   * Optional big proof-number punches (e.g. "$10,000", "30%", "+10,000
   * alumnos") -- a single dramatic stat slammed center-frame, distinct from
   * `keywordCallouts` (a theme word, smaller, near the top) and from the
   * running `captions` (spoken dialogue). Set `countFrom`/`countTo` to
   * animate a count-up instead of a static punch-in (money/results feeling
   * like they're climbing) -- in that case `text` is ignored, the display is
   * built from `prefix` + the counting number + `suffix`.
   */
  statCallouts?: {
    text: string;
    atMs: number;
    durationMs: number;
    countFrom?: number;
    countTo?: number;
    prefix?: string;
    suffix?: string;
    color?: string;
    /** Center position (default: dead center), size in px at 1080 wide, neon glow. */
    x?: number;
    y?: number;
    size?: number;
    glow?: boolean;
  }[];
  /**
   * Optional small rounded pill labels anchored to a corner (an offer/bonus
   * tag, a credential chip) -- transient, not persistent like `title`.
   */
  badges?: {
    text: string;
    atMs: number;
    durationMs: number;
    position?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
    bg?: string;
    color?: string;
    icon?: string;
  }[];
  /**
   * Optional pointer arrows aimed at something on screen (a UI element on a
   * screenshot insert, a price, a face). `x`/`y` is the TIP of the arrow in
   * the reference 1080x1920 frame.
   */
  arrows?: {
    atMs: number;
    durationMs: number;
    x: number;
    y: number;
    direction?: "up" | "down" | "left" | "right";
    length?: number;
    color?: string;
  }[];
  /**
   * Optional hand-drawn-marker-style circles/ellipses that draw themselves on
   * around a region of the frame (a word, a face, a UI element). `x`/`y` is
   * the CENTER; `width`/`height` are the full bounding box, not a radius --
   * easy to eyeball straight from a paused frame of the source video.
   */
  highlightCircles?: {
    atMs: number;
    durationMs: number;
    x: number;
    y: number;
    width: number;
    height: number;
    color?: string;
    strokeWidth?: number;
  }[];
  /**
   * Optional animated line/area "proof of results" chart with a glowing dot
   * chasing the line and a floating counter tracking the current value --
   * the revenue-graph shot common in business/money VSLs. `points` is any
   * list of raw values (not normalized); at most one per video.
   */
  revenueChart?: {
    atMs: number;
    durationMs: number;
    points: number[];
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    color?: string;
    counterPrefix?: string;
    counterSuffix?: string;
    label?: string;
  };
  /**
   * Optional dark vignette wash for a heavier/more dramatic section. Omit
   * `atMs`/`durationMs` for the whole video, or scope it to just part of it.
   */
  vignette?: {
    atMs?: number;
    durationMs?: number;
    intensity?: number;
  };
  /** Logos/emojis that pop in near the speaker in sync with a word (see components/Sticker.tsx). */
  stickers?: { atMs: number; durationMs: number; x: number; y: number; emoji?: string; src?: string; size?: number; rotate?: number }[];
  /** Numbered list down the left edge whose slots fill with an icon as each item is named (components/ListSidebar.tsx). At most one per video. */
  listSidebar?: {
    startMs: number;
    endMs: number;
    items: { atMs: number; emoji?: string; src?: string; label?: string }[];
    x?: number;
    y?: number;
    gap?: number;
  };
  /** Floating screenshot/proof cards (payment notifications, dashboards). `src` relative to remotion/public/. Only real screenshots the user provided. */
  imageCards?: { src: string; atMs: number; durationMs: number; x: number; y: number; width?: number; rotate?: number }[];
  /** Instagram-style "Hazme una pregunta" sticker. Omit atMs/durationMs to keep it the whole video. */
  questionStickers?: { text: string; header?: string; atMs?: number; durationMs?: number; x?: number; y?: number; width?: number }[];
  /** Circular picture-in-picture bubbles (image or muted video, relative to remotion/public/). */
  bubbles?: { src: string; atMs: number; durationMs: number; x: number; y: number; size?: number; borderColor?: string }[];
  /** Name + credential tags for interviewees/experts. */
  lowerThirds?: { name: string; subtitle?: string; atMs: number; durationMs: number; accent?: string; bottomPx?: number }[];
  /** Persistent channel/brand marks in a top corner. */
  brandBugs?: { text?: string; src?: string; position?: "top-left" | "top-right"; atMs?: number; durationMs?: number; height?: number }[];
  /** VSL: the buy/apply button hovering over the presenter, re-launched at each CTA moment (components/CtaButton.tsx). */
  ctaButtons?: { text: string; atMs: number; durationMs: number; y?: number; color?: string; textColor?: string; chevrons?: boolean; chevronColor?: string }[];
  /** VSL: a real decreasing timer for the closing section (components/CountdownTimer.tsx). Only if the offer has a real deadline. */
  countdownTimer?: { startMs: number; endMs: number; fromSeconds: number; label?: string; style?: "bar" | "corner"; withHours?: boolean; color?: string };
  /** VSL: value stack / price anchor graphic (components/PriceStack.tsx). Real prices only. */
  priceStacks?: { atMs: number; durationMs: number; title?: string; lines: { label: string; price: string }[]; totalLabel?: string; total?: string; strikeTotal?: boolean; layout?: "panel" | "overlay"; bg?: string; accent?: string; staggerMs?: number }[];
  /** VSL: risk-reversal badge (components/GuaranteeSeal.tsx). Real guarantee only. */
  guaranteeSeals?: { atMs: number; durationMs: number; big: string; small?: string; caption?: string; look?: "dark" | "gold" }[];
  /** VSL: full-frame kinetic text cards / chapter breaks / quotes (components/TitleCard.tsx). */
  titleCards?: { text: string; atMs: number; durationMs: number; bg?: string; dim?: number; color?: string; look?: "sans" | "serif" | "quote"; fontSize?: number; position?: "center" | "top" | "bottom" }[];
  /** VSL: fan of the user's proof screenshots over a gradient backdrop (components/ProofStack.tsx). */
  proofStacks?: { images: string[]; atMs: number; durationMs: number; backdrop?: "blue" | "purple" | "dark"; staggerMs?: number; cardWidth?: number }[];
  /** VSL: comparison table revealed row by row (components/ComparisonTable.tsx). */
  comparisonTables?: { atMs: number; durationMs: number; title?: string; columns: string[]; rows: { label: string; cells: { text: string; tone?: "good" | "mid" | "bad" | "neutral" }[] }[]; highlightFirst?: boolean; staggerMs?: number }[];
  /** Virtual-camera reframing of a wide source (applies to every clip; times are SOURCE seconds). */
  reframe?: Reframe;
  /** Beat pulses (zoom/flash/shake) over the picture layers -- see scripts/make_beat_edit.py. */
  pulses?: Pulse[];
  /** Headline text drawn BEHIND the presenter (needs mattes from scripts/vision_analyze.py; hard-cut styles only). */
  behindText?: BehindTextItem[];
  /** Music start offset in seconds: >0 skips into the track (e.g. to land a drop on a key moment), <0 delays it. */
  musicOffsetSeconds?: number;
  /** Unified look over main footage + b-roll (see Grade). */
  grade?: Grade;
  /** Sound-design hits (whooshes, pops, hits) placed on events; use scripts/add_sfx.py to generate them. */
  sfx?: SfxHit[];
  /** Duration of the MAIN content only -- excludes `cta` below, which is added on top. */
  totalDurationInFrames: number;
  /**
   * Optional 5-second countdown CTA appended after the main content ends
   * (shared across all styles). `text` supports `\n` for a manual line
   * break, matching the reference layout (2 short lines). `durationInFrames`
   * defaults to 150 (5s at 30fps) if omitted.
   */
  cta?: {
    text: string;
    backgroundSrc: string;
    musicSrc?: string;
    durationInFrames?: number;
  };
};

export const DEFAULT_CTA_DURATION_IN_FRAMES = 150;

/**
 * No-assets fixture so `remotion render`/`remotion studio` work without a
 * real job file -- used as a smoke test for the pipeline itself.
 */
export const defaultEditPlan: EditPlan = {
  fps: 30,
  width: 1080,
  height: 1920,
  clips: [],
  captions: [
    { text: "PREVIEW", startMs: 0, endMs: 1200 },
    { text: "SIN", startMs: 1200, endMs: 1600 },
    { text: "CLIPS", startMs: 1600, endMs: 2200 },
  ],
  broll: [],
  totalDurationInFrames: 90,
};
