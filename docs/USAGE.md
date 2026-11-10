# 部署说明 · USAGE

这份 README 由「自绘 SVG 资产 + 真实 GitHub 数据」组成，不依赖 github-readme-stats / vercel 等第三方卡片服务（国内访问更稳）。所有面板数据每天由 GitHub Actions 自动重新抓取并提交。

## 1. 文件说明

```
.
├── README.md                      # GitHub 个人主页正文（中英双语）
├── assets/
│   ├── hero.svg                   # 顶部横幅
│   ├── dashboard.svg              # 贡献面板（脚本生成，勿手改）
│   └── divider.svg                # 分隔线
├── data/
│   ├── stats.json                 # 抓取到的真实数据快照
│   └── profile.json               # 账号信息
├── scripts/
│   ├── fetch_data.py              # 抓数据：GitHub REST + 公开贡献历镜像 + 博客仓库
│   └── gen_dashboard.py           # 生成 assets/dashboard.svg
├── .github/workflows/
│   └── update-dashboard.yml       # 每日自动刷新
└── DESIGN.md                      # 设计契约（配色/布局/数据约定）
```

## 2. 让 README 出现在 GitHub 主页（关键）

GitHub 只会把**仓库名与用户名完全相同**的仓库里的 `README.md` 显示在个人主页。

仓库名必须是：`rougamorika`（全小写，和用户名一致）。

两种做法任选其一：

**A. 新建仓库（推荐，干净）**
1. GitHub → New repository → Repository name 填 `rougamorika` → Public → Create。
2. 把本目录所有文件（README.md、assets/、scripts/、data/、.github/、DESIGN.md、.gitignore）推到该仓库的 `main` 分支。
3. 打开 `https://github.com/rougamorika`，主页会自动出现新 README。

**B. 复用已有仓库**
你已有 `rougamorika/IamRougamoRIKA`（description 是 “Config files for my GitHub profile.”）。
在 Settings → Repository name 把它改名为 `rougamorika` 即可（原地址会重定向），再把本目录内容覆盖进去。

## 3. 打开自动更新

1. 仓库 → Settings → Actions → General → Workflow permissions → 选 **Read and write permissions** → Save。
2. 仓库 → Actions → `Update contribution dashboard` → 右侧 **Run workflow** 手动跑一次，确认能生成并提交。
3. 之后每天 03:17 UTC（北京时间 11:17）自动刷新；也可以随时手动触发。

> Actions 里 `fetch_data.py` 会读取 `GITHUB_TOKEN`，避免共享 IP 撞上 GitHub API 的 60 次/小时匿名限额。

## 4. 本地预览 / 重新生成

```powershell
python scripts/fetch_data.py --user rougamorika   # 抓最新数据（需要网络）
python scripts/gen_dashboard.py                   # 重新生成 assets/dashboard.svg
```

只想用已有快照重算（不联网）：

```powershell
python scripts/fetch_data.py --offline --user rougamorika
python scripts/gen_dashboard.py
```

`preview/` 是本地渲染检查用的目录，已在 `.gitignore` 里，不会提交。

## 5. 数据来源与口径

- 贡献热力图 / 连续天数 / 最佳日：公开贡献历镜像 `github-contributions-api.jogruber.de`（与 GitHub 主页同源数据）。
- 仓库、语言、关注者：GitHub REST API `api.github.com`。
- 博客信息：`rougamorika/rougamorika.github.io` 仓库的「关于我」。
- 时区：`Asia/Shanghai`，每日刷新一次，数据可能比 GitHub 主页晚最多一天。

## 6. 想改点什么

| 想改 | 改哪里 |
|---|---|
| 名字 / 标语 / 兴趣文案 | `README.md` |
| 横幅文字与装饰 | `assets/hero.svg`（`ROUGAMO`、kicker、tagline 三处文本） |
| 面板配色 | `scripts/gen_dashboard.py` 顶部的颜色常量 + `DESIGN.md` §2 |
| 面板模块顺序/尺寸 | `scripts/gen_dashboard.py` + `DESIGN.md` §4 |
| 抓取账号 | 工作流里 `--user rougamorika` 和脚本参数 |
| 徽章链接 | `README.md` 顶部 badge 行 |

## 7. 常见问题

- **主页没出现 README**：仓库名不是 `rougamorika`，或仓库是 private，或 README 不在默认分支根目录。
- **图片不更新**：GitHub 图片有缓存（camo），等几分钟；确认 Actions 真的产生了新提交。
- **Actions 失败**：看日志里 `fetch_data.py` 的报错；多半是 API 限额或外部镜像暂时不可用，重跑即可。
- **想彻底不依赖外网服务**：README 里的 shields.io 徽章可以换成纯文本链接，其余图像全部是仓库内 SVG。
