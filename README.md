# TechPulse — AI/科技/程序员资讯聚合工具

垂直资讯聚合阅读工具，支持去重、营销水文过滤、可信度评分、关键词收藏、星标、导出等功能。

## 项目结构

```
techpulse/
├── index.html                  # 前端页面（单文件，直接打开即可用）
├── news.json                   # 资讯数据（由 GitHub Actions 自动生成，无需手动编辑）
├── scripts/
│   └── fetch_news.py           # RSS 抓取脚本（解析、去重、过滤、输出 JSON）
├── .github/
│   └── workflows/
│       └── fetch-news.yml      # GitHub Actions 定时任务（每 30 分钟抓取一次）
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

## 快速部署（5 分钟）

### 第一步：创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)，点右上角 **+** → **New repository**
2. Repository name 填 `techpulse`，选 **Public**，点 **Create repository**

### 第二步：上传文件

把本目录下的**所有文件和文件夹**（包括 `.github` 隐藏文件夹）上传到仓库根目录：

- 方式 A（网页上传）：仓库页面 → **Add file** → **Upload files** → 拖入所有文件 → **Commit changes**
- 方式 B（Git 命令行）：
  ```bash
  git init
  git add .
  git commit -m "init: TechPulse news aggregator"
  git branch -M main
  git remote add origin https://github.com/你的用户名/techpulse.git
  git push -u origin main
  ```

### 第三步：开启 GitHub Pages

1. 仓库页面 → **Settings** → 左侧 **Pages**
2. Source 选 **Deploy from a branch**
3. Branch 选 `main`，文件夹选 `/ (root)`，点 **Save**
4. 等 1-2 分钟，页面顶部会显示 `Your site is live at https://你的用户名.github.io/techpulse/`

### 第四步：手动触发一次数据抓取

1. 仓库页面 → **Actions** → 左侧选 **Fetch News** → 点 **Run workflow** → 再点 **Run workflow**
2. 等 1-2 分钟，状态变成绿色 ✓ 表示成功
3. 成功后仓库根目录会出现 `news.json`
4. 打开你的 Pages 链接，就能看到真实资讯了

> 之后每 30 分钟会自动抓取一次，无需人工干预。

## 自定义配置

### 修改 RSS 源

编辑 `scripts/fetch_news.py` 顶部的 `FEEDS` 列表，按格式添加或删除：

```python
FEEDS = [
    ("源名称", "https://example.com/rss", "ai"),  # 分类可选 ai/tech/dev
    # ...
]
```

修改后提交到 GitHub，下次定时任务自动生效。

### 修改抓取频率

编辑 `.github/workflows/fetch-news.yml` 中的 `cron` 表达式：

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'   # 每 30 分钟；改成 '0 * * * *' 为每小时；'*/15 * * * *' 为每 15 分钟
```

> 注意：cron 是 UTC 时间，北京时间 = UTC + 8 小时。GitHub Actions 定时任务可能有 5-10 分钟延迟。

### 修改营销过滤关键词

编辑 `scripts/fetch_news.py` 中的 `MARKETING_PATTERNS` 列表，添加正则表达式即可。

## 本地运行（可选）

想在本地测试抓取脚本：

```bash
pip install -r requirements.txt
python scripts/fetch_news.py
# 运行后会在当前目录生成 news.json
```

然后用浏览器打开 `index.html` 即可查看本地数据。

## 功能说明

| 功能 | 说明 |
|------|------|
| 三分类 | AI 行业 / 科技 / 程序员，左侧导航切换 |
| 手动/自动刷新 | 顶部刷新按钮 + 30 分钟自动刷新（可开关） |
| 四种排序 | 综合 / 最新 / 最热 / 可信度 |
| 事件去重 | 同一事件多来源自动合并，保留主来源+补充来源 |
| 营销水文过滤 | 含加群/私信/课程/训练营/限时优惠等强引导词直接过滤 |
| 可信度评分 | 1-5 星，卡片左侧色条随可信度变化 |
| 信息密度 | 高/中/低三档标签 |
| 已读标记 | 单条已读 / 全部已读，已读卡片降透明度 |
| 关键词收藏 | 自定义关键词，命中自动高亮 + 进入收藏视图 |
| 星标 | 重点资讯星标，支持只看星标 |
| 搜索 | 标题 / 摘要 / 标签全文搜索 |
| 导出 | 导出星标/收藏为 Markdown 或 CSV（Excel 可打开） |
| 本地持久化 | 已读/星标/关键词存在浏览器 localStorage，刷新不丢失 |

## 常见问题

**Q: Actions 运行失败怎么办？**
A: 去 Actions 页面点进失败的任务，看具体报错。常见原因：某个 RSS 源超时或失效（公共 RSSHub 不稳定），可以先在 `FEEDS` 里注释掉可疑的源逐个排查。

**Q: 页面打开但没有资讯？**
A: 检查：① Actions 是否成功运行过（仓库里有没有 `news.json`）；② Pages 部署是否成功；④ 浏览器按 Ctrl+F5 强制刷新清缓存。

**Q: 中文显示乱码？**
A: `news.json` 是 UTF-8 编码，前端用 `fetch` 加载不会乱码。如果是 Excel 打开 CSV 乱码，CSV 文件已带 BOM 头，用 Excel 直接打开即可；仍乱码的话用「数据 → 从文本/CSV 导入」选择 UTF-8。

**Q: 想加更多功能怎么办？**
A: 直接修改 `index.html`（纯前端，所有逻辑都在一个文件里），提交后 Pages 自动更新。数据相关的修改改 `scripts/fetch_news.py`。

## 技术栈

- 前端：原生 HTML/CSS/JS（单文件，零框架依赖）
- 数据抓取：Python + feedparser
- 定时任务：GitHub Actions
- 部署：GitHub Pages
- 持久化：浏览器 localStorage
