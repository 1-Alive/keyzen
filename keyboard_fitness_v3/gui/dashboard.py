import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import UI_REFRESH_MS
from gui.charts import make_dashboard_figure


class Dashboard(tk.Tk):
    def __init__(self, stats_service, fatigue_model, anomaly_detector, trend_analyzer, session_manager):
        super().__init__()
        self.stats = stats_service
        self.fatigue = fatigue_model
        self.anomalies = anomaly_detector
        self.trends = trend_analyzer
        self.session_manager = session_manager
        self.canvas = None

        self.colors = {
            "bg": "#f4f1ea",
            "ink": "#20211f",
            "muted": "#6f7169",
            "line": "#ddd6c8",
            "panel": "#ffffff",
            "navy": "#1f2a26",
            "hero_alt": "#283832",
            "teal": "#2f7d73",
            "blue": "#3f6f8f",
            "gold": "#b8873a",
            "red": "#b84a3a",
            "violet": "#7666a6",
        }

        self.title("KeyZen")
        self.icon_image = self._create_window_icon()
        self.iconphoto(True, self.icon_image)
        self.geometry("1280x900")
        self.minsize(1120, 760)
        self.configure(bg=self.colors["bg"])
        self._build_style()
        self._build_ui()
        self.refresh()

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#e8e1d4",
            background=self.colors["teal"],
            bordercolor="#e8e1d4",
            lightcolor=self.colors["teal"],
            darkcolor=self.colors["teal"],
            thickness=12,
        )

    def _create_window_icon(self):
        image = tk.PhotoImage(width=32, height=32)
        image.put("#1f2a26", to=(0, 0, 32, 32))
        image.put("#2f7d73", to=(4, 4, 28, 28))
        image.put("#f4f1ea", to=(7, 8, 25, 24))
        image.put("#b8873a", to=(8, 21, 24, 24))
        image.put("#1f2a26", to=(11, 12, 14, 20))
        image.put("#1f2a26", to=(18, 12, 21, 20))
        image.put("#1f2a26", to=(14, 15, 18, 18))
        return image

    def _draw_brand_icon(self, parent):
        canvas = tk.Canvas(parent, width=64, height=64, bg=self.colors["navy"], highlightthickness=0)
        canvas.create_oval(8, 8, 56, 56, outline="#8fcac0", width=3)
        canvas.create_arc(8, 8, 56, 56, start=300, extent=44, outline=self.colors["navy"], width=5, style=tk.ARC)
        canvas.create_rectangle(17, 22, 47, 44, fill="#f4f1ea", outline="#b8873a", width=2)
        canvas.create_line(20, 39, 44, 39, fill="#b8873a", width=2)
        canvas.create_text(32, 32, text="KZ", fill="#1f2a26", font=("Segoe UI", 12, "bold"))
        return canvas

    def _make_card(self, parent, title, accent):
        frame = tk.Frame(
            parent,
            bg=self.colors["panel"],
            highlightbackground=self.colors["line"],
            highlightthickness=1,
        )
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=7)
        tk.Frame(frame, bg=accent, height=4).pack(fill=tk.X)
        tk.Label(
            frame,
            text=title,
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=16, pady=(13, 4))
        value = tk.Label(
            frame,
            text="--",
            bg=self.colors["panel"],
            fg=self.colors["ink"],
            font=("Segoe UI", 24, "bold"),
        )
        value.pack(anchor="w", padx=16)
        caption = tk.Label(
            frame,
            text="",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 9),
        )
        caption.pack(anchor="w", padx=16, pady=(4, 14))
        return value, caption

    def _build_ui(self):
        hero = tk.Frame(self, bg=self.colors["navy"])
        hero.pack(fill=tk.X)

        brand_icon = self._draw_brand_icon(hero)
        brand_icon.pack(side=tk.LEFT, padx=(24, 0), pady=20)

        title_block = tk.Frame(hero, bg=self.colors["navy"])
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=18, pady=20)
        tk.Label(
            title_block,
            text="KeyZen",
            bg=self.colors["navy"],
            fg="#ffffff",
            font=("Segoe UI", 25, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="键禅 · 在输入节律里保持清醒、专注和松弛",
            bg=self.colors["navy"],
            fg="#c8d7d1",
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(6, 0))

        status_box = tk.Frame(hero, bg=self.colors["hero_alt"], highlightbackground="#43544c", highlightthickness=1)
        status_box.pack(side=tk.RIGHT, padx=24, pady=20)
        tk.Label(status_box, text="当前状态", bg=self.colors["hero_alt"], fg="#c8d7d1", font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(12, 2))
        status_row = tk.Frame(status_box, bg=self.colors["hero_alt"])
        status_row.pack(fill=tk.X, padx=18, pady=(0, 12))
        self.status_dot = tk.Canvas(status_row, width=18, height=18, bg=self.colors["hero_alt"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.status_text = tk.Label(status_row, text="Starting", bg=self.colors["hero_alt"], fg="#ffffff", font=("Segoe UI", 13, "bold"))
        self.status_text.pack(side=tk.LEFT)

        metrics = tk.Frame(self, bg=self.colors["bg"])
        metrics.pack(fill=tk.X, padx=17, pady=(18, 12))
        self.today_value, self.today_caption = self._make_card(metrics, "今日总按键", self.colors["teal"])
        self.speed_value, self.speed_caption = self._make_card(metrics, "当前速度", self.colors["blue"])
        self.fastest_value, self.fastest_caption = self._make_card(metrics, "最快速度", self.colors["gold"])
        self.fatigue_value, self.fatigue_caption = self._make_card(metrics, "Fatigue Score", self.colors["red"])
        self.session_value, self.session_caption = self._make_card(metrics, "输入状态", self.colors["violet"])

        progress_wrap = tk.Frame(self, bg=self.colors["bg"])
        progress_wrap.pack(fill=tk.X, padx=24, pady=(0, 12))
        self.progress = ttk.Progressbar(progress_wrap, maximum=100, mode="determinate")
        self.progress.pack(fill=tk.X)

        body = tk.Frame(self, bg=self.colors["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 22))

        chart_panel = tk.Frame(body, bg=self.colors["panel"], highlightbackground=self.colors["line"], highlightthickness=1)
        chart_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chart_header = tk.Frame(chart_panel, bg=self.colors["panel"])
        chart_header.pack(fill=tk.X, padx=16, pady=(14, 4))
        tk.Label(chart_header, text="趋势与 Session 分布", bg=self.colors["panel"], fg=self.colors["ink"], font=("Segoe UI", 15, "bold")).pack(side=tk.LEFT)
        tk.Label(chart_header, text="每 5 秒刷新", bg=self.colors["panel"], fg=self.colors["muted"], font=("Segoe UI", 9)).pack(side=tk.RIGHT)
        self.chart_frame = tk.Frame(chart_panel, bg=self.colors["panel"])
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        side = tk.Frame(body, width=340, bg=self.colors["panel"], highlightbackground=self.colors["line"], highlightthickness=1)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(16, 0))
        side.pack_propagate(False)
        tk.Label(side, text="分析洞察", bg=self.colors["panel"], fg=self.colors["ink"], font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 8))

        self.quick_facts = tk.Frame(side, bg=self.colors["panel"])
        self.quick_facts.pack(fill=tk.X, padx=16, pady=(0, 10))

        self.insight_text = tk.Text(
            side,
            width=38,
            height=26,
            wrap=tk.WORD,
            bg="#f8fafc",
            fg=self.colors["ink"],
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
        )
        self.insight_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

    def _set_fact(self, label, value, color):
        item = tk.Frame(self.quick_facts, bg="#f8fafc", highlightbackground=self.colors["line"], highlightthickness=1)
        item.pack(fill=tk.X, pady=4)
        tk.Frame(item, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(item, text=label, bg="#f8fafc", fg=self.colors["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        tk.Label(item, text=value, bg="#f8fafc", fg=self.colors["ink"], font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=10, pady=(0, 8))

    def refresh(self):
        summary = self.stats.today_summary()
        fatigue = self.fatigue.calculate()
        anomalies = self.anomalies.detect()
        peaks = self.trends.peak_hours()
        lows = self.trends.low_activity_periods()
        is_active = self.session_manager.is_active()

        self.today_value.configure(text=str(summary["today_total"]))
        self.today_caption.configure(text=f"昨日对比 {summary['delta_vs_yesterday']:+d} keys")
        self.speed_value.configure(text=f"{summary['current_speed']:.0f}")
        self.speed_caption.configure(text="keys/min · 最近 1 分钟")
        self.fastest_value.configure(text=f"{summary['fastest_speed']}")
        self.fastest_caption.configure(text="keys/min · 今日单分钟峰值")
        self.fatigue_value.configure(text=f"{fatigue['score']:.1f}")
        self.fatigue_caption.configure(text=fatigue["level"])
        self.session_value.configure(text="Active" if is_active else "Inactive")
        self.session_caption.configure(text=f"最长 session {fatigue['longest_session_minutes']:.0f} 分钟")
        self.progress["value"] = fatigue["score"]

        color_map = {"Green": "#16a34a", "Yellow": "#d97706", "Orange": "#ea580c", "Red": "#dc2626"}
        color = color_map.get(fatigue["color"], "#667085")
        self.status_dot.delete("all")
        self.status_dot.create_oval(3, 3, 15, 15, fill=color, outline=color)
        self.status_text.configure(text=fatigue["level"])

        self._refresh_facts(summary, fatigue, anomalies, peaks)
        self._refresh_insights(summary, fatigue, anomalies, peaks, lows)
        self._refresh_charts()
        self.after(UI_REFRESH_MS, self.refresh)

    def _refresh_facts(self, summary, fatigue, anomalies, peaks):
        for child in self.quick_facts.winfo_children():
            child.destroy()
        self._set_fact("最快速度", f"{summary['fastest_speed']} keys/min", self.colors["gold"])
        self._set_fact("最近1小时强度", f"{fatigue['recent_keys_per_min']:.1f} keys/min", self.colors["blue"])
        self._set_fact("异常事件", f"{len(anomalies)} 个", self.colors["red"] if anomalies else self.colors["teal"])
        self._set_fact("高峰时段", ", ".join(peaks) if peaks else "暂无", self.colors["teal"])

    def _refresh_insights(self, summary, fatigue, anomalies, peaks, lows):
        self.insight_text.configure(state=tk.NORMAL)
        self.insight_text.delete("1.0", tk.END)
        lines = [
            "今日概览",
            f"今日总按键: {summary['today_total']} keys",
            f"当前速度: {summary['current_speed']:.0f} keys/min",
            f"最快速度: {summary['fastest_speed']} keys/min",
            f"7日均值: {summary['seven_day_mean']:.0f} keys",
            "",
            "疲劳模型",
            f"最近1小时强度: {fatigue['recent_keys_per_min']:.1f} keys/min",
            f"最长session: {fatigue['longest_session_minutes']:.0f} 分钟",
            "",
            "节律",
            "高峰时段: " + (", ".join(peaks) if peaks else "暂无"),
            "低效时段: " + (", ".join(lows) if lows else "暂无"),
            "",
            "异常检测",
        ]
        if anomalies:
            lines.extend([f"- {item['type']}: {item['message']}" for item in anomalies])
        else:
            lines.append("- 暂无异常")
        lines.extend(["", "建议", self._advice(fatigue["score"])])
        self.insight_text.insert(tk.END, "\n".join(lines))
        self.insight_text.configure(state=tk.DISABLED)

    @staticmethod
    def _advice(score):
        if score >= 85:
            return "立即休息 15-30 分钟，并停止连续高强度输入。"
        if score >= 70:
            return "建议安排短休息，降低输入节奏。"
        if score >= 40:
            return "保持节奏，每小时起身活动几分钟。"
        return "状态良好，维持规律输入和休息。"

    def _refresh_charts(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        fig = make_dashboard_figure(self.stats, self.trends)
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
