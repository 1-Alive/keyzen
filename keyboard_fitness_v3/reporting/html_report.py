import json
from datetime import date


def render_html(
    summary,
    fatigue,
    anomalies,
    peak_hours,
    low_periods,
    top_keys,
    activity_guess,
    chart_filename,
    payload,
):
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    anomaly_count = len(anomalies)
    advice = (
        "立即休息，并降低后续连续输入强度。"
        if fatigue["score"] >= 85
        else "安排短休息，关注肩颈和手腕状态。"
        if fatigue["score"] >= 70
        else "保持规律节奏，建议每小时短暂活动。"
    )
    anomaly_items = "".join(
        f"<li><strong>{item['type']}</strong><span>{item['message']}</span></li>" for item in anomalies
    ) or "<li><strong>暂无异常</strong><span>今天没有触发高负荷、疲劳风险或低活跃异常。</span></li>"

    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Keyboard Fitness Daily Report</title>
  <style>
    :root {
      --ink: #1d2433;
      --muted: #667085;
      --line: #d9dee8;
      --panel: #ffffff;
      --paper: #f3f6f8;
      --teal: #0f766e;
      --blue: #2563eb;
      --gold: #d97706;
      --rose: #e11d48;
      --violet: #7c3aed;
      --green: #16a34a;
      --shadow: 0 18px 45px rgba(31, 41, 55, 0.10);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: linear-gradient(180deg, #eef4f6 0%, #f8fafc 52%, #edf2f7 100%);
      font-family: Inter, "Segoe UI", Arial, "Microsoft YaHei", sans-serif;
    }
    .shell { max-width: 1220px; margin: 0 auto; padding: 28px 24px 42px; }
    .hero {
      min-height: 240px;
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.8fr);
      gap: 22px;
      align-items: stretch;
    }
    .hero-main {
      padding: 30px;
      color: #fff;
      background:
        linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(15, 118, 110, 0.88)),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.08) 0 1px, transparent 1px 34px);
      border-radius: 8px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }
    .hero-main:after {
      content: "";
      position: absolute;
      right: -80px;
      top: 18px;
      width: 280px;
      height: 180px;
      border: 1px solid rgba(255,255,255,0.18);
      transform: rotate(-11deg);
    }
    .eyebrow { margin: 0 0 12px; color: #bde8e1; font-size: 13px; letter-spacing: 0; }
    h1 { margin: 0; font-size: 36px; line-height: 1.12; letter-spacing: 0; }
    .hero-copy { max-width: 720px; margin: 18px 0 0; color: #d9fbf5; font-size: 16px; line-height: 1.7; }
    .status-panel {
      padding: 24px;
      background: rgba(255,255,255,0.92);
      border: 1px solid rgba(217, 222, 232, 0.9);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .score-row { display: flex; align-items: baseline; justify-content: space-between; gap: 14px; }
    .score { font-size: 52px; font-weight: 800; line-height: 1; color: var(--teal); }
    .badge { padding: 7px 10px; border-radius: 999px; color: #fff; background: var(--teal); font-size: 13px; white-space: nowrap; }
    .meter { height: 12px; margin: 20px 0 14px; border-radius: 999px; background: #e5e7eb; overflow: hidden; }
    .meter span { display: block; height: 100%; width: 0; background: linear-gradient(90deg, var(--green), var(--gold), var(--rose)); }
    .status-panel p { margin: 0; color: var(--muted); line-height: 1.6; }
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 18px 0; }
    .metric {
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(31, 41, 55, 0.06);
    }
    .metric label { display: block; color: var(--muted); font-size: 13px; margin-bottom: 10px; }
    .metric strong { display: block; font-size: 28px; line-height: 1.1; }
    .metric small { display: block; color: var(--muted); margin-top: 8px; }
    .grid { display: grid; grid-template-columns: 1.35fr 0.85fr; gap: 18px; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 8px 24px rgba(31, 41, 55, 0.06);
      min-width: 0;
    }
    .panel h2 { margin: 0 0 14px; font-size: 18px; }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
    .tabs { display: inline-flex; padding: 3px; border: 1px solid var(--line); border-radius: 8px; background: #f8fafc; }
    .tab {
      border: 0;
      background: transparent;
      color: var(--muted);
      padding: 7px 11px;
      border-radius: 6px;
      cursor: pointer;
      font: inherit;
    }
    .tab.active { background: #fff; color: var(--ink); box-shadow: 0 1px 5px rgba(31, 41, 55, 0.14); }
    canvas { width: 100%; height: 280px; display: block; }
    .mini canvas { height: 230px; }
    .insight {
      padding: 16px;
      border-left: 4px solid var(--teal);
      background: #edf7f5;
      border-radius: 6px;
      color: #164e47;
      line-height: 1.7;
    }
    .list { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
    .list li { padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: #fbfcfe; }
    .list strong { display: block; margin-bottom: 5px; }
    .list span { color: var(--muted); line-height: 1.55; }
    .table-tools { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 12px 0; }
    input {
      width: min(280px, 100%);
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      font: inherit;
    }
    table { width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 8px; }
    th, td { padding: 12px 10px; border-bottom: 1px solid var(--line); text-align: left; }
    th { color: var(--muted); font-size: 13px; cursor: pointer; background: #f8fafc; user-select: none; }
    tr:hover td { background: #f9fbfb; }
    .key-pill { display: inline-flex; min-width: 38px; justify-content: center; padding: 5px 9px; border: 1px solid #cfd8e3; border-bottom-width: 3px; border-radius: 6px; background: #fff; font-weight: 700; }
    .fallback { margin-top: 14px; color: var(--muted); font-size: 13px; }
    .fallback a { color: var(--blue); }
    @media (max-width: 900px) {
      .hero, .grid, .metrics { grid-template-columns: 1fr; }
      .shell { padding: 16px; }
      h1 { font-size: 30px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-main">
        <p class="eyebrow">Keyboard Fitness V3 · 本地行为健康日报 · __TODAY__</p>
        <h1>今天的输入节律、负荷和键盘习惯</h1>
        <p class="hero-copy">__ACTIVITY_GUESS__</p>
      </div>
      <aside class="status-panel">
        <div class="score-row">
          <div>
            <div class="score" id="scoreValue">__SCORE__</div>
            <p>Fatigue Score</p>
          </div>
          <span class="badge" id="scoreBadge">__LEVEL__</span>
        </div>
        <div class="meter"><span id="scoreMeter"></span></div>
        <p>__ADVICE__</p>
      </aside>
    </section>

    <section class="metrics">
      <article class="metric"><label>今日总按键</label><strong>__TODAY_TOTAL__</strong><small>昨日对比 __DELTA__</small></article>
      <article class="metric"><label>7 日均值</label><strong>__SEVEN_MEAN__</strong><small>近期基线</small></article>
      <article class="metric"><label>异常事件</label><strong>__ANOMALY_COUNT__</strong><small>高负荷 / 疲劳 / 低活跃</small></article>
      <article class="metric"><label>峰值时段</label><strong>__PEAKS__</strong><small>低活跃：__LOWS__</small></article>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="panel-head">
          <h2>输入趋势</h2>
          <div class="tabs">
            <button class="tab active" data-trend="hourly">今日小时</button>
            <button class="tab" data-trend="seven">7 天</button>
            <button class="tab" data-trend="thirty">30 天</button>
          </div>
        </div>
        <canvas id="trendChart"></canvas>
        <p class="fallback">静态图备份：<a href="__CHART_FILENAME__">report.png</a></p>
      </article>
      <article class="panel mini">
        <h2>疲劳因子构成</h2>
        <canvas id="fatigueChart"></canvas>
      </article>
    </section>

    <section class="grid" style="margin-top:18px;">
      <article class="panel">
        <h2>按键频率 Top 10</h2>
        <canvas id="keyChart"></canvas>
      </article>
      <article class="panel mini">
        <h2>Session 长度分布</h2>
        <canvas id="sessionChart"></canvas>
      </article>
    </section>

    <section class="grid" style="margin-top:18px;">
      <article class="panel">
        <h2>按键明细</h2>
        <div class="table-tools">
          <input id="keyFilter" placeholder="搜索按键">
          <span style="color:var(--muted);font-size:13px;">点击表头可排序</span>
        </div>
        <table>
          <thead><tr><th data-sort="key">按键</th><th data-sort="total">次数</th><th data-sort="share">占比</th></tr></thead>
          <tbody id="keyRows"></tbody>
        </table>
      </article>
      <article class="panel">
        <h2>洞察与提醒</h2>
        <p class="insight"><strong>可能主要在做：</strong>__ACTIVITY_GUESS__</p>
        <h2 style="margin-top:18px;">异常检测</h2>
        <ul class="list">__ANOMALIES__</ul>
      </article>
    </section>
  </main>

  <script>
    const DATA = __DATA__;
    const COLORS = ["#0f766e", "#2563eb", "#d97706", "#7c3aed", "#e11d48", "#16a34a", "#475569"];

    function setupCanvas(canvas) {
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(320, Math.floor(rect.width * ratio));
      canvas.height = Math.max(180, Math.floor(rect.height * ratio));
      const ctx = canvas.getContext("2d");
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      return { ctx, width: rect.width, height: rect.height };
    }

    function drawAxes(ctx, x, y, w, h) {
      ctx.strokeStyle = "#d9dee8";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x, y + h);
      ctx.lineTo(x + w, y + h);
      ctx.stroke();
      ctx.strokeStyle = "rgba(217,222,232,0.7)";
      for (let i = 1; i < 4; i++) {
        const gy = y + h * i / 4;
        ctx.beginPath();
        ctx.moveTo(x, gy);
        ctx.lineTo(x + w, gy);
        ctx.stroke();
      }
    }

    function drawLineChart(id, labels, values, color, title) {
      const canvas = document.getElementById(id);
      const { ctx, width, height } = setupCanvas(canvas);
      ctx.clearRect(0, 0, width, height);
      const pad = { l: 44, r: 18, t: 28, b: 42 };
      const x = pad.l, y = pad.t, w = width - pad.l - pad.r, h = height - pad.t - pad.b;
      const max = Math.max(...values, 1);
      drawAxes(ctx, x, y, w, h);
      ctx.fillStyle = "#1d2433";
      ctx.font = "600 14px Segoe UI";
      ctx.fillText(title, x, 18);
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.beginPath();
      values.forEach((v, i) => {
        const px = x + (values.length === 1 ? 0 : i * w / (values.length - 1));
        const py = y + h - (v / max) * h;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
      values.forEach((v, i) => {
        const px = x + (values.length === 1 ? 0 : i * w / (values.length - 1));
        const py = y + h - (v / max) * h;
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(px, py, 4, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
      });
      ctx.fillStyle = "#667085";
      ctx.font = "12px Segoe UI";
      const step = Math.max(1, Math.ceil(labels.length / 8));
      labels.forEach((label, i) => {
        if (i % step !== 0 && i !== labels.length - 1) return;
        const px = x + (labels.length === 1 ? 0 : i * w / (labels.length - 1));
        ctx.fillText(String(label), Math.min(px, x + w - 28), y + h + 24);
      });
    }

    function drawBarChart(id, labels, values, color, title, horizontal=false) {
      const canvas = document.getElementById(id);
      const { ctx, width, height } = setupCanvas(canvas);
      ctx.clearRect(0, 0, width, height);
      const pad = horizontal ? { l: 92, r: 24, t: 30, b: 26 } : { l: 42, r: 18, t: 28, b: 42 };
      const x = pad.l, y = pad.t, w = width - pad.l - pad.r, h = height - pad.t - pad.b;
      const max = Math.max(...values, 1);
      ctx.fillStyle = "#1d2433";
      ctx.font = "600 14px Segoe UI";
      ctx.fillText(title, x, 18);
      ctx.font = "12px Segoe UI";
      values.forEach((v, i) => {
        ctx.fillStyle = color;
        if (horizontal) {
          const row = h / Math.max(values.length, 1);
          const bw = (v / max) * w;
          const by = y + i * row + 4;
          ctx.fillRect(x, by, bw, Math.max(8, row - 8));
          ctx.fillStyle = "#1d2433";
          ctx.fillText(labels[i], 8, by + Math.max(13, row / 2 + 4));
          ctx.fillText(String(v), x + bw + 6, by + Math.max(13, row / 2 + 4));
        } else {
          const gap = 8;
          const bw = Math.max(8, (w - gap * (values.length - 1)) / Math.max(values.length, 1));
          const bh = (v / max) * h;
          const bx = x + i * (bw + gap);
          ctx.fillRect(bx, y + h - bh, bw, bh);
          ctx.fillStyle = "#667085";
          ctx.fillText(labels[i], bx, y + h + 22);
        }
      });
    }

    function drawDonut(id, items) {
      const canvas = document.getElementById(id);
      const { ctx, width, height } = setupCanvas(canvas);
      ctx.clearRect(0, 0, width, height);
      const cx = width / 2, cy = height / 2 - 8, radius = Math.min(width, height) * 0.27;
      const total = Math.max(items.reduce((sum, item) => sum + item.value, 0), 1);
      let start = -Math.PI / 2;
      items.forEach((item, i) => {
        const angle = item.value / total * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radius, start, start + angle);
        ctx.closePath();
        ctx.fillStyle = COLORS[i % COLORS.length];
        ctx.fill();
        start += angle;
      });
      ctx.globalCompositeOperation = "destination-out";
      ctx.beginPath(); ctx.arc(cx, cy, radius * 0.56, 0, Math.PI * 2); ctx.fill();
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "#1d2433";
      ctx.font = "700 20px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText(DATA.fatigue.score.toFixed(1), cx, cy + 7);
      ctx.textAlign = "left";
      ctx.font = "12px Segoe UI";
      items.forEach((item, i) => {
        const lx = 16 + (i % 2) * (width / 2 - 10);
        const ly = height - 60 + Math.floor(i / 2) * 22;
        ctx.fillStyle = COLORS[i % COLORS.length];
        ctx.fillRect(lx, ly - 9, 10, 10);
        ctx.fillStyle = "#667085";
        ctx.fillText(`${item.label}: ${item.value.toFixed(1)}`, lx + 16, ly);
      });
    }

    function renderKeyRows(sortKey="total", asc=false) {
      const filter = document.getElementById("keyFilter").value.trim().toLowerCase();
      const tbody = document.getElementById("keyRows");
      const escapeHtml = value => String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
      const rows = DATA.topKeys
        .filter(item => item.key.toLowerCase().includes(filter))
        .sort((a, b) => {
          const av = a[sortKey], bv = b[sortKey];
          const result = typeof av === "string" ? av.localeCompare(bv) : av - bv;
          return asc ? result : -result;
        });
      tbody.innerHTML = rows.map(item => `
        <tr>
          <td><span class="key-pill">${escapeHtml(item.key)}</span></td>
          <td>${item.total}</td>
          <td>${item.share.toFixed(1)}%</td>
        </tr>
      `).join("") || '<tr><td colspan="3">没有匹配的按键</td></tr>';
    }

    function renderTrend(mode) {
      if (mode === "seven") {
        drawLineChart("trendChart", DATA.sevenDay.map(d => d.date.slice(5)), DATA.sevenDay.map(d => d.total), "#2563eb", "7 天输入趋势");
      } else if (mode === "thirty") {
        drawLineChart("trendChart", DATA.thirtyDay.map(d => d.date.slice(5)), DATA.thirtyDay.map(d => d.total), "#7c3aed", "30 天输入趋势");
      } else {
        drawLineChart("trendChart", DATA.hourly.map(d => `${d.hour}:00`), DATA.hourly.map(d => d.total), "#0f766e", "今日小时输入曲线");
      }
    }

    let sortState = { key: "total", asc: false };
    document.getElementById("scoreMeter").style.width = `${Math.min(100, DATA.fatigue.score)}%`;
    document.getElementById("keyFilter").addEventListener("input", () => renderKeyRows(sortState.key, sortState.asc));
    document.querySelectorAll("th[data-sort]").forEach(th => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        sortState.asc = sortState.key === key ? !sortState.asc : false;
        sortState.key = key;
        renderKeyRows(sortState.key, sortState.asc);
      });
    });
    document.querySelectorAll(".tab").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(item => item.classList.remove("active"));
        btn.classList.add("active");
        renderTrend(btn.dataset.trend);
      });
    });

    function drawAll() {
      renderTrend(document.querySelector(".tab.active").dataset.trend);
      drawDonut("fatigueChart", DATA.fatigue.components);
      drawBarChart("keyChart", DATA.topKeys.map(d => d.key), DATA.topKeys.map(d => d.total), "#d97706", "高频按键分布", true);
      drawBarChart("sessionChart", DATA.sessionHistogram.map(d => d.label), DATA.sessionHistogram.map(d => d.total), "#0f766e", "Session 分钟分布");
      renderKeyRows(sortState.key, sortState.asc);
    }
    window.addEventListener("resize", drawAll);
    drawAll();
  </script>
</body>
</html>"""

    replacements = {
        "__TODAY__": date.today().isoformat(),
        "__ACTIVITY_GUESS__": activity_guess,
        "__SCORE__": f"{fatigue['score']:.1f}",
        "__LEVEL__": fatigue["level"],
        "__ADVICE__": advice,
        "__TODAY_TOTAL__": str(summary["today_total"]),
        "__DELTA__": f"{summary['delta_vs_yesterday']:+d}",
        "__SEVEN_MEAN__": f"{summary['seven_day_mean']:.0f}",
        "__ANOMALY_COUNT__": str(anomaly_count),
        "__PEAKS__": ", ".join(peak_hours) or "暂无",
        "__LOWS__": ", ".join(low_periods) or "暂无",
        "__CHART_FILENAME__": chart_filename,
        "__ANOMALIES__": anomaly_items,
        "__DATA__": data_json,
    }
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    return html
