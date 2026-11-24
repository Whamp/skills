# Deterministic Scene API (`scene.html`)

`scripts/render_video.py` loads `scene.html` over loopback HTTP, injects `window.__TIMELINE__`, waits for fonts and KaTeX, and calls `window.renderAt(t)` for every frame timestamp `t` (in seconds).

## Required contract

1. **Fixed viewport stage:** render inside a `1920×1080` `#stage` container with `overflow: hidden` and `background: #000`.
2. **Read `timeline.json`:** use `window.__TIMELINE__` when already injected by the renderer, or `await fetch("timeline.json").then(r => r.json())` when opened directly in a browser.
3. **Signal readiness:** assign `window.__SCENE_READY__ = initPromise` (a Promise that resolves once timeline data, fonts, and KaTeX equations have finished rendering).
4. **Pure deterministic `window.renderAt(t)`:** given any timestamp `t` in `[0, total_duration_s]`, compute the exact visual state for `t` from scratch (never accumulate state across calls, because `--keyframes` jumps directly to arbitrary timestamps!).
5. **No CSS wall-clock animations:** omit CSS `transition` and `@keyframes` on animated stage elements. Drive every opacity, `transform`, SVG `stroke-dashoffset`, bar width, and chart clip directly from `t` inside `renderAt(t)`.

## Bundled layout helpers (`stage_helpers.js`)

`build_narration.py` copies `assets/stage_helpers.js` into `<out-dir>/stage_helpers.js` (and `render_video.py` also serves it as a fallback at `/stage_helpers.js`). Include `<script src="./stage_helpers.js"></script>` in `scene.html` to access `window.PaperStage`:

- **Timing & math:** `clamp`, `lerp`, `easeOutCubic`, `easeInOutCubic`, `timeSpan`, `makeBeatClock(timeline)`, `revealStroke(el, p)`, `renderLatex(el, tex)`.
- **Auto-measuring SVG primitives:**
  - `svgEl(tag, attrs, parent)` — creates an SVG element in the SVG namespace.
  - `drawSpine(parent, items, opts)` — lays out 2–4 centered top spine pills inside the safe margin with measured widths and verdict slots; update per beat via `spine.setState(i, { status, verdict })`.
  - `drawBarChart(parent, config)` — auto-measures label and value columns via `getBBox()` so bars never collide with labels; drive via `chart.setProgress(p)` and morph in place across ablations via `chart.morphValues(nextValues, p, nextDisplayValues)`.
  - `drawLineChart(parent, config)` — plots vector scaling/training curves with axes, ticks, `stroke-dashoffset` draw-on (`chart.setProgress(p)`), and vertically de-collided end labels.
  - `placeBadgeRightOf(anchorEl, text, opts)` — positions a pill badge to the right of `anchorEl.getBBox()` clamped within the right safe margin.
  - `fitLabelInBox(textEl, boxRect, opts)` — shrinks an SVG label font size if needed so it fits cleanly inside its container rect.

## Minimal `scene.html` skeleton

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Paper Explainer</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <script src="./stage_helpers.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      width: 1920px; height: 1080px; overflow: hidden;
      background: #000; color: #f5f7fa;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    }
    #stage {
      position: relative; width: 1920px; height: 1080px;
      background: #000; overflow: hidden;
    }
    svg#canvas { position: absolute; inset: 0; width: 1920px; height: 1080px; }
    #math-layer { position: absolute; inset: 0; pointer-events: none; }
    .math-node { position: absolute; transform: translate(-50%, -50%); }
    /* Optional interactive scrub bar, only visible with ?preview=1 */
    #preview-bar {
      display: none; position: fixed; left: 24px; right: 24px; bottom: 18px;
      background: rgba(18, 22, 28, 0.92); border: 1px solid #30363d;
      border-radius: 10px; padding: 10px 16px; gap: 14px; align-items: center;
      font-size: 16px; z-index: 99;
    }
  </style>
