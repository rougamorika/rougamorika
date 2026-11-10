# DESIGN CONTRACT — rougamorika profile README

Version 1.0 · 2026-11-10 · owner: **Lead**
This file is the single source of truth for every agent working on this deliverable.
Read it fully before writing anything. If something is missing, ask the Lead — do not guess.

Repo root: `H:\dswork\readme-diy` (this folder becomes the GitHub repo `rougamorika/rougamorika`).

---

## 0. Deliverable map & write scopes

| Path | Owner | Notes |
|---|---|---|
| `README.md` | **readme-writer** | bilingual profile README, Chinese prose + English labels |
| `assets/hero.svg` | **asset-designer** | 1000×260 banner |
| `assets/divider.svg` | **asset-designer** | 1000×24 section divider |
| `assets/dashboard.svg` | **panel-builder** | generated, 1000×680 contribution panel |
| `scripts/gen_dashboard.py` | **panel-builder** | reads `data/stats.json`, writes `assets/dashboard.svg`; deterministic |
| `scripts/fetch_data.py` | Lead | do not edit |
| `data/stats.json`, `data/profile.json` | Lead | read-only input data (real GitHub data) |
| `.github/workflows/update-dashboard.yml` | Lead | daily refresh |
| `preview/**` | **qa-reviewer** | HTML simulation + PNG screenshots |
| `docs/USAGE.md` | Lead | deployment guide |

Do **not** write outside your scope. If you need a shared file changed, message the Lead.

## 1. Brand & voice

Dark, technical, warm. Mint-green accent on near-black. Motifs: sine waves / FFT bars / wind-turbine arcs / LaTeX-like glyphs. **No anime characters, no stock photos.**

- SVG text: **English only** (Chinese glyph rendering differs across systems; README markdown carries the Chinese).
- Tone: understated, precise, a little playful. No hype words ("revolutionary", "ninja", "rockstar", "passionate").
- All numbers come from `data/stats.json`; never hardcode values in the dashboard.

## 2. Design tokens (use exactly)

| Token | Value | Use |
|---|---|---|
| bg | `#0A0F16` | canvas |
| panel | `#0D141D` | cards |
| panel2 | `#111B26` | tiles / inner rows |
| border | `#1B2634` | 1px strokes |
| gridEmpty | `#151F2A` | empty heatmap cells |
| text | `#E6EDF3` | primary |
| text2 | `#A9B7C6` | secondary |
| muted | `#7C8B9C` | labels |
| faint | `#4E5D6D` | footnotes / axes |
| green1 | `#39D353` | accent, brightest |
| green2 | `#2EA043` | mid |
| green3 | `#7EE787` | highlight text |
| greenDeep | `#0E4429` | level-1 fills |
| cyan | `#56D4DD` | secondary accent (charts) |
| amber | `#F2CC60` | awards / best-day highlight |

- Radius: cards `16`, tiles `12`, chips `999`.
- Sans font stack: `Inter, "Segoe UI", "Helvetica Neue", Arial, "Noto Sans", sans-serif`.
- Mono font stack: `"JetBrains Mono", "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace`.
- No web fonts, no `@import`, no external URLs of any kind inside SVG.
- Minimum SVG font size `11`; primary labels ≥ `12`; big numbers `28–34`.
- Letter-spacing `1.2–2.6` for UPPERCASE micro-labels.

## 3. Canvases

| Asset | viewBox / size |
|---|---|
| `hero.svg` | `0 0 1000 260` |
| `dashboard.svg` | `0 0 1000 680` |
| `divider.svg` | `0 0 1000 24` |

Content padding: keep all content within 24 px of each edge (hero: 32 px horizontally).

## 4. Dashboard layout (1000 × 680) — exact grid

Canvas `#0A0F16`; two very subtle radial glows (`#39D353` at 3–5 % opacity) allowed at top-left / bottom-right.

