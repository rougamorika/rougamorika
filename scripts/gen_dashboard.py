#!/usr/bin/env python3
"""Generate assets/dashboard.svg from data/stats.json.

The dashboard is fully data-driven: every number comes from the JSON snapshot
produced by scripts/fetch_data.py, so re-running this script on fresh data
refreshes the whole panel.

Usage:
    python scripts/gen_dashboard.py
    python scripts/gen_dashboard.py --data data/stats.json --out assets/dashboard.svg
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H = 1000, 680
PAD = 24

# ---------------------------------------------------------------- design tokens
BG = "#0A0F16"
PANEL = "#0D141D"
PANEL2 = "#111B26"
BORDER = "#1B2634"
GRID_EMPTY = "#151F2A"
TEXT = "#E6EDF3"
TEXT2 = "#A9B7C6"
MUTED = "#7C8B9C"
FAINT = "#4E5D6D"
GREEN1 = "#39D353"
GREEN2 = "#2EA043"
GREEN3 = "#7EE787"
GREEN_DEEP = "#0E4429"
CYAN = "#56D4DD"

SANS = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace"

LEVELS = {0: GRID_EMPTY, 1: "#1F6F36", 2: GREEN2, 3: GREEN1, 4: GREEN3}

CARD_Y = {"history": 180, "activity": 472}


# ---------------------------------------------------------------- helpers
def esc(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_num(value: int) -> str:
    return f"{value:,}"


def text(
    x: float,
    y: float,
    body: object,
    *,
    size: float = 12,
    fill: str = TEXT,
    weight: int | None = None,
    anchor: str = "start",
    ls: float | None = None,
    family: str = "sans",
    opacity: float | None = None,
) -> str:
    attrs = [f'x="{x:g}"', f'y="{y:g}"', f'font-size="{size:g}"', f'fill="{fill}"']
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if ls is not None:
        attrs.append(f'letter-spacing="{ls:g}"')
    if family == "mono":
        attrs.append(f'font-family="{MONO}"')
    elif family == "sans":
        attrs.append(f'font-family="{SANS}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity:g}"')
    return f'<text {" ".join(attrs)}>{esc(body)}</text>'


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = "none",
    stroke: str | None = None,
    rx: float = 0,
    opacity: float | None = None,
) -> str:
    attrs = [f'x="{x:g}"', f'y="{y:g}"', f'width="{w:g}"', f'height="{h:g}"']
    if rx:
        attrs.append(f'rx="{rx:g}"')
    attrs.append(f'fill="{fill}"')
    if stroke:
        attrs.append(f'stroke="{stroke}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity:g}"')
    return f'<rect {" ".join(attrs)}/>'


def smooth_path(points: list[tuple[float, float]], top: float, bottom: float) -> str:
    """Catmull-Rom spline as cubic Beziers, clamped to the plot band."""
    if not points:
        return ""
    if len(points) == 1:
        return f"M {points[0][0]:.2f} {points[0][1]:.2f}"
    d = f"M {points[0][0]:.2f} {points[0][1]:.2f}"
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1x, c1y = p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6
        c2x, c2y = p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6
        d += (
            f" C {c1x:.2f} {max(top, min(bottom, c1y)):.2f}"
            f" {c2x:.2f} {max(top, min(bottom, c2y)):.2f}"
            f" {p2[0]:.2f} {p2[1]:.2f}"
        )
    return d


def level_of(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def year_grid(by_date: dict[str, int], year: int) -> tuple[list[list[int]], list[tuple[int, str]]]:
    """53 weeks × 7 days for one calendar year (Sunday-start weeks, GitHub style)."""
    jan1 = dt.date(year, 1, 1)
    start = jan1 - dt.timedelta(days=(jan1.weekday() + 1) % 7)
    weeks: list[list[int]] = []
    for w in range(53):
        row = []
        for d in range(7):
            day = start + dt.timedelta(days=w * 7 + d)
            row.append(by_date.get(day.isoformat(), 0) if day.year == year else 0)
        weeks.append(row)
    month_ticks: list[tuple[int, str]] = []
    for month in range(1, 13):
        first = dt.date(year, month, 1)
        week = (first - start).days // 7
        if 0 <= week < 53:
            month_ticks.append((week, first.strftime("%b").upper()))
    return weeks, month_ticks


# ---------------------------------------------------------------- modules
def header(stats: dict) -> str:
    user = stats["user"]["login"]
    updated = stats.get("today") or stats.get("generated_at", "")[:10]
    out = [
        '<g id="dash-header">',
        rect(PAD, 18, 26, 26, fill=GREEN_DEEP, stroke=GREEN2, rx=7),
        f'<path d="M30 31 h3.2 l2.1-5.2 3.4 10.4 2.1-5.2 h3.2" fill="none" '
        f'stroke="{GREEN1}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
        text(60, 33, "CONTRIBUTION DASHBOARD", size=17, weight=600, ls=2.2, fill=TEXT),
        text(60, 50, "PUBLIC GITHUB ACTIVITY · ALL YEARS", size=10.5, fill=MUTED, ls=1.4),
        text(976, 33, f"@{user}", size=15, family="mono", fill=GREEN1, anchor="end"),
        text(976, 50, f"updated {updated} · Asia/Shanghai", size=10.5, fill=FAINT, anchor="end"),
        '<line x1="24" y1="72" x2="976" y2="72" stroke="%s" stroke-width="1"/>' % BORDER,
        "</g>",
    ]
    return "\n".join(out)


def stat_tiles(stats: dict) -> str:
    contrib = stats["contrib"]
    user = stats["user"]
    first_year = min(stats["contrib"]["years"].keys())
    active = contrib["active_days"]
    # account age is the honest denominator (the calendar snapshot includes the whole first year)
    account_start = dt.date.fromisoformat((user.get("created_at") or contrib["first_date"])[:10])
    today = dt.date.fromisoformat(stats["today"])
    tracked = (today - account_start).days + 1
    pct = active * 100 / tracked if tracked else 0
    streak = contrib["longest_streak"]
    start, end = streak.get("start") or streak.get("end", ""), streak.get("end", "")

    tiles = [
        ("TOTAL CONTRIBUTIONS", fmt_num(contrib["total"]), f"since {first_year}"),
        ("ACTIVE DAYS", fmt_num(active), f"{pct:.1f}% of account days"),
        ("LONGEST STREAK", f'{streak["days"]:g} d', f"{start} → {end[5:]}"),
        ("BEST DAY", fmt_num(contrib["best_day"]["count"]), contrib["best_day"]["date"]),
        ("PUBLIC REPOS", fmt_num(user["public_repos"]), f'{stats["repos"]["public_nonfork"]} original'),
        ("FOLLOWERS", fmt_num(user["followers"]), f'{user["following"]} following'),
    ]
    gap = 10
    width = (W - 2 * PAD - gap * (len(tiles) - 1)) / len(tiles)
    out = ['<g id="dash-tiles">']
    for i, (label, value, sub) in enumerate(tiles):
        x = PAD + i * (width + gap)
        out += [
            rect(x, 88, width, 76, fill=PANEL2, stroke=BORDER, rx=12),
            f'<rect x="{x + 14:g}" y="102" width="18" height="2.4" rx="1.2" fill="{GREEN2}" opacity=".8"/>',
            text(x + 14, 126, label, size=10.2, fill=MUTED, ls=0.8),
            text(x + 14, 152, value, size=27, weight=700, family="mono", fill=TEXT),
            text(x + 14, 166, sub, size=9.8, fill=FAINT),
        ]
    out.append("</g>")
    return "\n".join(out)


def history_card(stats: dict) -> str:
    by_date = {d["date"]: d["count"] for d in stats["calendar"]}
    years = [2024, 2025, 2026]
    top = CARD_Y["history"]
    out = [
        f'<g id="dash-history">',
        rect(PAD, top, W - 2 * PAD, 276, fill=PANEL, stroke=BORDER, rx=16),
        text(48, 200, "CONTRIBUTION HISTORY", size=12, fill=MUTED, ls=1.8),
        text(952, 200, "ONE CELL = ONE DAY", size=9.5, fill=FAINT, anchor="end", ls=1),
    ]
    grid_x, cell, gap = 76, 8, 2
    pitch = cell + gap
    row_tops = [220, 302, 384]
    empties: list[str] = []
    actives: list[str] = []
    for year, row_top in zip(years, row_tops):
        weeks, month_ticks = year_grid(by_date, year)
        if year == years[0]:
            for week, label in month_ticks:
                out.append(
                    text(grid_x + week * pitch + 1, row_top - 6, label, size=9.0, fill=FAINT, ls=0.4)
                )
        out.append(text(64, row_top + 37, str(year), size=12, family="mono", fill=MUTED, anchor="end"))
        for w, col in enumerate(weeks):
            for d, count in enumerate(col):
                x = grid_x + w * pitch
                y = row_top + d * pitch
                if count == 0:
                    empties.append(rect(x, y, cell, cell, fill=GRID_EMPTY, rx=1.4))
                else:
                    actives.append(rect(x, y, cell, cell, fill=LEVELS[level_of(count)], rx=1.4))
    out.append(f'<g stroke="{BORDER}" stroke-opacity=".45">' + "".join(empties) + "</g>")
    out += actives
    # right panel: by year + records
    years_all = [y for y in (2023, 2024, 2025, 2026) if str(y) in stats["contrib"]["years"]]
    values = [stats["contrib"]["years"].get(str(y), 0) for y in years_all]
    max_v = max(values) or 1
    base_y = 336
    max_h = 96
    out += [text(640, 230, "BY YEAR", size=11, fill=MUTED, ls=1.6)]
    for i, (year, value) in enumerate(zip(years_all, values)):
        bar_h = max(3.0, value / max_v * max_h)
        x = 656 + i * 72
        out.append(
            f'<rect x="{x:g}" y="{base_y - bar_h:.2f}" width="40" height="{bar_h:.2f}" rx="3" '
            f'fill="url(#dash-bar)"/>'
        )
        out.append(text(x + 20, base_y - bar_h - 7, fmt_num(value), size=10.5, family="mono",
                        fill=TEXT2, anchor="middle"))
        out.append(text(x + 20, base_y + 15, str(year), size=10, fill=FAINT, anchor="middle",
                        family="mono"))
    out += [
        f'<line x1="640" y1="360" x2="952" y2="360" stroke="{BORDER}" stroke-width="1"/>',
        text(640, 382, "LONGEST STREAK", size=9.8, fill=MUTED, ls=1.1),
        text(952, 382, f'{stats["contrib"]["longest_streak"]["days"]} days', size=12.5, fill=TEXT,
             anchor="end", family="mono"),
        text(640, 408, "BEST DAY", size=9.8, fill=MUTED, ls=1.1),
        text(952, 408, f'{stats["contrib"]["best_day"]["count"]} · {stats["contrib"]["best_day"]["date"]}',
             size=12.5, fill=TEXT, anchor="end", family="mono"),
        text(640, 434, "AVG / ACTIVE DAY", size=9.8, fill=MUTED, ls=1.1),
        text(952, 434, fmt_num(round(stats["contrib"]["avg_per_active_day"], 1)), size=12.5, fill=TEXT,
             anchor="end", family="mono"),
        "</g>",
    ]
    return "\n".join(out)


def activity_card(stats: dict) -> str:
    months = stats["months"]
    values = [m["count"] for m in months]
    max_v = max(values) or 1
    left, right = 56, 624
    top, baseline = 514, 592
    n = len(values)
    step = (right - left) / (n - 1) if n > 1 else 0

    def y_of(v: int) -> float:
        return baseline - (v / max_v) * (baseline - top) * 0.9

    points = [(left + i * step, y_of(v)) for i, v in enumerate(values)]
    line = smooth_path(points, top, baseline)
    area = line + f" L {points[-1][0]:.2f} {baseline} L {points[0][0]:.2f} {baseline} Z"
    peak_i = max(range(n), key=lambda i: values[i])
    peak = points[peak_i]

    out = [
        '<g id="dash-activity">',
        rect(PAD, CARD_Y["activity"], 616, 140, fill=PANEL, stroke=BORDER, rx=16),
        text(48, 496, "LAST 12 MONTHS", size=12, fill=MUTED, ls=1.8),
        text(616, 496, "MONTHLY CONTRIBUTIONS", size=9.5, fill=FAINT, anchor="end", ls=1),
        f'<line x1="{left}" y1="{baseline}" x2="{right}" y2="{baseline}" stroke="{BORDER}" stroke-width="1"/>',
        f'<line x1="{left}" y1="{(top + baseline) / 2:.0f}" x2="{right}" y2="{(top + baseline) / 2:.0f}" '
        f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="2 4" opacity=".8"/>',
        f'<path d="{area}" fill="url(#dash-area)"/>',
        f'<path d="{line}" fill="none" stroke="{GREEN1}" stroke-width="2" stroke-linejoin="round"/>',
        text(48, top + 3, fmt_num(max_v), size=9.5, fill=FAINT, anchor="end", family="mono"),
        text(48, baseline + 3, "0", size=9.5, fill=FAINT, anchor="end", family="mono"),
        f'<circle cx="{peak[0]:.2f}" cy="{peak[1]:.2f}" r="4" fill="{GREEN3}" stroke="{BG}" stroke-width="1.5"/>',
        text(peak[0], peak[1] - 9, fmt_num(values[peak_i]), size=10, fill=GREEN3, anchor="middle",
             family="mono"),
    ]
    for i, m in enumerate(months):
        if i % 2:
            continue
        x = left + i * step
        yy, mm = m["month"].split("-")
        out.append(text(x, 608, f"{yy[2:]}/{mm}", size=9.5, fill=FAINT, anchor="middle", family="mono"))
    out.append("</g>")
    return "\n".join(out)


def languages_card(stats: dict) -> str:
    repos = stats["languages"]["repos"][:4]
    total_repos = sum(r["repos"] for r in stats["languages"]["repos"]) or 1
    max_repos = max((r["repos"] for r in repos), default=1)
    bytes_share = stats["languages"]["bytes"][0] if stats["languages"]["bytes"] else None
    out = [
        '<g id="dash-languages">',
        rect(656, CARD_Y["activity"], 320, 140, fill=PANEL, stroke=BORDER, rx=16),
        text(680, 496, "LANGUAGES", size=12, fill=MUTED, ls=1.8),
        text(952, 496, "BY PRIMARY LANGUAGE", size=9.5, fill=FAINT, anchor="end", ls=1),
    ]
    for i, item in enumerate(repos):
        y = 522 + i * 19
        bar_w = 84 * item["repos"] / max_repos
        out.append(text(680, y + 3, item["name"], size=11, fill=TEXT2))
        out.append(rect(760, y - 5, 84, 6, fill=GRID_EMPTY, rx=3))
        out.append(rect(760, y - 5, max(3, bar_w), 6, fill=GREEN1, rx=3, opacity=0.85))
        out.append(text(936, y + 3, f'{item["repos"]}', size=11, fill=TEXT, anchor="end", family="mono"))
        out.append(text(940, y + 3, "repos", size=9.3, fill=FAINT))
    if bytes_share:
        out.append(
            text(680, 602, f'BYTE SHARE · {bytes_share["name"].upper()} {bytes_share["pct"]:g}%',
                 size=9.3, fill=FAINT, ls=0.8)
        )
    out.append("</g>")
    return "\n".join(out)


def achievements(stats: dict) -> str:
    contrib = stats["contrib"]
    top_lang = stats["languages"]["bytes"][0] if stats["languages"]["bytes"] else None
    chips = [
        f'{fmt_num(contrib["total"])} CONTRIBUTIONS',
        f'{contrib["active_days"]} ACTIVE DAYS',
        f'{contrib["longest_streak"]["days"]}-DAY STREAK',
        f'{stats["repos"]["public_nonfork"]} ORIGINAL REPOS',
        f'{top_lang["pct"]:g}% {top_lang["name"].upper()}' if top_lang else "POLYGLOT",
        f'SINCE {min(contrib["years"].keys())}',
    ]
    size, gap, pad = 10.2, 8, 13
    widths = [pad * 2 + 10 + len(c) * size * 0.62 for c in chips]
    total = sum(widths) + gap * (len(chips) - 1)
    x = (W - total) / 2
    y = 630
    out = ['<g id="dash-achievements">']
    for chip, width in zip(chips, widths):
        out += [
            rect(x, y, width, 24, fill=PANEL2, stroke=BORDER, rx=12),
            f'<circle cx="{x + pad + 2:.2f}" cy="{y + 12:.2f}" r="2.6" fill="{GREEN1}"/>',
            text(x + pad + 11, y + 15.6, chip, size=size, fill=TEXT2, ls=0.7),
        ]
        x += width + gap
    out.append("</g>")
    return "\n".join(out)


def footer(stats: dict) -> str:
    updated = stats.get("today") or stats.get("generated_at", "")[:10]
    return (
        '<g id="dash-footer">'
        + text(24, 666, "PUBLIC GITHUB DATA · GENERATED WITH PYTHON", size=9.3, fill=FAINT, ls=1)
        + text(976, 666, f'@{stats["user"]["login"]} · UPDATED {updated}', size=9.3, fill=FAINT,
               anchor="end", ls=1)
        + "</g>"
    )


def build(stats: dict) -> str:
    defs = f"""<defs>
    <radialGradient id="dash-glow-a" cx="0" cy="0" r="1">
      <stop offset="0" stop-color="{GREEN1}" stop-opacity=".07"/>
      <stop offset="1" stop-color="{GREEN1}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="dash-glow-b" cx="0" cy="0" r="1">
      <stop offset="0" stop-color="{CYAN}" stop-opacity=".05"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="dash-bar" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="{GREEN_DEEP}"/>
      <stop offset=".55" stop-color="{GREEN2}"/>
      <stop offset="1" stop-color="{GREEN1}"/>
    </linearGradient>
    <linearGradient id="dash-area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GREEN1}" stop-opacity=".30"/>
      <stop offset=".65" stop-color="{GREEN1}" stop-opacity=".08"/>
      <stop offset="1" stop-color="{GREEN1}" stop-opacity="0"/>
    </linearGradient>
  </defs>"""
    body = [
        defs,
        rect(0, 0, W, H, fill=BG),
        f'<ellipse cx="120" cy="40" rx="520" ry="320" fill="url(#dash-glow-a)"/>',
        f'<ellipse cx="900" cy="650" rx="420" ry="240" fill="url(#dash-glow-b)"/>',
        header(stats),
        stat_tiles(stats),
        history_card(stats),
        activity_card(stats),
        languages_card(stats),
        achievements(stats),
        footer(stats),
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "stats.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "dashboard.svg"))
    args = ap.parse_args()
    with open(args.data, encoding="utf-8") as fh:
        stats = json.load(fh)
    svg = build(stats)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    print(f"[dashboard] wrote {args.out} ({len(svg.encode('utf-8'))} bytes)")
    print(
        f"[dashboard] contributions={stats['contrib']['total']} "
        f"years={sorted(stats['contrib']['years'])} "
        f"months={len(stats['months'])} languages={len(stats['languages']['bytes'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
