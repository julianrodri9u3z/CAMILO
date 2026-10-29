#!/usr/bin/env python3
"""
"Ears" for the edit: asks a video+audio model (TwelveLabs Pegasus, key already in .env) to LISTEN to a
render and report what it hears -- sound effects and when, mix balance, anything harsh, cheap or broken.

STATUS: EXPERIMENTAL / NOT RELIABLE. Two tests gave inconsistent answers (it once reported no music in a mix that had music
and never reported the sound effects that were measurably present). Do not use it to approve or reject a mix; use the numeric
checks (qa_render.py, beat_grid.py, per-effect level vs mix) and ask the user to listen.

Why: I cannot hear. Numbers (qa_render.py: LUFS, peaks, silence) say the mix is technically sound;
this adds a second, perceptual opinion. Treat it as a hint, not ground truth: the model can hallucinate
sounds and its timestamps are approximate. Confirm anything it flags with the numeric tools
(add_sfx plan times, beat_grid.py) and, for the final call, ask the user to listen.

Usage:
  python3 listen_check.py --video final.mp4 [--out report.txt] [--question "extra thing to check"]
"""
import argparse, importlib.util, os, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ar", os.path.join(HERE, "analyze_reference.py"))
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)

PROMPT = """You are an audio post-production supervisor listening to this short-form video ad/clip. Report ONLY what you actually hear.
1. MIX: describe voice, music and any other layers. Is the voice always clearly intelligible? Is the music too loud, too quiet, or just right under the voice?
2. SOUND EFFECTS: list every non-speech, non-music sound effect you hear (whoosh, pop, click, impact/boom, riser, ding...), each with an approximate timestamp (mm:ss) and whether it sounds natural/professional or synthetic/cheap/harsh. If you hear none, say so.
3. PROBLEMS: clipping/distortion, abrupt cuts or pops, pumping, noise, awkward silences, sounds that mask the voice.
4. SYNC: do the effects land on visual events (graphics appearing, b-roll cuts), or do they feel early/late?
5. Overall verdict in one sentence: would a viewer think this was professionally sound-designed?
Answer concisely as a numbered list. If unsure about something, say 'unsure' instead of guessing.{extra}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out")
    ap.add_argument("--question", default="")
    ap.add_argument("--prompt", help="use this full prompt instead of the audio-supervisor checklist (e.g. to ask what the video says / shows)")
    a = ap.parse_args()
    key = ar.get_key("TWELVELABS_KEY", "twelvelabs.io")
    if not key:
        sys.exit("TWELVELABS_KEY missing in editar-anuncios/.env")
    H = {"x-api-key": key}
    B = "https://api.twelvelabs.io/v1.3"
    index_id = ar.get_or_create_index(H, B, "editar-anuncios")
    with open(a.video, "rb") as f:
        task = requests.post(f"{B}/tasks", headers=H, data={"index_id": index_id}, files={"video_file": f})
    if task.status_code >= 300:
        sys.exit(f"TwelveLabs rejected the upload ({task.status_code}): {task.text[:300]}  (needs a real video of at least ~360p; for an audio-only check mux the audio onto a 1280x720 dark video)")
    tid = task.json()["_id"]
    print("uploading/processing in TwelveLabs...")
    vid, t0 = None, time.time()
    while time.time() - t0 < 900:
        st = requests.get(f"{B}/tasks/{tid}", headers=H).json()
        if st.get("status") == "ready":
            vid = st["video_id"]
            break
        if st.get("status") == "failed":
            sys.exit(f"TwelveLabs failed: {st}")
        time.sleep(8)
    if not vid:
        sys.exit("timeout waiting for TwelveLabs")
    info = requests.get(f"{B}/indexes/{index_id}/videos/{vid}", headers=H).json()
    asset = info.get("asset_id", vid)
    r = requests.post(f"{B}/analyze", headers=H, timeout=300, json={
        "model_name": "pegasus1.5", "video": {"type": "asset_id", "asset_id": asset},
        "prompt_v2": {"input_text": a.prompt or PROMPT.format(extra=("\n6. ALSO: " + a.question) if a.question else "")},
        "temperature": 0.2, "stream": False})
    r.raise_for_status()
    text = r.json().get("data", "")
    print(text)
    if a.out:
        open(a.out, "w").write(text)


if __name__ == "__main__":
    main()
