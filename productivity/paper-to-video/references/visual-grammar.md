# Visual Grammar (3Blue1Brown / alphaXiv Style)

Use this visual system for every `scene.html` explainer so the output reads like a crisp mathematical animation rather than a slide deck.

## Canvas and safe margins

- Fixed stage: `1920 × 1080` (16:9 landscape), background `#000000`.
- Outer safe margin: keep all text, arrows, and axis ticks inside `x ∈ [72, 1848]`, `y ∈ [56, 1024]`.
- Keep generous black space (`>= 30%` of the frame) so the viewer's eye lands immediately on the active mechanism.

## Semantic color palette

Assign each color one consistent meaning across the entire video:

| Role | Hex | Usage |
| --- | --- | --- |
| Canvas | `#000000` | Pure black stage |
| Primary ink | `#F5F7FA` | Main labels, equations, active outlines |
| Muted ink | `#8B949E` | Axis ticks, subtitles, dimmed/rejected options |
| Structural stroke | `#30363D` | Box borders, dividers, inactive layers |
| Hero accent (3b1b blue) | `#4DA6FF` | The paper's core mechanism, winning bar/curve, active spine pill |
| Hero soft fill | `rgba(77, 166, 255, 0.16)` | Highlighted module fills and callout badges |
| Contrast accent (amber) | `#F59E0B` | Baseline, ablated/failing method, error or compute penalty |
| Secondary highlight (emerald) | `#34D399` | Secondary gain, proof milestone, or target region |

Reserve red/coral (`#F87171`) strictly for failure markers or regressions. Never cycle rainbow colors arbitrarily.

## Persistent visual spine

Place 2–4 compact pills across the top band (`y = 44..116`) representing the paper's decomposition, hypotheses, or claims:

- Start neutral (subtle white/gray border).
- Highlight the currently tested pill with `#4DA6FF` border and subtle glow.
- Attach a small verdict badge directly beneath each pill once the paper resolves it (`optional`, `key`, `proved`, `fails`), dimming resolved non-key pills so the winner stands out visually.

Keeping the spine visible across Acts 2–4 gives the viewer an effortless map of where they are in the argument.

## Continuous spatial morphing

Treat the stage as one continuous mathematical whiteboard:

- Keep shared actors on stage and move, scale, or transform them between beats (e.g., an input grid splits into patches, one patch flattens into a token vector, the backbone expands into its layer stack, one layer zooms open into its block diagram).
- When testing an ablation, transform the affected box in place while revealing the resulting bar or curve right beside or beneath it.
- Avoid bullet-list slides, prose paragraphs, or hard cuts to unrelated layouts.

## Four-act 2-minute narrative arc

| Act | Time | Purpose | Visual move |
| --- | --- | --- | --- |
| 1. Mechanism hook | `0:00–0:20` | Show the concrete object and central question immediately | Build the input/system diagram; reveal the 2–4 spine pills |
| 2. Controlled test | `0:20–0:50` | State the fair comparison rule and test the first hypothesis | Show the controlled metric/equation + first ablation bar chart in place |
| 3. Core insight | `0:50–1:25` | Zoom into the paper's key mechanism or theorem | Morph system box into layer/math view; reveal color-coded equation |
| 4. Proof & takeaway | `1:25–2:00` | Show ablations, scaling/efficiency curves, and honest verdict | Slide diagram left; animate comparison bars/curves right; end with thesis + citation |

## Typography and legibility

Viewers often watch inside a chat pane or on a phone. Size every label for small playback windows:

- Font stack: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif` for labels; KaTeX Computer Modern for math.
- Opening title: `44–52 px`, bold (`700`), centered at top (`y = 70`).
- Section / chart titles: `28–34 px`, semibold (`600`).
- Diagram labels & axis values: `24–28 px`, medium (`500`). Never smaller than `20 px` except minor footnotes/citations (`20–22 px`).
- Equations: `32–44 px` rendered via KaTeX; color-code key terms (`\color{#4DA6FF}{...}`) to match their diagram counterpart.
- Label length: 1–5 words placed right on or next to the object. Never narrate with on-screen sentences when the voiceover already says them.

## Data plots and scientific fidelity

- Draw crisp vector SVG charts (horizontal bar charts, line plots, log-scale curves) with direct value labels at bar tips and clean legend lines — skip heavy chart frames and grid clutter.
- Always display units, sample/model scale, and baseline conditions on the plot (e.g., `1.7B backbone · matched lifetime compute`).
- Animate bars growing left-to-right and curves drawing along `stroke-dashoffset` right as the narrator cites the comparison.
- End on a clean takeaway frame containing the core diagram, a single sharp thesis sentence (plus any key caveat if the headline claim is conditional), and the citation (`Authors, Year · arXiv:XXXX.XXXXX`).
