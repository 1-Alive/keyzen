# Keyboard Fitness V3

本地运行的键盘行为健康分析系统。数据只写入本机 SQLite，不联网，不上传。

## 安装

```bash
cd keyboard_fitness_v3
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 启动

```bash
python main.py
```

日报输出在 `reports/`：

- `report.html`
- `report.png`
- `report_summary.txt`

数据库会在首次运行时自动创建为 `keyboard.db`。