| # | Module | x | y | w | h | Content |
|---|---|---|---|---|---|---|
| 1 | Header | 24 | 20 | 952 | 46 | green square logo mark (24×24, rx 6) + `CONTRIBUTION DASHBOARD` (17px, ls 2.4, text) + `PUBLIC GITHUB ACTIVITY · ALL YEARS` (11px muted) ; right-aligned mono `@rougamorika` 15px green1 at y=40, `updated YYYY-MM-DD` 11px faint at y=58 |
| 2 | Divider | 24 | 74 | 952 | 1 | 1px `#1B2634` |
| 3 | Stat tiles | 24 | 88 | 952 | 76 | 6 tiles, gap 10, width 150.3, rx 12, panel2 fill, border. Label 10.5px muted uppercase ls 1.2 (y+24), value mono 28px text (y+56), sub 10.5px faint (y+70) |
| 4 | History card | 24 | 180 | 952 | 276 | panel fill, rx 16, border |
| 4a | — card title | 48 | 204 | — | — | `CONTRIBUTION HISTORY` 12px muted uppercase ls 1.8 ; right note `ONE CELL = ONE DAY` 10px faint |
| 4b | — year rows | 76 | 216 / 298 / 380 | 530 | 70 each | 3 rows (2024, 2025, 2026), 53 weeks × 7 days, cell 8, gap 2 (pitch 10). Row label (mono 12px, faded) at x=36, y=row_top+34. Empty cell `#151F2A`; levels: 1 `#0E4429`, 2 `#1F6F36`, 3 `#2EA043`, 4 `#39D353`. Month ticks (Jan/Feb…) 9px faint above row 1 only, aligned to week columns |
| 4c | — right panel | 640 | 216 | 312 | 220 | `BY YEAR` 11px muted uppercase ; vertical bars for 2023–2026 at x=656/728/800/872, width 44, gap 28, baseline y=330, max height 120, rounded top rx 4, mint gradient; value 11px mono above bar, year 10.5px faint below. Below: 2 lines — `LONGEST STREAK` + value (e.g. `9 days · Mar 2025`), `BEST DAY` + value (`29 · 2025-03-10`), 11px muted / 13px text |
| 5 | Activity card | 24 | 472 | 616 | 140 | panel fill, rx 16. Title `LAST 12 MONTHS` 12px muted uppercase. Smooth area chart: 12 monthly points, x 48→600, y 512→584, gradient fill `#39D353` 26 %→0 %, 2px green line, dot on max point. X labels every 2 months `YY/MM` 9.5px faint at y=602; y-axis: 2 horizontal grid lines (`#1B2634`) + max value 9.5px |
| 6 | Languages card | 656 | 472 | 320 | 140 | panel fill, rx 16. Title `LANGUAGES` 12px muted uppercase. Up to 5 rows: language name 11px text2, bar track `#151F2A` 6px high rx 3, fill green1/cyan ramp, count `n repos` 10.5px faint right. Footnote `BYTE SHARE: TS 82.9%` 9.5px faint (from data) |
| 7 | Achievements | 24 | 628 | 952 | 26 | 6 chips: rounded 999, fill panel2, border, 10.5px text muted; icon dot 6px green1. Chips generated from data: total contributions, active days, longest streak, original repos, languages, `SINCE 2023` |
| 8 | Footer | 24 | 662 | 952 | 12 | `generated from public GitHub data · @rougamorika · updated YYYY-MM-DD` 10px faint, right-aligned or centered |

Exact numbers may shift ±4 px for optical balance, but module boxes must stay inside the card and never overlap.
Micro-labels may sit 0.2–0.5 px below the nominal sizes above when needed for optical fit
(the generator records these as deliberate adjustments).

## 5. Hero layout (1000 × 260)

- Background: `#0A0F16`, subtle grid (1px lines at 8 % opacity, 40px pitch), radial glow behind the name.
- Kicker (x=32, y=56): `SHANGHAI UNIVERSITY OF ELECTRIC POWER · 2023 – 2027` 11.5px, ls 3, muted.
- Name (x=32, y=140): `ROUGAMO` 76px, weight 800, fill gradient `#E6EDF3 → #7EE787`; optional two-tone split.
- Real name (x=32, y=176): `Fernandez Rougamo Zhou` 19px text2.
- Tagline (x=32, y=214): `SIGNAL PROCESSING · ROBOTICS · WIND ENERGY · MACHINE LEARNING` 11.5px ls 2.2, green1 at 80 %.
- Right motif (x 600–968, y 40–220): sine wave + FFT bar stems + a minimal 3-blade rotor arc, all strokes only; `#39D353` 30–70 % opacity; one dashed circle.
- Bottom hairline (y=238): 1px gradient from transparent → `#1B2634` → transparent.
- Allowed animation: dash-offset flow on the sine (18 s linear) and a 8 s glow pulse; wrap in
  `@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }`.
