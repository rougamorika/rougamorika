#!/usr/bin/env python3
"""Fetch public GitHub + blog data used by the README dashboard.

Usage:
    python scripts/fetch_data.py                # defaults to rougamorika
    python scripts/fetch_data.py --user NAME --out data

Only public, unauthenticated endpoints are used. GitHub REST API budget:
user + repos + events + tree + per-repo languages (~20 calls).

Outputs (under --out):
    raw/user.json          GitHub user object
    raw/repos.json         repository list
    raw/events.json        recent public events
    raw/tree.json          blog repo file tree (articles)
    raw/languages.json     byte counts per repo (top repos)
    raw/contributions.json contribution calendar (all years, jogruber API)
    raw/blog.json          parsed blog article metadata
    profile.json           normalized profile facts
    stats.json             aggregated dashboard numbers
    summary.md             human/agent readable digest
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "dsh-readme-diy/1.0 (+profile-readme-builder)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Optional token: without it the GitHub REST API allows only 60 requests/hour per IP,
# which is usually enough locally but not on shared CI runners.
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def http_get(url: str, *, timeout: int = 40, as_json: bool = True):
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return json.loads(body) if as_json else body


def try_get(url: str, *, as_json: bool = True, timeout: int = 40):
    try:
        return http_get(url, as_json=as_json, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - best effort data collection
        print(f"  ! failed {url}: {exc}", file=sys.stderr)
        return None


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def parse_iso(value: str) -> dt.date:
    return dt.date.fromisoformat(value[:10])


def streak_stats(days: list[dict]) -> dict:
    """days: [{'date':'YYYY-MM-DD','count':N}, ...] sorted ascending."""
    dates = [d["date"] for d in days]
    counts = {d["date"]: d["count"] for d in days}
    best = 0
    best_range = ("", "")
    run = 0
    run_start = ""
    prev = None
    for d in days:
        if d["count"] > 0:
            # run continues only when the previous calendar day was also active
            if run > 0 and (parse_iso(d["date"]) - parse_iso(prev)).days == 1:
                run += 1
            else:
                run = 1
                run_start = d["date"]
            if run > best:
                best = run
                best_range = (run_start, d["date"])
        else:
            run = 0
        prev = d["date"]

    # current streak: walk back from the most recent day
    current = 0
    if days:
        last = days[-1]
        if last["count"] > 0:
            current = 1
            idx = len(days) - 2
            while idx >= 0 and days[idx]["count"] > 0:
                current += 1
                idx -= 1
    active = sum(1 for d in days if d["count"] > 0)
    total = sum(d["count"] for d in days)
    best_day = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    return {
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "total": total,
        "active_days": active,
        "longest_streak": {"days": best, "start": best_range[0], "end": best_range[1]},
        "current_streak": current,
        "best_day": best_day,
        "avg_per_active_day": round(total / active, 2) if active else 0,
    }


def align_week_start(day: dt.date) -> dt.date:
    """Sunday-start weeks, like GitHub's contribution graph."""
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)


def build_heatmap(days: list[dict], today: dt.date, weeks: int = 53) -> dict:
    by_date = {d["date"]: d["count"] for d in days}
    end = today
    start = align_week_start(end) - dt.timedelta(days=(weeks - 1) * 7)
    cells = []
    cursor = start
    while cursor <= end:
        key = cursor.isoformat()
        count = by_date.get(key, 0)
        if count == 0:
            level = 0
        elif count <= 2:
            level = 1
        elif count <= 5:
            level = 2
        elif count <= 9:
            level = 3
        else:
            level = 4
        cells.append({"date": key, "count": count, "level": level})
        cursor += dt.timedelta(days=1)
    # pad to full final week (Saturday ending)
    while len(cells) % 7:
        nxt = parse_iso(cells[-1]["date"]) + dt.timedelta(days=1)
        cells.append({"date": nxt.isoformat(), "count": 0, "level": 0})
    weeks_data = [cells[i : i + 7] for i in range(0, len(cells), 7)]
    return {"start": cells[0]["date"], "end": cells[-1]["date"], "weeks": weeks_data}


