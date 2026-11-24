/* Auto-measuring SVG layout and deterministic animation primitives for paper-to-video. */
(function initPaperStage(globalScope) {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const STAGE_WIDTH = 1920;
  const SAFE_MARGIN_X = 72;
  const SAFE_RIGHT = STAGE_WIDTH - SAFE_MARGIN_X;

  const PALETTE = Object.freeze({
    canvas: "#000000",
    ink: "#F5F7FA",
    muted: "#8B949E",
    stroke: "#30363D",
    hero: "#4DA6FF",
    heroFill: "rgba(77, 166, 255, 0.16)",
    amber: "#F59E0B",
    emerald: "#34D399",
    danger: "#F87171",
  });

  /** Clamp a number to [min, max]. */
  function clamp(value, min = 0, max = 1) {
    return Math.max(min, Math.min(max, value));
  }

  /** Linearly interpolate between start and end by progress in [0, 1]. */
  function lerp(start, end, progress) {
    return start + (end - start) * progress;
  }

  /** Cubic ease-out curve on [0, 1]. */
  function easeOutCubic(progress) {
    const t = clamp(progress);
    return 1 - Math.pow(1 - t, 3);
  }

  /** Cubic ease-in-out curve on [0, 1]. */
  function easeInOutCubic(progress) {
    const t = clamp(progress);
    if (t < 0.5) {
      return 4 * t * t * t;
    }
    return 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /** Compute eased [0, 1] progress for timestamp t across [t0, t1]. */
  function timeSpan(t, t0, t1, ease = easeOutCubic) {
    return ease(clamp((t - t0) / Math.max(1e-4, t1 - t0)));
  }

  /** Build a beat lookup clock from timeline.json. */
  function makeBeatClock(timeline) {
    const beats = Object.fromEntries(
      timeline.beats.map((beat) => [beat.id, beat]),
    );
    const totalDuration = Number(timeline.total_duration_s || 0);

    function progress(
      beatId,
      t,
      startFrac = 0,
      endFrac = 0.5,
      ease = easeOutCubic,
    ) {
      const beat = beats[beatId];
      if (!beat) {
        throw new Error(`PaperStage unknown beat id: ${beatId}`);
      }
      const dur = Math.max(0.2, beat.audio_end_s - beat.start_s);
      return timeSpan(
        t,
        beat.start_s + dur * startFrac,
        beat.start_s + dur * endFrac,
        ease,
      );
    }

    function active(beatId, t) {
      const beat = beats[beatId];
      if (!beat) {
        return false;
      }
      return t >= beat.start_s && t < beat.end_s;
    }

    return { beats, totalDuration, progress, active };
  }

  /** Create an SVG element with attributes and optional parent insertion. */
  function svgEl(tag, attrs, parent) {
    const el = document.createElementNS(SVG_NS, tag);
    if (attrs) {
      for (const [key, value] of Object.entries(attrs)) {
        if (value !== undefined && value !== null) {
          el.setAttribute(key, String(value));
        }
      }
    }
    if (parent) {
      parent.appendChild(el);
    }
    return el;
  }

  /** Reveal an SVG stroked path or line deterministically from progress in [0, 1]. */
  function revealStroke(el, progress) {
    let totalLen = Number(el.dataset.strokeLen || 0);
    if (!totalLen) {
      totalLen = el.getTotalLength();
      el.dataset.strokeLen = String(totalLen);
    }
    el.style.strokeDasharray = String(totalLen);
    el.style.strokeDashoffset = String(totalLen * (1 - clamp(progress)));
  }

  /** Render LaTeX into a .math-node container using KaTeX. */
  function renderLatex(el, tex, options) {
    if (globalScope.katex) {
      const opts = {
        displayMode: true,
        throwOnError: false,
        ...options,
      };
      globalScope.katex.render(tex, el, opts);
    } else {
      el.textContent = tex;
    }
  }

  /** Measure an SVG element safely even when detached. */
  function measureSvgBox(el) {
    try {
      return el.getBBox();
    } catch (_err) {
      return { x: 0, y: 0, width: 0, height: 0 };
    }
  }

  /** Shrink an SVG text element font-size if needed so it fits cleanly inside boxRect. */
  function fitLabelInBox(textEl, boxRect, options) {
    const padX = options && options.padX !== undefined ? options.padX : 12;
    const minFontSize =
      options && options.minFontSize !== undefined ? options.minFontSize : 16;
    const maxWidth = Math.max(20, boxRect.width - padX * 2);
    let fontSize = Number(
      textEl.getAttribute("font-size") ||
        parseFloat(globalScope.getComputedStyle(textEl).fontSize) ||
        24,
    );

    let box = measureSvgBox(textEl);
    while (box.width > maxWidth && fontSize > minFontSize) {
      const ratio = maxWidth / Math.max(1, box.width);
      fontSize = Math.max(minFontSize, Math.floor(fontSize * ratio));
      textEl.setAttribute("font-size", String(fontSize));
      box = measureSvgBox(textEl);
      if (fontSize <= minFontSize) {
        break;
      }
    }
    return { fontSize, bbox: box };
  }

  /** Place a measured pill badge to the right of anchorEl without crossing maxRight. */
  function placeBadgeRightOf(anchorEl, text, options) {
    const opts = options || {};
    const parent = opts.parent || anchorEl.parentNode;
    const gap = opts.gap !== undefined ? opts.gap : 14;
    const padX = opts.padX !== undefined ? opts.padX : 14;
    const padY = opts.padY !== undefined ? opts.padY : 6;
    const fontSize = opts.fontSize !== undefined ? opts.fontSize : 20;
    const maxRight = opts.maxRight !== undefined ? opts.maxRight : SAFE_RIGHT;
    const fill = opts.fill || PALETTE.heroFill;
    const stroke = opts.stroke || PALETTE.hero;
    const textColor = opts.textColor || PALETTE.ink;

    const anchorBox = measureSvgBox(anchorEl);
    const group = svgEl("g", { class: "stage-badge" }, parent);
    const rect = svgEl(
      "rect",
      {
        rx: 8,
        ry: 8,
        fill,
        stroke,
        "stroke-width": 1.5,
      },
      group,
    );
    const label = svgEl(
      "text",
      {
        "font-size": fontSize,
        "font-weight": 600,
        fill: textColor,
        "text-anchor": "middle",
        "dominant-baseline": "central",
      },
      group,
    );
    label.textContent = text;

    const textBox = measureSvgBox(label);
    const badgeW = Math.ceil(textBox.width + padX * 2);
    const badgeH = Math.ceil(Math.max(textBox.height, fontSize) + padY * 2);
    const centerY = anchorBox.y + anchorBox.height / 2;
    const rawX = anchorBox.x + anchorBox.width + gap;
    const x = Math.min(rawX, maxRight - badgeW);
    const y = Math.round(centerY - badgeH / 2);

    rect.setAttribute("x", String(x));
    rect.setAttribute("y", String(y));
    rect.setAttribute("width", String(badgeW));
    rect.setAttribute("height", String(badgeH));
    label.setAttribute("x", String(x + badgeW / 2));
    label.setAttribute("y", String(y + badgeH / 2));

    return {
      group,
      rect,
      label,
      bbox: { x, y, width: badgeW, height: badgeH },
    };
  }

  /** Draw the persistent top visual spine with measured pills and verdict badges. */
  function drawSpine(parent, items, options) {
    const opts = options || {};
    const y = opts.y !== undefined ? opts.y : 58;
    const pillHeight = opts.pillHeight !== undefined ? opts.pillHeight : 48;
    const gap = opts.gap !== undefined ? opts.gap : 24;
    const fontSize = opts.fontSize !== undefined ? opts.fontSize : 24;
    const padX = opts.padX !== undefined ? opts.padX : 26;
    const centerX = opts.centerX !== undefined ? opts.centerX : STAGE_WIDTH / 2;
    const maxTotalWidth =
      opts.maxTotalWidth !== undefined
        ? opts.maxTotalWidth
        : STAGE_WIDTH - SAFE_MARGIN_X * 2;

    const group = svgEl("g", { class: "stage-spine" }, parent);
    const pills = [];

    for (const item of items) {
      const labelText = typeof item === "string" ? item : item.label;
      const pillGroup = svgEl("g", { class: "stage-spine-pill" }, group);
      const rect = svgEl(
        "rect",
        {
          y,
          height: pillHeight,
          rx: 12,
          ry: 12,
          fill: "#0D1117",
          stroke: PALETTE.stroke,
          "stroke-width": 2,
        },
        pillGroup,
      );
      const label = svgEl(
        "text",
        {
          y: y + pillHeight / 2,
          "font-size": fontSize,
          "font-weight": 600,
          fill: PALETTE.ink,
          "text-anchor": "middle",
          "dominant-baseline": "central",
        },
        pillGroup,
      );
      label.textContent = labelText;

      const verdictGroup = svgEl(
        "g",
        { class: "stage-spine-verdict", opacity: 0 },
        pillGroup,
      );
      const verdictRect = svgEl(
        "rect",
        {
          y: y + pillHeight + 8,
          height: 28,
          rx: 7,
          ry: 7,
          fill: PALETTE.heroFill,
          stroke: PALETTE.hero,
          "stroke-width": 1.5,
        },
        verdictGroup,
      );
      const verdictText = svgEl(
        "text",
        {
          y: y + pillHeight + 22,
          "font-size": 18,
          "font-weight": 600,
          fill: PALETTE.ink,
          "text-anchor": "middle",
          "dominant-baseline": "central",
        },
        verdictGroup,
      );

      const textBox = measureSvgBox(label);
      const width = Math.ceil(Math.max(150, textBox.width + padX * 2));
      pills.push({
        group: pillGroup,
        rect,
        label,
        verdictGroup,
        verdictRect,
        verdictText,
        width,
        x: 0,
      });
    }

    let totalW =
      pills.reduce((sum, pill) => sum + pill.width, 0) +
      gap * Math.max(0, pills.length - 1);
    if (totalW > maxTotalWidth && pills.length > 0) {
      const scale =
        (maxTotalWidth - gap * Math.max(0, pills.length - 1)) /
        Math.max(1, totalW - gap * Math.max(0, pills.length - 1));
      for (const pill of pills) {
        pill.width = Math.floor(pill.width * scale);
      }
      totalW = maxTotalWidth;
    }

    let cursorX = Math.round(centerX - totalW / 2);
    for (const pill of pills) {
      pill.x = cursorX;
      pill.rect.setAttribute("x", String(cursorX));
      pill.rect.setAttribute("width", String(pill.width));
      pill.label.setAttribute("x", String(cursorX + pill.width / 2));
      fitLabelInBox(pill.label, { width: pill.width }, { padX: 12 });
      cursorX += pill.width + gap;
    }

    function setState(index, state) {
      const pill = pills[index];
      if (!pill) {
        return;
      }
      const status = (state && state.status) || "neutral";
      const opacity = state && state.opacity !== undefined ? state.opacity : 1;
      pill.group.setAttribute("opacity", String(opacity));

      if (status === "active") {
        pill.rect.setAttribute("stroke", PALETTE.hero);
        pill.rect.setAttribute("fill", PALETTE.heroFill);
        pill.label.setAttribute("fill", PALETTE.ink);
      } else if (status === "key") {
        pill.rect.setAttribute("stroke", PALETTE.emerald);
        pill.rect.setAttribute("fill", "rgba(52, 211, 153, 0.16)");
        pill.label.setAttribute("fill", PALETTE.ink);
      } else if (status === "dim") {
        pill.rect.setAttribute("stroke", PALETTE.stroke);
        pill.rect.setAttribute("fill", "#080A0E");
        pill.label.setAttribute("fill", PALETTE.muted);
      } else {
        pill.rect.setAttribute("stroke", PALETTE.stroke);
        pill.rect.setAttribute("fill", "#0D1117");
        pill.label.setAttribute("fill", PALETTE.ink);
      }

      if (state && state.verdict) {
        pill.verdictText.textContent = state.verdict;
        const vBox = measureSvgBox(pill.verdictText);
        const vW = Math.ceil(vBox.width + 20);
        const vX = Math.round(pill.x + (pill.width - vW) / 2);
        const vColor =
          status === "key"
            ? PALETTE.emerald
            : status === "dim"
              ? PALETTE.muted
              : PALETTE.hero;
        pill.verdictRect.setAttribute("x", String(vX));
        pill.verdictRect.setAttribute("width", String(vW));
        pill.verdictRect.setAttribute("stroke", vColor);
        pill.verdictRect.setAttribute(
          "fill",
          status === "dim" ? "#0D1117" : "rgba(77, 166, 255, 0.14)",
        );
        pill.verdictText.setAttribute("x", String(vX + vW / 2));
        pill.verdictText.setAttribute("fill", vColor);
        pill.verdictGroup.setAttribute(
          "opacity",
          String(
            state.verdictOpacity !== undefined ? state.verdictOpacity : 1,
          ),
        );
      } else {
        pill.verdictGroup.setAttribute("opacity", "0");
      }
    }

    return { group, pills, setState };
  }

  /** Draw an auto-measured horizontal bar chart with in-place morphing support. */
  function drawBarChart(parent, config) {
    const x = config.x !== undefined ? config.x : 120;
    const y = config.y !== undefined ? config.y : 220;
    const width = config.width !== undefined ? config.width : 800;
    const rowHeight = config.rowHeight !== undefined ? config.rowHeight : 64;
    const barHeight = config.barHeight !== undefined ? config.barHeight : 34;
    const labelFontSize = config.labelFontSize || 24;
    const valueFontSize = config.valueFontSize || 24;
    const unit = config.unit || "";
    const maxValue =
      config.maxValue ||
      Math.max(1e-6, ...config.bars.map((bar) => Number(bar.value || 0)));

    const group = svgEl("g", { class: "stage-bar-chart" }, parent);
    let bodyTop = y;

    if (config.title) {
      const titleEl = svgEl(
        "text",
        {
          x,
          y: bodyTop + 26,
          "font-size": 30,
          "font-weight": 600,
          fill: PALETTE.ink,
        },
        group,
      );
      titleEl.textContent = config.title;
      bodyTop += 40;
    }

    if (config.subtitle) {
      const subEl = svgEl(
        "text",
        {
          x,
          y: bodyTop + 20,
          "font-size": 21,
          "font-weight": 500,
          fill: PALETTE.muted,
        },
        group,
      );
      subEl.textContent = config.subtitle;
      bodyTop += 38;
    }

    const rowData = config.bars.map((bar, index) => {
      const rowY = bodyTop + 16 + index * rowHeight;
      const labelEl = svgEl(
        "text",
        {
          x,
          y: rowY + barHeight / 2,
          "font-size": labelFontSize,
          "font-weight": bar.highlight ? 600 : 500,
          fill: bar.highlight ? PALETTE.ink : PALETTE.muted,
          "dominant-baseline": "central",
        },
        group,
      );
      labelEl.textContent = bar.label;

      const valueEl = svgEl(
        "text",
        {
          y: rowY + barHeight / 2,
          "font-size": valueFontSize,
          "font-weight": 600,
          fill: bar.highlight ? bar.color || PALETTE.hero : PALETTE.ink,
          "dominant-baseline": "central",
        },
        group,
      );
      valueEl.textContent =
        bar.displayValue !== undefined
          ? String(bar.displayValue)
          : `${bar.value}${unit}`;

      return {
        spec: bar,
        rowY,
        labelEl,
        valueEl,
        labelW: measureSvgBox(labelEl).width,
        valueW: measureSvgBox(valueEl).width,
      };
    });

    const labelColW = Math.ceil(
      Math.max(100, ...rowData.map((row) => row.labelW)),
    );
    const valueColW = Math.ceil(
      Math.max(70, ...rowData.map((row) => row.valueW)),
    );
    const labelGap = 20;
    const valueGap = 16;
    const barStartX = x + labelColW + labelGap;
    const maxBarW = Math.max(
      80,
      width - labelColW - labelGap - valueColW - valueGap,
    );

    const bars = rowData.map((row) => {
      const track = svgEl(
        "rect",
        {
          x: barStartX,
          y: row.rowY,
          width: maxBarW,
          height: barHeight,
          rx: 6,
          ry: 6,
          fill: "#11161D",
          stroke: "none",
          "data-audit-ignore": "true",
        },
        group,
      );
      const fillRect = svgEl(
        "rect",
        {
          x: barStartX,
          y: row.rowY,
          width: 0,
          height: barHeight,
          rx: 6,
          ry: 6,
          fill: row.spec.color || (row.spec.highlight ? PALETTE.hero : PALETTE.amber),
        },
        group,
      );
      group.appendChild(row.valueEl);
      row.valueEl.setAttribute("x", String(barStartX + valueGap));
      return {
        spec: row.spec,
        track,
        fillRect,
        labelEl: row.labelEl,
        valueEl: row.valueEl,
      };
    });

    function renderBarValue(bar, currentValue, displayText) {
      const frac = clamp(currentValue / maxValue, 0, 1);
      const barW = Math.max(0, frac * maxBarW);
      bar.fillRect.setAttribute("width", String(barW));
      bar.valueEl.textContent = displayText;
      bar.valueEl.setAttribute("x", String(barStartX + barW + valueGap));
    }

    function setProgress(progress) {
      const p = clamp(progress);
      for (const bar of bars) {
        const val = Number(bar.spec.value || 0) * p;
        const displayText =
          p >= 0.99 && bar.spec.displayValue !== undefined
            ? String(bar.spec.displayValue)
            : `${val.toFixed(config.decimals !== undefined ? config.decimals : 1)}${unit}`;
        renderBarValue(bar, val, displayText);
        bar.valueEl.setAttribute("opacity", String(clamp(p * 2)));
      }
    }

    function morphValues(nextValues, progress, nextDisplayValues) {
      const p = clamp(progress);
      for (let i = 0; i < bars.length; i += 1) {
        const bar = bars[i];
        const fromVal = Number(bar.spec.value || 0);
        const toVal =
          nextValues[i] !== undefined ? Number(nextValues[i]) : fromVal;
        const cur = lerp(fromVal, toVal, p);
        const displayText =
          p >= 0.99 && nextDisplayValues && nextDisplayValues[i] !== undefined
            ? String(nextDisplayValues[i])
            : `${cur.toFixed(config.decimals !== undefined ? config.decimals : 1)}${unit}`;
        renderBarValue(bar, cur, displayText);
        bar.valueEl.setAttribute("opacity", "1");
      }
    }

    setProgress(0);
    return { group, bars, setProgress, morphValues };
  }

  /** Draw a vector line/scaling chart with stroke reveal and non-overlapping end labels. */
  function drawLineChart(parent, config) {
    const x = config.x !== undefined ? config.x : 140;
    const y = config.y !== undefined ? config.y : 220;
    const width = config.width !== undefined ? config.width : 820;
    const height = config.height !== undefined ? config.height : 460;
    const [xMin, xMax] = config.xDomain || [0, 1];
    const [yMin, yMax] = config.yDomain || [0, 1];
    const plotLeft = x + (config.leftPad !== undefined ? config.leftPad : 86);
    const plotRight =
      x + width - (config.rightPad !== undefined ? config.rightPad : 170);
    const plotBottom = y + height - 64;

    const group = svgEl("g", { class: "stage-line-chart" }, parent);
    let headerBottom = y;

    if (config.title) {
      const titleEl = svgEl(
        "text",
        {
          x,
          y: headerBottom + 26,
          "font-size": 30,
          "font-weight": 600,
          fill: PALETTE.ink,
        },
        group,
      );
      titleEl.textContent = config.title;
      headerBottom += 38;
    }

    if (config.subtitle) {
      const subEl = svgEl(
        "text",
        {
          x,
          y: headerBottom + 20,
          "font-size": 21,
          "font-weight": 500,
          fill: PALETTE.muted,
        },
        group,
      );
      subEl.textContent = config.subtitle;
      headerBottom += 32;
    }

    const plotTop = headerBottom + (config.yLabel ? 42 : 20);

    const mapX = (vx) =>
      lerp(plotLeft, plotRight, (vx - xMin) / Math.max(1e-9, xMax - xMin));
    const mapY = (vy) =>
      lerp(plotBottom, plotTop, (vy - yMin) / Math.max(1e-9, yMax - yMin));

    // Axes
    svgEl(
      "line",
      {
        x1: plotLeft,
        y1: plotBottom,
        x2: plotRight,
        y2: plotBottom,
        stroke: PALETTE.stroke,
        "stroke-width": 2,
      },
      group,
    );
    svgEl(
      "line",
      {
        x1: plotLeft,
        y1: plotTop,
        x2: plotLeft,
        y2: plotBottom,
        stroke: PALETTE.stroke,
        "stroke-width": 2,
      },
      group,
    );

    for (const tick of config.xTicks || []) {
      const val = typeof tick === "object" ? tick.value : tick;
      const text = typeof tick === "object" ? tick.label : String(tick);
      const tx = mapX(val);
      svgEl(
        "line",
        {
          x1: tx,
          y1: plotBottom,
          x2: tx,
          y2: plotBottom + 8,
          stroke: PALETTE.stroke,
          "stroke-width": 1.5,
        },
        group,
      );
      const tickEl = svgEl(
        "text",
        {
          x: tx,
          y: plotBottom + 30,
          "font-size": 20,
          fill: PALETTE.muted,
          "text-anchor": "middle",
        },
        group,
      );
      tickEl.textContent = text;
    }

    for (const tick of config.yTicks || []) {
      const val = typeof tick === "object" ? tick.value : tick;
      const text = typeof tick === "object" ? tick.label : String(tick);
      const ty = mapY(val);
      svgEl(
        "line",
        {
          x1: plotLeft,
          y1: ty,
          x2: plotRight,
          y2: ty,
          stroke: "#161B22",
          "stroke-width": 1,
        },
        group,
      );
      const tickEl = svgEl(
        "text",
        {
          x: plotLeft - 14,
          y: ty,
          "font-size": 20,
          fill: PALETTE.muted,
          "text-anchor": "end",
          "dominant-baseline": "central",
        },
        group,
      );
      tickEl.textContent = text;
    }

    if (config.xLabel) {
      const xAxisEl = svgEl(
        "text",
        {
          x: (plotLeft + plotRight) / 2,
          y: plotBottom + 58,
          "font-size": 22,
          fill: PALETTE.muted,
          "text-anchor": "middle",
        },
        group,
      );
      xAxisEl.textContent = config.xLabel;
    }

    if (config.yLabel) {
      const yAxisEl = svgEl(
        "text",
        {
          x: plotLeft - 14,
          y: plotTop - 16,
          "font-size": 20,
          fill: PALETTE.muted,
          "text-anchor": "end",
        },
        group,
      );
      yAxisEl.textContent = config.yLabel;
    }

    const builtSeries = (config.series || []).map((item) => {
      const points = item.points || [];
      const pathD = points
        .map(
          (pt, idx) =>
            `${idx === 0 ? "M" : "L"}${mapX(pt[0]).toFixed(1)},${mapY(pt[1]).toFixed(1)}`,
        )
        .join(" ");
      const path = svgEl(
        "path",
        {
          d: pathD,
          fill: "none",
          stroke: item.color || PALETTE.hero,
          "stroke-width": item.strokeWidth || 3.5,
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
        },
        group,
      );
      if (item.dashed) {
        path.setAttribute("stroke-dasharray", "8 6");
      }

      const lastPt = points[points.length - 1] || [xMin, yMin];
      const endY = mapY(lastPt[1]);
      const labelEl = svgEl(
        "text",
        {
          x: plotRight + 14,
          y: endY,
          "font-size": 22,
          "font-weight": 600,
          fill: item.color || PALETTE.hero,
          "dominant-baseline": "central",
        },
        group,
      );
      labelEl.textContent = item.label || "";
      return { spec: item, path, labelEl, rawEndY: endY, labelY: endY };
    });

    // De-collide end-of-line series labels vertically.
    const sortedLabels = [...builtSeries].sort((a, b) => a.rawEndY - b.rawEndY);
    const minSpacing = 28;
    for (let i = 1; i < sortedLabels.length; i += 1) {
      const prev = sortedLabels[i - 1];
      const cur = sortedLabels[i];
      if (cur.labelY - prev.labelY < minSpacing) {
        cur.labelY = prev.labelY + minSpacing;
      }
    }
    for (const item of sortedLabels) {
      item.labelEl.setAttribute("y", String(item.labelY));
    }

    function setProgress(progress) {
      const p = clamp(progress);
      for (const item of builtSeries) {
        if (!item.spec.dashed) {
          revealStroke(item.path, p);
        } else {
          item.path.setAttribute("opacity", String(p));
        }
        item.labelEl.setAttribute("opacity", String(clamp((p - 0.65) / 0.35)));
      }
    }

    setProgress(0);
    return { group, series: builtSeries, setProgress };
  }

  globalScope.PaperStage = Object.freeze({
    PALETTE,
    clamp,
    lerp,
    easeOutCubic,
    easeInOutCubic,
    timeSpan,
    makeBeatClock,
    svgEl,
    revealStroke,
    renderLatex,
    fitLabelInBox,
    placeBadgeRightOf,
    drawSpine,
    drawBarChart,
    drawLineChart,
  });
})(window);
