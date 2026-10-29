/**
 * Per-style tuning knobs. Values here should track references/estilos/*.json
 * in the skill folder (the learned profile) -- when Claude updates a style's
 * profile after analyzing new reference ads, the matching entry here should
 * be nudged to stay consistent. This file is what the Remotion side actually
 * reads at render time; the JSON profile is the source of truth for reasoning
 * and reporting.
 */

export type CaptionVariant =
  | "elegant" | "bold" | "bouncy" | "plain" | "karaoke" | "highlight" | "bar"
  // Added 2026-09 from the ADS ELIDA / ADS GAIA / JUAN CARRIZO / loose references (see references/motion-graphics.md):
  | "active" | "chip" | "wordBox" | "native" | "boxed" | "kinetic";

/**
 * "fade"/"none"/"slide" are hand-rolled in Edit.tsx (predate this list). The
 * rest are straight from @remotion/transitions' `presentations/` -- already
 * an installed dependency, unused until 2026-09 -- so adding one here is
 * free (no new deps, battle-tested code): see Edit.tsx's `presentationFor`
 * for the mapping and references/realism... er, references/estilos/*.md for
 * which one actually fits an observed reference before assigning it as a
 * style's default. Good starting points by mood: "zoomBlur"/"crossZoom" for
 * energetic UGC/TikTok, "filmBurn" for cinematic/chisme, "dreamyZoom" for
 * spiritual/voz-en-off, "wipe"/"iris" for a gossip-style reveal.
 */
export type TransitionKind =
  | "fade" | "none" | "slide"
  | "zoomBlur" | "crossZoom" | "wipe" | "iris" | "filmBurn" | "dreamyZoom" | "pushCut";

export type StyleConfig = {
  transition: TransitionKind;
  transitionDurationMs: number;
  captionVariant: CaptionVariant;
  captionColor: string;
  captionHighlightColor: string;
  captionFontFamily: string;
  captionPositionFromBottom: number; // px, at 1080x1920 reference size
  brollFadeMs: number;
  brollZoomPunchIn: boolean;
  /** Same punch-in zoom BrollLayer already does, applied to the MAIN clip on
   * every cut instead -- a big lever for "energetic UGC" pacing that was
   * previously broll-only. Off by default for styles whose reference footage
   * showed a locked/static main shot (podcast, cinematografico). */
  mainClipZoomPunch: boolean;
  musicDuckedVolume: number;
  musicFullVolume: number;
};

export const CINEMATOGRAFICO: StyleConfig = {
  transition: "fade",
  transitionDurationMs: 500,
  captionVariant: "elegant",
  captionColor: "#F5F1E8",
  captionHighlightColor: "#F5F1E8",
  captionFontFamily: "Georgia, 'Times New Roman', serif",
  captionPositionFromBottom: 220,
  brollFadeMs: 600,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.05,
  musicFullVolume: 0.2,
};

export const UGC_IA: StyleConfig = {
  transition: "none",
  transitionDurationMs: 80,
  captionVariant: "bold",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FFE600",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 460,
  brollFadeMs: 150,
  brollZoomPunchIn: true,
  mainClipZoomPunch: true,
  musicDuckedVolume: 0.04,
  musicFullVolume: 0.15,
};

export const TIKTOK: StyleConfig = {
  transition: "slide",
  transitionDurationMs: 180,
  captionVariant: "bouncy",
  // Black outline / white fill -- matches the plain bold-white-caption look
  // seen across real TikTok UGC references (e.g. @immortal.unc), not a
  // colored highlight. Updated 2026-08 from a manual reference screenshot
  // (no downloadable video, so no analyze_reference.py metrics run -- see
  // references/estilos/tiktok.md for the note).
  captionColor: "#000000",
  captionHighlightColor: "#FFFFFF",
  captionFontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
  captionPositionFromBottom: 380,
  brollFadeMs: 100,
  brollZoomPunchIn: true,
  mainClipZoomPunch: true,
  musicDuckedVolume: 0.06,
  musicFullVolume: 0.25,
};

// Seed guess -- no reference ads analyzed yet for this style. Refine once
// references/estilos/chisme.json has n_ejemplos_analizados > 0.
export const CHISME: StyleConfig = {
  transition: "none",
  transitionDurationMs: 100,
  captionVariant: "bold",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FF3B30",
  captionFontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
  captionPositionFromBottom: 420,
  brollFadeMs: 200,
  brollZoomPunchIn: true,
  mainClipZoomPunch: true,
  musicDuckedVolume: 0.05,
  musicFullVolume: 0.18,
};

