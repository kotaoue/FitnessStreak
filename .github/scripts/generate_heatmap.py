"""Generate a GitHub-style fitness heatmap as an SVG file.

Reads exercise JSON files from the results/ directory, counts True values
per day, and renders a 52-week contribution-graph-style heatmap.
"""

import json
import logging
from datetime import date, timedelta
from pathlib import Path

RESULTS_DIR = Path("results")
OUTPUT_FILE = RESULTS_DIR / "heatmap.svg"

CELL = 11  # cell size in pixels
GAP = 2    # gap between cells in pixels
STEP = CELL + GAP

LEFT_PAD = 28   # space for day-of-week labels
TOP_PAD = 30    # space for title and month labels
RIGHT_PAD = 36
BOT_PAD = 28    # space for legend

# Colour scale: 0–4 exercises done (muted gray → deep red)
COLORS = [
    "#330b0b",  # 0 – no activity (near-black dark red)
    "#4e1111",  # 1 – dark red
    "#812222",  # 2 – mid red
    "#b43434",  # 3 – bright-mid red
    "#e84545",  # 4 – vivid red
]

DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # row index → label (0 = Sun)
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data() -> dict[str, int]:
    """Load exercise counts from JSON files in RESULTS_DIR.

    Returns:
        A mapping of ISO date strings to the count of completed exercises.
    """
    data: dict[str, int] = {}
    for path in RESULTS_DIR.glob("????-??-??.json"):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            count = sum(1 for v in obj.get("exercises", {}).values() if v)
            data[obj["date"]] = count
        except Exception as exc:
            logging.warning("Skipping %s: %s", path.name, exc)
    return data


def build_grid(today: date) -> list[list[date]]:
    """Build a 52-week Sunday-anchored calendar grid ending on *today*.

    Args:
        today: The reference date (last cell in the grid).

    Returns:
        A list of weeks, each week being a list of 7 consecutive dates
        starting on Sunday.
    """
    start = today - timedelta(days=364)
    start -= timedelta(days=start.isoweekday() % 7)  # rewind to preceding Sunday
    weeks = []
    cur = start
    while cur <= today:
        weeks.append([cur + timedelta(days=i) for i in range(7)])
        cur += timedelta(weeks=1)
    return weeks


def _render_month_labels(weeks: list[list[date]]) -> list[str]:
    """Return SVG text elements for month labels along the top of the grid.

    Args:
        weeks: The calendar grid produced by build_grid().

    Returns:
        A list of SVG element strings.
    """
    parts: list[str] = []
    prev_month = None
    for wi, week in enumerate(weeks):
        m = week[0].month
        if m != prev_month:
            x = LEFT_PAD + wi * STEP
            parts.append(f'<text x="{x}" y="{TOP_PAD - 4}">{MONTH_NAMES[m - 1]}</text>')
            prev_month = m
    return parts


def _render_day_labels() -> list[str]:
    """Return SVG text elements for day-of-week labels on the left of the grid.

    Returns:
        A list of SVG element strings.
    """
    parts: list[str] = []
    for row, label in DAY_LABELS.items():
        y = TOP_PAD + row * STEP + CELL - 1
        parts.append(f'<text x="0" y="{y}" dominant-baseline="middle">{label}</text>')
    return parts


def _render_cells(weeks: list[list[date]], today: date, data: dict[str, int]) -> list[str]:
    """Return SVG rect elements for every day cell in the grid.

    Args:
        weeks: The calendar grid produced by build_grid().
        today: Cells after this date are skipped.
        data: A mapping of ISO date strings to exercise counts (0–4).

    Returns:
        A list of SVG element strings.
    """
    parts: list[str] = []
    for wi, week in enumerate(weeks):
        x = LEFT_PAD + wi * STEP
        for row, d in enumerate(week):
            if d > today:
                continue
            y = TOP_PAD + row * STEP
            key = d.isoformat()
            count = data.get(key, 0)
            color = COLORS[min(count, len(COLORS) - 1)]
            tip = f"{key}: {count}/4"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}"'
                f' rx="2" fill="{color}"><title>{tip}</title></rect>'
            )
    return parts


def _render_legend(width: int) -> list[str]:
    """Return SVG elements for the Less/More color legend at the bottom.

    Args:
        width: Total SVG canvas width, used to right-align the legend.

    Returns:
        A list of SVG element strings.
    """
    parts: list[str] = []
    legend_y = TOP_PAD + 7 * STEP + GAP + 6
    legend_x = width - RIGHT_PAD - (len(COLORS) * STEP) - 26
    parts.append(
        f'<text x="{legend_x - 2}" y="{legend_y + CELL - 1}" dominant-baseline="middle">Less</text>'
    )
    for i, color in enumerate(COLORS):
        lx = legend_x + 22 + i * STEP
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    more_x = legend_x + 22 + len(COLORS) * STEP + 2
    parts.append(
        f'<text x="{more_x}" y="{legend_y + CELL - 1}" dominant-baseline="middle">More</text>'
    )
    return parts


def generate_svg(data: dict[str, int]) -> str:
    """Render the heatmap as an SVG string.

    Args:
        data: A mapping of ISO date strings to exercise counts (0–4).

    Returns:
        The complete SVG document as a string.
    """
    today = date.today()
    weeks = build_grid(today)
    n_weeks = len(weeks)
    total = sum(data.values())

    width = LEFT_PAD + n_weeks * STEP + RIGHT_PAD
    height = TOP_PAD + 7 * STEP + BOT_PAD

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="6" fill="#0d1117"/>',
        '<style>text { font-family: -apple-system, BlinkMacSystemFont, '
        '"Segoe UI", Helvetica, Arial, sans-serif; fill: #8b949e; font-size: 9px; }</style>',
        f'<text x="{LEFT_PAD}" y="11" font-size="9">'
        f'{total} exercises in the last year</text>',
    ]
    parts.extend(_render_month_labels(weeks))
    parts.extend(_render_day_labels())
    parts.extend(_render_cells(weeks, today, data))
    parts.extend(_render_legend(width))
    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARNING)
    data = load_data()
    svg = generate_svg(data)
    OUTPUT_FILE.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}  ({len(data)} days of data)")
