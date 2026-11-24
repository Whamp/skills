# Deterministic Scene API (`scene.html`)

`scripts/render_video.py` loads `scene.html` over loopback HTTP, injects `window.__TIMELINE__`, waits for fonts and KaTeX, and calls `window.renderAt(t)` for every frame timestamp `t` (in seconds).

## Required contract

1. **Fixed viewport stage:** render inside a `1920×1080` `#stage` container with `overflow: hidden` and `background: #000`.
2. **Read `timeline.json`:** use `window.__TIMELINE__` when already injected by the renderer, or `await fetch("timeline.json").then(r => r.json())` when opened directly in a browser.
3. **Signal readiness:** assign `window.__SCENE_READY__ = initPromise` (a Promise that resolves once timeline data, fonts, and KaTeX equations have finished rendering).
4. **Pure deterministic `window.renderAt(t)`:** given any timestamp `t` in `[0, total_duration_s]`, compute the exact visual state for `t` from scratch (never accumulate state across calls, because `--keyframes` jumps directly to arbitrary timestamps!).
5. **No CSS wall-clock animations:** omit CSS `transition` and `@keyframes` on animated stage elements. Drive every opacity, `transform`, SVG `stroke-dashoffset`, bar width, and chart clip directly from `t` inside `renderAt(t)`.

## Minimal `scene.html` skeleton

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Paper Explainer</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
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
    // ---- Pure deterministic helpers ----
    const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
    const lerp = (a, b, p) => a + (b - a) * p;
    const easeOut = (p) => 1 - Math.pow(1 - clamp(p), 3);
    const easeInOut = (p) => {
      const x = clamp(p);
      return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
    };
    const span = (t, t0, t1, ease = easeOut) => ease(clamp((t - t0) / Math.max(1e-4, t1 - t0)));

    // Beat lookup helper: returns { start, audioEnd, end, dur }
    let B = {};
    let TOTAL = 10;

    function beatProgress(id, t, startFrac = 0, endFrac = 0.5, ease = easeOut) {
      const b = B[id];
      const dur = Math.max(0.2, b.audio_end_s - b.start_s);
      return span(t, b.start_s + dur * startFrac, b.start_s + dur * endFrac, ease);
    }

    function revealStroke(el, p) {
      const len = Number(el.dataset.len || (el.dataset.len = String(el.getTotalLength())));
      el.style.strokeDasharray = String(len);
      el.style.strokeDashoffset = String(len * (1 - clamp(p)));
    }

    function renderMath(el, tex) {
      if (window.katex) {
        window.katex.render(tex, el, { displayMode: true, throwOnError: false });
      } else {
        el.textContent = tex;
      }
    }

    // ---- Scene construction and per-frame update ----
    function buildScene(timeline) {
      B = Object.fromEntries(timeline.beats.map((b) => [b.id, b]));
      TOTAL = timeline.total_duration_s;
      // Build SVG elements and pre-render KaTeX nodes once here.
    }

    window.renderAt = function renderAt(t) {
      // Compute every opacity, transform, bar width, and stroke reveal purely from t and B.
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
        scrub.max = String(TOTAL);
        let cur = 0, playing = false, lastTs = 0;
        const paint = (sec) => {
          cur = clamp(sec, 0, TOTAL);
          scrub.value = String(cur);
          label.textContent = `${cur.toFixed(2)}s / ${TOTAL.toFixed(2)}s`;
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
          if (cur + dt >= TOTAL) { paint(TOTAL); playing = false; btn.textContent = "Play"; return; }
          paint(cur + dt);
          requestAnimationFrame(tick);
        }
      }
    })();
  </script>
</body>
</html>
```

## KaTeX offline fallback

When rendering offline (no CDN access), pass `--katex-dir /path/to/katex/dist` or inline local `katex.min.css` and `katex.min.js` into the output directory and reference them via relative paths (`./katex.min.css`, `./katex.min.js`). `render_video.py` serves all files inside the directory containing `scene.html`.

## Previewing interactively

Serve `<out-dir>` over loopback (e.g. `python3 -m http.server --bind 127.0.0.1 <port> -d <out-dir>`) and open `/scene.html?preview=1` to scrub every frame and inspect timing before rendering.
