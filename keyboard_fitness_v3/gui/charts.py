from matplotlib.figure import Figure


def make_dashboard_figure(stats_service, trend_analyzer):
    fig = Figure(figsize=(9.6, 6.8), dpi=100)
    fig.patch.set_facecolor("#f4f1ea")

    ax1 = fig.add_subplot(311)
    hourly = stats_service.hourly_counts()
    ax1.plot(hourly["hour"], hourly["total"], color="#2f7d73", linewidth=2.4)
    ax1.fill_between(hourly["hour"], hourly["total"], color="#a7d4cb", alpha=0.35)
    ax1.set_title("Today Hourly Activity")
    ax1.set_xlabel("Hour")
    ax1.set_ylabel("Keys")
    ax1.grid(True, alpha=0.25)

    ax2 = fig.add_subplot(312)
    trend = trend_analyzer.seven_day_trend()
    ax2.plot(trend["date"], trend["total_keys"], marker="o", color="#3f6f8f", linewidth=2.4)
    ax2.set_title("7-Day Trend")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Keys")
    ax2.tick_params(axis="x", rotation=25)
    ax2.grid(True, alpha=0.25)

    ax3 = fig.add_subplot(313)
    sessions = trend_analyzer.session_distribution()
    if sessions.empty:
        ax3.bar([0], [0], color="#b8873a")
        ax3.set_xticks([])
    else:
        ax3.hist(sessions["minutes"], bins=12, color="#b8873a", edgecolor="#6b4c1f")
    ax3.set_title("Session Length Distribution")
    ax3.set_xlabel("Minutes")
    ax3.set_ylabel("Sessions")
    ax3.grid(True, alpha=0.25)

    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor("#ffffff")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#ddd6c8")
        ax.spines["bottom"].set_color("#ddd6c8")
        ax.tick_params(colors="#6f7169")
        ax.title.set_color("#20211f")

    fig.tight_layout(pad=2)
    return fig