def month_series(days: list[dict], today: dt.date, months: int = 12) -> list[dict]:
    counts: dict[str, int] = {}
    for d in days:
        counts[d["date"][:7]] = counts.get(d["date"][:7], 0) + d["count"]
    out = []
    y, m = today.year, today.month
    for _ in range(months):
        key = f"{y:04d}-{m:02d}"
        out.append({"month": key, "count": counts.get(key, 0)})
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="rougamorika")
    ap.add_argument("--out", default=os.path.join(ROOT, "data"))
    ap.add_argument("--blog-repo", default="rougamorika/rougamorika.github.io")
    ap.add_argument("--blog-branch", default="main")
    ap.add_argument(
        "--offline",
        action="store_true",
        help="rebuild stats from existing data/raw/*.json without any network requests",
    )
    ap.add_argument(
        "--fetch-articles",
        action="store_true",
        help="crawl markdown frontmatter of the blog repo to build a latest-posts list",
    )
    args = ap.parse_args()

    user = args.user
    out = os.path.abspath(args.out)
    raw = os.path.join(out, "raw")
    os.makedirs(raw, exist_ok=True)
    print(f"[fetch] user={user} out={out} offline={args.offline}")

    if args.offline:
        def load_raw(name, default):
            path = os.path.join(raw, name)
            if not os.path.exists(path):
                print(f"warn: missing {path}", file=sys.stderr)
                return default
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)

        profile = load_raw("user.json", {})
        repos = load_raw("repos.json", [])
        events = load_raw("events.json", [])
        calendar = load_raw("contributions.json", {"total": {}, "contributions": []})
        tree = load_raw("tree.json", {})
        languages: dict[str, dict[str, int]] = load_raw("languages.json", {})
        if not profile:
            print("fatal: no cached user.json; run without --offline first", file=sys.stderr)
            return 1
    else:
        profile = try_get(f"https://api.github.com/users/{user}")
        if not profile:
            print("fatal: cannot load GitHub user", file=sys.stderr)
            return 1
        write_json(os.path.join(raw, "user.json"), profile)

        repos = try_get(f"https://api.github.com/users/{user}/repos?per_page=100&sort=updated") or []
        write_json(os.path.join(raw, "repos.json"), repos)

        events = try_get(f"https://api.github.com/users/{user}/events/public?per_page=100") or []
        write_json(os.path.join(raw, "events.json"), events)

        rate = try_get("https://api.github.com/rate_limit") or {}
        write_json(os.path.join(raw, "rate_limit.json"), rate)

        # ---- contribution calendar (public mirror of GitHub's graph) ----
        calendar = try_get(f"https://github-contributions-api.jogruber.de/v4/{user}?y=all")
        if not calendar:
            print("warn: contribution calendar unavailable, dashboard will use zeros", file=sys.stderr)
            calendar = {"total": {}, "contributions": []}
        write_json(os.path.join(raw, "contributions.json"), calendar)

        tree = try_get(
            f"https://api.github.com/repos/{args.blog_repo}/git/trees/{args.blog_branch}?recursive=1"
        ) or {}
        write_json(os.path.join(raw, "tree.json"), tree)

        languages = {}

    all_days = sorted(
        ({"date": c["date"], "count": int(c.get("count", 0))} for c in calendar.get("contributions", [])),
        key=lambda d: d["date"],
    )
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date()
    # The mirror pads the calendar with future days of the current year; ignore them.
    days = [d for d in all_days if d["date"] <= today.isoformat()]
    totals = streak_stats(days)
    totals["years"] = {}
    for d in days:
        year = d["date"][:4]
        totals["years"].setdefault(year, 0)
        totals["years"][year] += d["count"]
    heatmap = build_heatmap(days, today, weeks=53)
    months = month_series(days, today, 12)
    weekdays = {k: 0 for k in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
    levels = {str(i): 0 for i in range(5)}
    for d in days:
        wd = dt.date.fromisoformat(d["date"]).strftime("%a")
        weekdays[wd] = weekdays.get(wd, 0) + d["count"]
        lvl = 0 if d["count"] == 0 else 1 if d["count"] <= 2 else 2 if d["count"] <= 5 else 3 if d["count"] <= 9 else 4
        levels[str(lvl)] += 1

    # ---- repositories / languages ----
    clean = []
    non_fork = [r for r in repos if not r.get("fork")]
    for r in repos:
        clean.append(
            {
                "name": r.get("name"),
                "url": r.get("html_url"),
                "description": r.get("description") or "",
                "language": r.get("language") or "",
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "size": r.get("size", 0),
                "fork": bool(r.get("fork")),
                "topics": r.get("topics") or [],
                "updated_at": (r.get("pushed_at") or r.get("updated_at") or "")[:10],
                "created_at": (r.get("created_at") or "")[:10],
                "homepage": r.get("homepage") or "",
            }
        )
    languages = languages if isinstance(languages, dict) else {}
    if not args.offline:
        budget = min(16, len(non_fork))
        for r in sorted(non_fork, key=lambda x: x.get("size", 0), reverse=True)[:budget]:
            lang = try_get(f"https://api.github.com/repos/{user}/{r['name']}/languages")
            if lang:
                languages[r["name"]] = lang
        write_json(os.path.join(raw, "languages.json"), languages)

    lang_bytes: dict[str, int] = {}
    for mapping in languages.values():
        for name, byt in mapping.items():
            lang_bytes[name] = lang_bytes.get(name, 0) + int(byt)
    lang_total = sum(lang_bytes.values()) or 1
    langs = [
        {"name": k, "bytes": v, "pct": round(v * 100 / lang_total, 1)}
        for k, v in sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)
    ]
    repo_lang_count: dict[str, int] = {}
    for r in non_fork:
        if r.get("language"):
            repo_lang_count[r["language"]] = repo_lang_count.get(r["language"], 0) + 1
    repo_lang = [
        {"name": k, "repos": v} for k, v in sorted(repo_lang_count.items(), key=lambda kv: kv[1], reverse=True)
    ]

    top_repos = sorted(
        non_fork, key=lambda r: (r.get("stargazers_count", 0), r.get("size", 0)), reverse=True
    )[:6]
    featured = [
        {
            "name": r["name"],
            "url": r["html_url"],
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
        }
        for r in top_repos
    ]

    # ---- blog articles (repo tree + optional frontmatter) ----
    if not args.offline:
        tree = try_get(
            f"https://api.github.com/repos/{args.blog_repo}/git/trees/{args.blog_branch}?recursive=1"
        ) or {}
        write_json(os.path.join(raw, "tree.json"), tree)
    md_paths = [
        t["path"]
        for t in tree.get("tree", [])
        if t.get("type") == "blob" and t["path"].lower().endswith(".md") and "Templates" not in t["path"]
    ]
    cached_blog = os.path.join(raw, "blog.json")
    if os.path.exists(cached_blog):
        with open(cached_blog, encoding="utf-8") as fh:
            articles = json.load(fh)
    else:
        # This blog keeps only an about page; do not spend requests crawling every markdown
        # file. Pass --fetch-articles when a blog has real posts worth listing.
        articles = []
        if args.fetch_articles and not args.offline:
            for path in md_paths[:20]:
                if "/关于/" in path or path.lower().endswith("readme.md"):
                    continue
                encoded = "/".join(urllib.parse.quote(part) for part in path.split("/"))
                raw_url = f"https://raw.githubusercontent.com/{args.blog_repo}/{args.blog_branch}/{encoded}"
                text = try_get(raw_url, as_json=False, timeout=10)
                if not text:
                    continue
                title = path.rsplit("/", 1)[-1].removesuffix(".md")
                date = ""
                category = path.split("/")[0] if "/" in path else ""
                if text.startswith("---"):
                    fm = text.split("---", 2)[1]
                    for line in fm.splitlines():
                        key, _, val = line.partition(":")
                        key, val = key.strip(), val.strip().strip("'\"")
                        if key == "title" and val:
                            title = val
                        elif key == "date" and val:
                            date = val
                        elif key == "category" and val:
                            category = val
                articles.append({"title": title, "date": date, "category": category, "path": path})
            articles = [a for a in articles if a["title"]]
            articles.sort(key=lambda a: a.get("date") or "", reverse=True)
        write_json(cached_blog, articles)

    # ---- normalized profile + stats ----
    joined = (profile.get("created_at") or "")[:10]
    profile_norm = {
        "login": profile.get("login"),
        "name": profile.get("name"),
        "bio": profile.get("bio"),
        "company": (profile.get("company") or "").lstrip("@"),
        "blog": profile.get("blog"),
        "location": profile.get("location"),
        "email": profile.get("email"),
        "public_repos": profile.get("public_repos"),
        "followers": profile.get("followers"),
        "following": profile.get("following"),
        "created_at": joined,
        "avatar_url": profile.get("avatar_url"),
        "html_url": profile.get("html_url"),
    }
    event_types: dict[str, int] = {}
    for e in events:
        event_types[e.get("type", "?")] = event_types.get(e.get("type", "?"), 0) + 1

    stats = {
        "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "today": today.isoformat(),
        "user": profile_norm,
        "contrib": totals,
        "calendar": days,
        "heatmap": heatmap,
        "months": months,
        "weekdays": weekdays,
        "levels": levels,
        "languages": {"bytes": langs, "repos": repo_lang},
        "repos": {
            "total": len(clean),
            "public_nonfork": len(non_fork),
            "stars": sum(r.get("stargazers_count", 0) for r in repos),
            "forks": sum(r.get("forks_count", 0) for r in repos),
            "featured": featured,
            "all": clean,
        },
        "events": {
            "window": "last ~90 days public events",
            "types": dict(sorted(event_types.items(), key=lambda kv: kv[1], reverse=True)),
            "count": len(events),
        },
        "blog": {"articles": articles, "count": len(articles)},
    }
    write_json(os.path.join(out, "profile.json"), profile_norm)
    write_json(os.path.join(out, "stats.json"), stats)

    # ---- human/agent digest ----
    lines = [
        f"# Data digest — @{user}",
        f"",
        f"- collected: {stats['generated_at']} (Asia/Shanghai), today={stats['today']}",
        f"- name: {profile_norm['name']} | location: {profile_norm['location']} | joined: {joined}",
        f"- followers: {profile_norm['followers']} | following: {profile_norm['following']} | public repos: {profile_norm['public_repos']} (non-fork {len(non_fork)})",
        f"- total contributions (all years): {totals['total']} over {totals['active_days']} active days",
        f"- longest streak: {totals['longest_streak']['days']} d ({totals['longest_streak']['start']} → {totals['longest_streak']['end']}) | current streak: {totals['current_streak']} d",
        f"- best day: {totals['best_day']['date']} ({totals['best_day']['count']}) | avg/active day: {totals['avg_per_active_day']}",
        f"- by year: {totals['years']}",
        f"- last 12 months (heatmap {heatmap['start']} → {heatmap['end']})",
        f"- months: " + ", ".join(f"{m['month']}={m['count']}" for m in months),
        f"- weekdays: {weekdays}",
    ]
    if langs:
        lines.append("- languages: " + ", ".join(f"{l['name']} {l['pct']}%" for l in langs[:8]))
    lines.append("- featured repos: " + "; ".join(f"{f['name']} ({f['language']}, ★{f['stars']})" for f in featured))
    if articles:
        lines.append(f"- blog articles ({len(articles)}):")
        for a in articles[:12]:
            lines.append(f"  - {a['date'] or '—'} [{a['category']}] {a['title']}")
    write_json(os.path.join(out, "summary.json"), stats)
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(( "\n".join(lines) ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