// Updated 2026-09 from a real reference (Daniel Dueñas, "Los 7 arcángeles de
// Dios") -- word-by-word, plain white text, mixed case (not forced uppercase),
// no stroke/box, no bounce/scale animation, just a quick fade. Distinct enough
// from the other 3 variants (all either phrase-grouped or heavy-stroke/bouncy)
// that it got its own "plain" CaptionVariant rather than being approximated
// with an existing one. No downloadable-metrics run yet (analyze_reference.py
// wasn't run against this one), so n_ejemplos_analizados in podcast.json is
// still not bumped -- this is a manual-observation update, same category as
// the tiktok.md note about @immortal.unc.
export const PODCAST: StyleConfig = {
  transition: "fade",
  transitionDurationMs: 350,
  captionVariant: "plain",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FFFFFF",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 300,
  brollFadeMs: 400,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.03,
  musicFullVolume: 0.1,
};

// Seed guess -- no reference ads analyzed yet for this style. Refine once
// references/estilos/voz-en-off-ugc.json has n_ejemplos_analizados > 0.
export const VOZ_EN_OFF_UGC: StyleConfig = {
  transition: "fade",
  transitionDurationMs: 250,
  captionVariant: "bold",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FFE600",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 420,
  brollFadeMs: 300,
  brollZoomPunchIn: true,
  mainClipZoomPunch: true,
  musicDuckedVolume: 0.05,
  musicFullVolume: 0.16,
};

// Learned 2026-09 from a real spiritual/angelical voiceover ad (no on-camera
// speaker -- AI-illustrated b-roll, narration only): short phrase stays on
// screen and only the word being spoken lights up cyan, uppercase, no
// stroke/bounce/scale -- distinct enough from "bold" (one giant word, nothing
// else visible) and "plain" (one word, no highlight at all) that it got its
// own "karaoke" CaptionVariant, same pattern as podcast.json getting "plain".
// Seed guess for everything except the caption look itself (colors/timing
// pulled directly from the reference; transition/broll/music not yet
// validated against a second example) -- refine once
// references/estilos/espiritual-voz-off.json has n_ejemplos_analizados > 0.
// Learned 2026-09 from a real numerology/UGC ad (real handheld footage of a
// hand writing a "sacred code" on paper, not AI-generated) -- short phrase on
// a solid yellow rounded box, bold black text, mixed case (not uppercase),
// one phrase group at a time. Distinct from ESPIRITUAL_VOZ_OFF's "karaoke"
// (no box, cyan per-word highlight, AI-illustrated visuals) -- same broad
// niche family, different real execution. Seed guess beyond the caption look
// itself; refine once references/estilos/codigos-voz-off.json has
// n_ejemplos_analizados > 0.
export const CODIGOS_VOZ_OFF: StyleConfig = {
  transition: "fade",
  transitionDurationMs: 250,
  captionVariant: "highlight",
  captionColor: "#000000",
  captionHighlightColor: "#F5D300",
  captionFontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
  captionPositionFromBottom: 380,
  brollFadeMs: 300,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.04,
  musicFullVolume: 0.14,
};

export const ESPIRITUAL_VOZ_OFF: StyleConfig = {
  transition: "fade",
  transitionDurationMs: 300,
  captionVariant: "karaoke",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#22D3EE",
  captionFontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
  // NOTE: the "karaoke" variant anchors from the TOP (Captions.tsx uses
  // flex-start/marginTop for it specifically), not the bottom like every
  // other variant -- the real reference sits at ~30% down from the top of
  // the frame, nowhere near the bottom third. Despite the field name, this
  // number is "px from top" here.
  captionPositionFromBottom: 580,
  brollFadeMs: 500,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.04,
  musicFullVolume: 0.15,
};

