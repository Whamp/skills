---
name: paper-to-video
description: Turn a research paper (arXiv URL/ID, PDF, or paper note) into a concise 3Blue1Brown-style animated explainer video with synchronized voiceover, visual math, and verified data plots. Use when asked to make a 3Blue1Brown video, animated explainer video, or narrated visual summary of a paper.
license: MIT
---

# Paper to Video

Produce a crisp, ~2-minute 3Blue1Brown-style animated explainer video (1920×1080 MP4) with synchronized voiceover from a research paper. Build audio first so every visual transition locks to measured speech timestamps, audit and inspect every beat's keyframe before full rendering, and show only verified paper claims and numbers.

**Inputs.** One paper source: an arXiv URL or ID, a local PDF, or an existing paper note that links to the primary paper. Optional: target duration (default `100–130s`), audience depth, voice, or output directory (default to a durable path outside any Git repo, e.g. `~/Videos/paper-to-video/<slug>/`, unless the user specifies another path).

## Steps

### 1. Read the primary paper and inspect its figures

Read the actual paper, not just an abstract or social post.

- **Online arXiv papers:** fetch `https://arxiv.org/html/<id>` (or the LaTeX source) first so equations, symbols, and tables stay exact without PDF column-extraction artifacts.
- **Local PDFs:** extract text without form-feed page breaks (`pdftotext -nopgbrk paper.pdf paper.txt`, or strip `\f` control bytes) before reading, because raw `pdftotext` form feeds can make file readers reject the output as binary and garble multi-column math.
- **Original figures:** inspect the paper's key figure pages directly (read the PDF pages visually or render them with `pdftoppm -png -r 150`) so you can faithfully reproduce real scaling curves, training trajectories, and architecture diagrams rather than falling back to bar charts alone.
- **Paper notes:** when starting from an existing note, read both the note (for caveats and focus) and the primary paper (for exact equations, axes, and numbers).

Write a brief working sheet in the output directory (not in chat):

- **Thesis:** the paper's core claim in one plain sentence.
- **Citation:** exact authors, year, and arXiv ID or venue (`Author et al. Year · arXiv:XXXX.XXXXX`).
- **Visual spine:** 2–4 questions, hypotheses, or components that stay visible across the video as verdicts fill in.
- **Verified facts:** every equation, metric, baseline, model scale, compute budget, and figure value you plan to display, each traced to its table, figure, or section. Include any material caveat that qualifies the headline result.

State the qualitative trend instead of fabricating decimals when a figure lacks printed numbers and cannot be read reliably.

**Done when** you have inspected the primary paper's text, tables, and key figures directly and saved the thesis, citation, 2–4 spine items, and a verified fact sheet with zero unverified numbers.

### 2. Draft the beat script (`beats.json`)

Write a tight spoken script aimed at `100–130 seconds` (`220–290 words` at ~140 wpm) unless the user asked for a different length. Start straight into the concrete mechanism on second 0 — skip greetings, channel intros, and throat-clearing.

Split the script into 10–18 **beats** in `<out-dir>/beats.json`:

```json
{
  "title": "Short Paper Title",
  "citation": "Author et al. 2026 · arXiv:XXXX.XXXXX",
  "voice": "en-GB-RyanNeural",
  "beats": [
    {
      "id": "hook",
      "text": "Fixed BPE tokenization breaks on noisy text at 1.3B scale.",
      "spoken_text": "Fixed B P E tokenization breaks on noisy text at one point three billion scale.",
      "pause_after_s": 0.35,
      "visual_cue": "What enters, morphs, or highlights during this beat"
    }
  ]
}
```

- Keep each beat to one spoken thought (roughly 10–25 words) paired with one visual move.
- Use optional `spoken_text` whenever exact paper notation (`BPE`, `1.3B`, `XWinograd`, `FineWeb-Edu`, `FLOP`) needs cleaner TTS pronunciation while `text` (or optional `subtitle_text`) keeps exact notation in subtitles.
- Use `pause_after_s` of `0.25–0.45` between connected sentences and `0.60–0.85` at act boundaries.

Validate structure and pacing with:

```bash
python3 scripts/build_narration.py <out-dir>/beats.json --out-dir <out-dir> --dry-run
```

Resolve `scripts/build_narration.py` relative to this `SKILL.md`.

**Done when** `--dry-run` passes, total estimated duration fits the target window (`100–130s` by default), technical terms have clean pronunciation, and every quantitative claim in `beats.json` matches step 1.

### 3. Build audio first (`timeline.json` and `narration.m4a`)

Synthesize the voiceover and measure exact beat timestamps before writing any animation timing:

```bash
python3 scripts/build_narration.py <out-dir>/beats.json --out-dir <out-dir>
```

- Uses `edge-tts` by default (falls back to `uvx --from edge-tts edge-tts` when not on `PATH`).
- Copies bundled `assets/stage_helpers.js` into `<out-dir>/stage_helpers.js` (unless already present) so `scene.html` can import `window.PaperStage` locally.
- Pass `--audio-dir <dir>` to assemble pre-generated audio clips (`<beat-id>.mp3`/`.wav`/`.m4a`) from another TTS engine or human recording.
- Pass `--silent` only when offline or when the user asks for a silent subtitled video; burn `subtitles.srt` during step 6.

