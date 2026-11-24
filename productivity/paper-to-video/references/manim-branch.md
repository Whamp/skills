# Manim Community Branch

Use this branch only when the user explicitly requests Manim output (`.py` Manim scene) instead of the default HTML/SVG renderer.

## Check prerequisites first

Before writing any Manim scene, verify all required binaries:

```bash
for cmd in manim pdflatex dvisvgm ffmpeg ffprobe; do
  command -v "$cmd" || echo "MISSING: $cmd"
done
```

- If `manim` is missing, `uv run --with manim manim --version` can supply it when Cairo and Pango development headers are installed.
- If `pdflatex` or `dvisvgm` is missing, `MathTex` and `Tex` will fail. Inform the user and either install TeX Live or fall back to the default HTML/SVG + KaTeX renderer.

## Sync Manim directly to `timeline.json`

Build audio first with `scripts/build_narration.py` so `timeline.json` and `narration.m4a` exist before writing the Manim scene. Inside `construct(self)`, track elapsed scene time and pace every beat to its measured `end_s`:

```python
import json
from pathlib import Path
from manim import *

class PaperExplainer(Scene):
    def construct(self) -> None:
        self.camera.background_color = BLACK
        timeline = json.loads(Path("timeline.json").read_text(encoding="utf-8"))
        beats = {beat["id"]: beat for beat in timeline["beats"]}
        cursor = 0.0

        def finish_beat(beat_id: str, spent: float) -> None:
            nonlocal cursor
            target = beats[beat_id]["end_s"]
            remaining = target - (cursor + spent)
            if remaining > 0.02:
                self.wait(remaining)
            cursor = max(cursor + spent, target)

        # Example beat
        title = Text(timeline["title"], font_size=40).to_edge(UP, buff=0.45)
        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.8)
        finish_beat("hook", 0.8)
```

## Render, check, and mux

1. Render a fast low-res pass (`-ql`) or save beat keyframes with `-s` / `ffmpeg` frame extraction to inspect layout and math before full HD.
2. Render 1080p 30fps (`manim -qh --fps 30 scene.py PaperExplainer`).
3. Mux the rendered video with `narration.m4a`:

```bash
ffmpeg -y -i media/videos/scene/1080p30/PaperExplainer.mp4 -i narration.m4a \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart final.mp4
```

Apply the same visual grammar ([visual-grammar.md](visual-grammar.md)): pure black background, persistent top spine pills, color-coded symbols, real paper data, and keyframe inspection before delivery.