// Learned 2026-09 from 12 real creator-UGC references (ADS ELIDA affiliate ads +
// loose IG/TikTok reels): mostly PLANO SECUENCIA (0-2 cuts/min; the whole video
// is one continuous take with overlays doing the pacing) or a few hard cuts;
// caption look varies but the most common (about a third) is mixed-case, heavy
// black outline, the word being spoken in yellow -- the "active" variant.
// Overlays are the identity of this style: title without a box ("POV: ..."),
// stickers/logos, numbered list sidebar, floating proof cards, question sticker,
// PIP bubbles (see references/motion-graphics.md). No zoom punch by default:
// the footage is one long take, not cuts to punch across. See
// references/estilos/ugc-creador.md before assuming any of this.
export const UGC_CREADOR: StyleConfig = {
  transition: "none",
  transitionDurationMs: 80,
  captionVariant: "active",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FFE600",
  captionFontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
  captionPositionFromBottom: 430,
  brollFadeMs: 150,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.04,
  musicFullVolume: 0.12,
};

// Learned 2026-09 from 2 real JUAN CARRIZO reels (only 2 -- thin evidence, treat
// as a candidate style): 48-55 hard cuts/min over lifestyle b-roll, kinetic
// typography (lowercase sans, words stacked, one huge emphasized word), no
// outline/box on the text. See references/estilos/editorial-lifestyle.md.
export const EDITORIAL_LIFESTYLE: StyleConfig = {
  transition: "none",
  transitionDurationMs: 60,
  captionVariant: "kinetic",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FFFFFF",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 520,
  brollFadeMs: 100,
  brollZoomPunchIn: true,
  mainClipZoomPunch: true,
  musicDuckedVolume: 0.05,
  musicFullVolume: 0.22,
};

// Learned 2026-09 from 7 ADS GAIA streaming-platform trailers (brand/broadcast
// production, not creator content): mostly hard cuts with ~20% crossfades,
// cinematic score, expert interviews with lower-thirds, persistent brand bug,
// end card. Subtitles are optional (4 of 7 have none); when present, a tight
// white box with black text (or, in one, white caps with purple boxes on key
// words). Half are 16:9 horizontal, half reformatted 9:16 -- ask which the
// placement needs. See references/estilos/trailer-documental.md.
export const TRAILER_DOCUMENTAL: StyleConfig = {
  transition: "none",
  transitionDurationMs: 350,
  captionVariant: "boxed",
  captionColor: "#000000",
  captionHighlightColor: "#FFFFFF",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 300,
  brollFadeMs: 450,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.06,
  musicFullVolume: 0.25,
};

// Learned 2026-09 from 5 real VSLs (UpLevel 4.6 min, Vida Sem Dieta 12.7, ELIDA bio 18,
// FRANQUICIA IA 31, an 8-item ranking 6.2): a presenter talking to camera cut with
// hard cuts + punch-in crops, roughly 6-18 cuts/min, sentence captions, and the
// overlay layer (proof cards, title cards, price stack, guarantee, timer, CTA button)
// doing the persuasion work. Transitions are hard cuts; b-roll is cut, not faded.
// captionVariant "native" (white sentence, soft shadow) is the Vida Sem Dieta look;
// UpLevel used a translucent gray box ("boxed" with an rgba highlightColor), the
// creators' VSLs used small black boxes -- choose per reference. Read
// ~/.claude/skills/editar-vsl/SKILL.md before using this style.
export const VSL: StyleConfig = {
  transition: "none",
  transitionDurationMs: 60,
  captionVariant: "native",
  captionColor: "#FFFFFF",
  captionHighlightColor: "rgba(0,0,0,0.55)",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 330,
  brollFadeMs: 200,
  brollZoomPunchIn: true,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.035,
  musicFullVolume: 0.12,
};

// 2026-10 test edit on a real podcast interview clip (single speaker, mid-shot, emotional
// storytelling). Not learned from a reference set -- built from the existing pieces:
// kinetic lowercase captions (one phrase stacked bottom-left, flagged words big), hard cuts,
// calm b-roll (no punch-in), very quiet music under the voice. Refine after real references.
export const PODCAST_CLIP: StyleConfig = {
  transition: "none",
  transitionDurationMs: 60,
  captionVariant: "kinetic",
  captionColor: "#FFFFFF",
  captionHighlightColor: "#FFD84A",
  captionFontFamily: "'Helvetica Neue', Arial, sans-serif",
  captionPositionFromBottom: 300,
  brollFadeMs: 300,
  brollZoomPunchIn: false,
  mainClipZoomPunch: false,
  musicDuckedVolume: 0.05,
  musicFullVolume: 0.16,
};