- `divider.svg`: centered 7×7 diamond (`#39D353`) with a soft green glow, over a 1px line
  from `#2A3A4A` fading out at both ends (must stay visible on `#0D1117`).

## 6. SVG technical rules

1. Valid XML: `xmlns="http://www.w3.org/2000/svg"` + `viewBox` + explicit `width`/`height`.
2. Unique ids, prefixed by asset (`hero-`, `dash-`, `div-`). No duplicate ids.
3. No `<script>`, no external `href`, no `<foreignObject>`, no embedded fonts.
4. Escape `&`, `<`, `>` inside text.
5. Dashboard is generated by `scripts/gen_dashboard.py` from `data/stats.json`; re-running with the same data
   must produce byte-identical output except the `updated` date string. Keep it pagination-free and < 120 KB.
6. Text must not overlap or clip; verify visually at 100 % and at 880 px display width.
7. Colour values only from the token table (alpha variants allowed via `opacity`/`stop-opacity`).

## 7. Data contract — `data/stats.json`

- `user`: `{login, name, blog, location, public_repos, followers, following, created_at, html_url}`
- `contrib`: `{total, active_days, longest_streak:{days,start,end}, current_streak, best_day:{date,count}, avg_per_active_day, first_date, last_date, years:{YYYY:count}}`
  — **use `calendar` (all days, ascending, `[{date,count}]`) for the 2024/2025/2026 mini heatmaps** and `months` for the area chart.
- `heatmap`: `{start, end, weeks: [[ {date,count,level} × 7 ] × N]}` — last 53 weeks (optional fallback)
- `months`: `[{month:"YYYY-MM", count}]` — last 12
- `weekdays`: `{Mon..Sun}`
- `levels`: `{"0".."4": count}`
- `languages`: `{bytes:[{name,bytes,pct}], repos:[{name,repos}]}`
- `repos`: `{total, public_nonfork, stars, forks, featured:[{name,url,description,language,stars,forks}], all:[…]}`
- `events`: `{types, count}`
- `blog`: `{count, articles:[…]}` (currently empty — blog has only an about page)
- `generated_at`, `today`, `timezone`

## 8. README structure (readme-writer)

Order (bilingual headings `中文 · English`):

1. `<div align="center"><img src="assets/hero.svg" width="100%" alt="…"></div>`
2. Badge row (center): blog, email, `SUEP · New Energy 2023–2027`, GitHub. Use shields.io static badges
   (`style=for-the-badge`), colours from tokens (URL-encoded hex, no `#`).
3. `## 关于我 · About Me` — 4–6 句中文 + 1 句英文 italic summary.
4. `## 研究兴趣 · Research Interests` — table/list of 4: 信号处理 / 机械臂 / 风能技术 / 机器学习.
5. `## 贡献面板 · Contribution Dashboard` — `assets/dashboard.svg` (width 100 %), one-line caption
   “数据每日自动更新 / refreshed daily by GitHub Actions”.
6. `## 竞赛与科研 · Awards & Research` — awards table + paper blockquote with link.
7. `## 精选项目 · Selected Projects` — 2×2 table of repo cards (name, language, one line, link).
8. `## 技术栈 · Tech Stack` — compact table or badge rows.
9. `## 最近在忙 · Now` — 3 bullets.
10. `## 联系我 · Get in Touch` — email / GitHub / blog.
11. Footer: `<div align="center"><img src="assets/divider.svg" width="100%"></div>` + small slogan.

Rules: no invented facts (only `data/content-pack.md`), alt text on every image, relative asset paths
(`assets/…`), no raw `<script>`, tables must degrade on mobile (≤3 columns).

## 9. Acceptance gates (Lead + qa-reviewer)

- `python -c "import xml.etree.ElementTree as ET; ET.parse(...)"` passes for every SVG.
- Edge headless screenshot of each asset and of the README preview; visual check for overlap/clipping.
- Dashboard regenerates deterministically: run generator twice → diff only the timestamp.
- No missing asset, no 404 external link (best effort), no Chinese text inside SVG files (regex check).
- README preview must show every image; the page must look intentional at 880 px width.