Inspect the emitted `timeline.json` summary (`total_duration_s`, per-beat `start_s` / `audio_end_s` / `end_s`, and `spoken_wpm`). If pacing runs too long or short, tighten `beats.json` and rebuild audio before animating.

**Done when** `<out-dir>/timeline.json`, `<out-dir>/subtitles.vtt`, `<out-dir>/subtitles.srt`, and `<out-dir>/narration.m4a` (unless `--silent`) exist and total duration matches the target pacing.

### 4. Author the deterministic scene (`scene.html`)

Read [visual grammar](references/visual-grammar.md) and [scene API](references/scene-api.md) before authoring `<out-dir>/scene.html`.

- Only switch to [the Manim branch](references/manim-branch.md) when the user explicitly requests Manim and `manim`, `pdflatex`, and `dvisvgm` are installed.

Build `<out-dir>/scene.html` as a self-contained 1920×1080 dark-canvas animation driven exclusively by `window.renderAt(t)` and `window.__TIMELINE__`:

- Load `./stage_helpers.js` (`window.PaperStage`) for `getBBox()`-aware `drawSpine`, `drawBarChart`, `drawLineChart`, `placeBadgeRightOf`, and `fitLabelInBox` so labels never clip or collide.
- Keep the persistent **spine** bar visible across acts so the viewer tracks which hypotheses or components are optional, key, or disproved.
- Morph persistent diagrams and charts in place across adjacent acts rather than fading to black between unrelated slides.
- Pair every mechanism change with the paper's measured data (scaling curves, bar charts, or latency deltas) with labeled axes, units, and baselines.
- Render equations with KaTeX (load `katex.min.js` synchronously without `defer`) and color-code key symbols to match the diagram.
- Drive every animated property from `t` inside `renderAt(t)`; omit CSS `transition` and `@keyframes` so frame stepping is deterministic.

**Done when** `<out-dir>/scene.html` covers every beat in `timeline.json` from `0` to `total_duration_s` and supports `?preview=1` interactive scrubbing.

### 5. Run the keyframe audit and visual check before full rendering

Capture one settled 1920×1080 PNG per beat plus a combined contact sheet, running the built-in KaTeX and SVG/DOM layout audit:

```bash
uv run --with playwright python3 scripts/render_video.py <out-dir>/scene.html \
  --timeline <out-dir>/timeline.json \
  --keyframes \
  --keyframes-dir <out-dir>/keyframes
```

`--keyframes` automatically fails (exit code `1`, `"ok": false`, while still saving all PNGs and `contact_sheet.png`) if KaTeX fails to render on any `.math-node`, any visible text or equation crosses the `72×56 px` safe margin, visible text boxes overlap, or visible text collides with a `<rect>` or `<polygon>` border. Mark purely decorative overlapping shapes with `data-audit-ignore="true"` only when the overlap is intentional.

After the automated audit passes (`"audit": {"passed": true}`), inspect `<out-dir>/keyframes/contact_sheet.png` and individual beat PNGs for complex math or charts. Verify:

- Zero overlapping text, colliding labels, or clipped equations.
- Labels and axis numbers stay legible at chat playback width (`>= 24 px` labels, `>= 28 px` math).
- Every displayed number, unit, baseline, and citation matches step 1.
- Visual continuity holds from beat to beat (persistent spine updates, smooth in-place morphing).

Fix every defect in `scene.html` and re-run `--keyframes` until both the automated audit and visual inspection pass.

**Done when** `--keyframes` reports `"ok": true` with zero audit issues and every beat keyframe has been visually inspected with zero layout, typography, math, or data defects.

### 6. Render and spot-check the final MP4

Render the full 1920×1080 H.264 MP4 muxed with `narration.m4a` (defaults to `--workers 4` parallel Chromium capture with lossless segment concat):

```bash
uv run --with playwright python3 scripts/render_video.py <out-dir>/scene.html \
  --timeline <out-dir>/timeline.json \
  --audio <out-dir>/narration.m4a \
  --out <out-dir>/<slug>.mp4
```

Add `--burn-subtitles <out-dir>/subtitles.srt` when rendering a `--silent` video or when the user asks for burned-in captions.

Verify the finished MP4 before handoff:

1. Confirm the script's JSON output reports `"ok": true`, dimensions `1920x1080`, expected frame count, and video/audio duration agreement within `0.2s`.
2. Spot-check the actual encoded MP4 by extracting 2–3 frames (including at least one mid-transition frame between beats) with `ffmpeg -ss <t> -i <out-dir>/<slug>.mp4 -frames:v 1 <out-dir>/spot_<n>.png` and visually inspecting them to confirm encoding sharpness, smooth mid-transition morphing, and absence of muxing artifacts.
3. Present the final MP4 directly in the reply (embedded when the interface supports video, plus its durable absolute path), along with the paper citation, duration, and the interactive `scene.html?preview=1` path.

**Done when** the rendered MP4 passes `ffprobe` verification and mid-transition frame spot-checking, and has been presented to the user with its citation and durable artifact paths.