</head>
<body>
  <div id="stage">
    <svg id="canvas" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg"></svg>
    <div id="math-layer"></div>
  </div>
  <div id="preview-bar">
    <button id="play-btn" type="button">Play</button>
    <input id="scrub" type="range" min="0" max="100" step="0.033" value="0" style="flex:1" />
    <span id="time-label">0.00s</span>
  </div>
  <script>
    const S = window.PaperStage;
    let clock = null;

    // ---- Scene construction and per-frame update ----
    function buildScene(timeline) {
      clock = S.makeBeatClock(timeline);
      const canvas = document.getElementById("canvas");
      // Build SVG actors with S.drawSpine / S.drawBarChart / S.drawLineChart and pre-render KaTeX with S.renderLatex.
      void canvas;
    }

    window.renderAt = function renderAt(t) {
      // Compute every opacity, transform, bar width, and stroke reveal purely from t and clock.
      void t;
    };

    window.__SCENE_READY__ = (async () => {
      const timeline = window.__TIMELINE__ || await fetch("timeline.json").then((r) => r.json());
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      buildScene(timeline);
      window.renderAt(0);

      // Interactive browser preview when opened with ?preview=1
      if (new URLSearchParams(location.search).get("preview") === "1") {
        const bar = document.getElementById("preview-bar");
        const scrub = document.getElementById("scrub");
        const label = document.getElementById("time-label");
        const btn = document.getElementById("play-btn");
        bar.style.display = "flex";
        scrub.max = String(clock.totalDuration);
        let cur = 0, playing = false, lastTs = 0;
        const paint = (sec) => {
          cur = S.clamp(sec, 0, clock.totalDuration);
          scrub.value = String(cur);
          label.textContent = `${cur.toFixed(2)}s / ${clock.totalDuration.toFixed(2)}s`;
          window.renderAt(cur);
        };
        scrub.addEventListener("input", () => { playing = false; btn.textContent = "Play"; paint(Number(scrub.value)); });
        btn.addEventListener("click", () => {
          playing = !playing;
          btn.textContent = playing ? "Pause" : "Play";
          lastTs = performance.now();
          if (playing) requestAnimationFrame(tick);
        });
        function tick(now) {
          if (!playing) return;
          const dt = (now - lastTs) / 1000;
          lastTs = now;
          if (cur + dt >= clock.totalDuration) { paint(clock.totalDuration); playing = false; btn.textContent = "Play"; return; }
          paint(cur + dt);
          requestAnimationFrame(tick);
        }
      }
    })();
  </script>
</body>
</html>
```

## Automated keyframe layout audit

`render_video.py --keyframes` audits every beat keyframe after calling `window.renderAt(t)`:

- **KaTeX integrity:** fails if `.math-node` exists while `window.katex` is missing, if any visible `.math-node` lacks a rendered `.katex` child, or if `.katex-error` is present. Always load `katex.min.js` synchronously (never with `defer`).
- **Safe margins:** flags any visible SVG `<text>` or `.math-node` outside `x ∈ [72, 1848]`, `y ∈ [56, 1024]`.
- **Collisions:** flags overlapping visible text/math boxes and text crossing the border of sibling `<rect>` or `<polygon>` elements. Add `data-audit-ignore="true"` only on intentionally decorative shapes (such as shaded plot regions or background tracks).

## KaTeX offline fallback

When rendering offline (no CDN access), pass `--katex-dir /path/to/katex/dist` or inline local `katex.min.css` and `katex.min.js` into the output directory and reference them via relative paths (`./katex.min.css`, `./katex.min.js`). `render_video.py` serves all files inside the directory containing `scene.html`.

## Previewing interactively

Serve `<out-dir>` over loopback (e.g. `python3 -m http.server --bind 127.0.0.1 <port> -d <out-dir>`) and open `/scene.html?preview=1` to scrub every frame and inspect timing before rendering.
