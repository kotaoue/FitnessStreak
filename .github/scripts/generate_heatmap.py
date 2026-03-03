import json
from datetime import date, timedelta
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
RESULTS_DIR = Path("results")
OUTPUT_FILE = RESULTS_DIR / "heatmap.svg"

CELL = 11       # cell size (px)
GAP  = 2        # gap between cells (px)
STEP = CELL + GAP

LEFT_PAD  = 28  # room for day-of-week labels
TOP_PAD   = 30  # room for title + month labels
RIGHT_PAD = 8
BOT_PAD   = 28  # room for legend

# 0–4 exercises done → colour (light → dark, warm red palette)
COLORS = [
    "#ebedf0",  # 0 – no activity (light gray)
    "#ffcba4",  # 1 – light orange
    "#ff8c61",  # 2 – orange
    "#e84545",  # 3 – vivid red
    "#9b2335",  # 4 – deep red
]

DAY_LABELS  = {1: "Mon", 3: "Wed", 5: "Fri"}  # row index → label (0 = Sun)
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ── Data loading ───────────────────────────────────────────────────────────────
def load_data() -> dict:
    """Return {YYYY-MM-DD: count_of_true_exercises}."""
    data = {}
    for f in RESULTS_DIR.glob("????-??-??.json"):
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
            count = sum(1 for v in obj.get("exercises", {}).values() if v)
            data[obj["date"]] = count
        except Exception:
            pass
    return data


# ── Date grid ──────────────────────────────────────────────────────────────────
def build_grid(today: date):
    """
    Return a list of weeks; each week is a list of 7 dates (Sun … Sat).
    The grid covers the last ~52 weeks ending today.
    """
    # Start from the Sunday on or before (today – 364 days)
    start = today - timedelta(days=364)
    # isoweekday: Mon=1 … Sun=7  → subtract to reach the preceding Sunday
    start -= timedelta(days=start.isoweekday() % 7)  # 0 if already Sun
    weeks = []
    cur = start
    while cur <= today:
        weeks.append([cur + timedelta(days=i) for i in range(7)])
        cur += timedelta(weeks=1)
    return weeks


# ── SVG generation ────────────────────────────────────────────────────────────
def generate_svg(data: dict) -> str:
    today   = date.today()
    weeks   = build_grid(today)
    n_weeks = len(weeks)
    total   = sum(data.values())

    width  = LEFT_PAD + n_weeks * STEP + RIGHT_PAD
    height = TOP_PAD  + 7 * STEP       + BOT_PAD

    parts = []

    # ── SVG header ──
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}">'
    )
    parts.append(
        f'<rect width="{width}" height="{height}" rx="6" fill="#0d1117"/>'
    )
    parts.append(
        '<style>text { font-family: -apple-system, BlinkMacSystemFont, '
        '"Segoe UI", Helvetica, Arial, sans-serif; fill: #8b949e; font-size: 9px; }</style>'
    )

    # ── Total count ──
    parts.append(
        f'<text x="{LEFT_PAD}" y="11" font-size="9">'
        f'{total} exercises in the last year</text>'
    )

    # ── Month labels ──
    prev_month = None
    for wi, week in enumerate(weeks):
        m = week[0].month
        if m != prev_month:
            x = LEFT_PAD + wi * STEP
            parts.append(
                f'<text x="{x}" y="{TOP_PAD - 4}">{MONTH_NAMES[m - 1]}</text>'
            )
            prev_month = m

    # ── Day-of-week labels ──
    for row, label in DAY_LABELS.items():
        y = TOP_PAD + row * STEP + CELL - 1
        parts.append(
            f'<text x="0" y="{y}" dominant-baseline="middle">{label}</text>'
        )

    # ── Cells ──
    for wi, week in enumerate(weeks):
        x = LEFT_PAD + wi * STEP
        for row, d in enumerate(week):
            if d > today:
                continue  # don't draw future cells
            y     = TOP_PAD + row * STEP
            key   = d.isoformat()
            count = data.get(key, 0)
            color = COLORS[min(count, len(COLORS) - 1)]
            tip   = f"{key}: {count}/4"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}"'
                f' rx="2" fill="{color}"><title>{tip}</title></rect>'
            )

    # ── Legend ──
    legend_y  = TOP_PAD + 7 * STEP + GAP + 6
    legend_x  = width - RIGHT_PAD - (len(COLORS) * STEP) - 26
    parts.append(f'<text x="{legend_x - 2}" y="{legend_y + CELL - 1}" dominant-baseline="middle">Less</text>')
    for i, color in enumerate(COLORS):
        lx = legend_x + 22 + i * STEP
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}"'
            f' rx="2" fill="{color}"/>'
        )
    more_x = legend_x + 22 + len(COLORS) * STEP + 2
    parts.append(f'<text x="{more_x}" y="{legend_y + CELL - 1}" dominant-baseline="middle">More</text>')

    parts.append('</svg>')
    return "\n".join(parts)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = load_data()
    svg  = generate_svg(data)
    OUTPUT_FILE.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}  ({len(data)} days of data)")
