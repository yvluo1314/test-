#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechPulse RSS 资讯抓取脚本
抓取多个技术类 RSS 源，解析、去重、过滤营销水文后输出 news.json
由 GitHub Actions 定时调用，生成的 JSON 由前端 index.html 直接加载。
"""

import feedparser
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from time import mktime

# ============================================================
# RSS 源配置：(名称, RSS地址, 分类)
# 分类可选：ai（AI行业）、tech（科技）、dev（程序员）
# 按需增减，修改后提交即生效
# ============================================================
FEEDS = [
    # —— AI 行业 ——
    ("机器之心",     "https://www.jiqizhixin.com/rss",                              "ai"),
    ("量子位",       "https://www.qbitai.com/feed",                                 "ai"),
    ("AI科技评论",   "https://www.leiphone.com/feed",                                "ai"),
    # —— 科技 ——
    ("Hacker News",  "https://hnrss.org/frontpage",                                 "tech"),
    ("InfoQ中文",    "https://www.infoq.cn/feed",                                   "tech"),
    ("少数派",       "https://sspai.com/feed",                                      "tech"),
    # —— 程序员 ——
    ("V2EX",         "https://www.v2ex.com/index.xml",                              "dev"),
    ("掘金前端",     "https://rsshub.app/juejin/category/frontend",                "dev"),
    ("掘金后端",     "https://rsshub.app/juejin/category/backend",                 "dev"),
    ("GitHub Trending", "https://rsshub.app/github/trending/daily",                "dev"),
]

# ============================================================
# 营销水文关键词（命中则过滤）
# 正则表达式，不区分大小写
# ============================================================
MARKETING_PATTERNS = [
    r"加群|加微信|私信|领资料|领取资料|资料包|大礼包",
    r"课程|训练营|培训|辅导班|一对一辅导|包教包会",
    r"咨询(?!一下)|限时优惠|限时秒杀|立减|特惠|秒杀|福利",
    r"名额有限|手慢无|仅剩\d+个|前\d+名",
    r"月入|副业赚钱|零基础.*赚|包就业|就业率.*\d+%",
    r"扫码|关注公众号|回复\d+|添加微信|wx\d+|v信",
]

# 来源可信度映射（1-5），未列出的来源默认 3
SOURCE_CREDIBILITY = {
    "Hacker News": 4,
    "机器之心": 4,
    "量子位": 3,
    "AI科技评论": 3,
    "InfoQ中文": 4,
    "少数派": 3,
    "V2EX": 3,
    "掘金前端": 3,
    "掘金后端": 3,
    "GitHub Trending": 5,
}

# 每个源最多抓取条数
MAX_PER_SOURCE = 15
# 只保留最近多少小时内的资讯
RECENT_HOURS = 48
# 输出最大条数
MAX_OUTPUT = 80


def clean_html(text):
    """去除 HTML 标签，提取纯文本"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_marketing(title, summary):
    """判断是否营销水文"""
    text = (title + " " + summary).lower()
    for pattern in MARKETING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def parse_entry(entry, source_name, category):
    """解析单条 RSS 条目为统一数据结构"""
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    summary = clean_html(entry.get("summary", entry.get("description", "")))

    # 摘要截断到 200 字
    if len(summary) > 200:
        summary = summary[:200] + "..."

    # 发布时间
    published_at = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published_at = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
        published_at = datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)
    else:
        published_at = datetime.now(timezone.utc)

    # 可信度评分
    credibility = SOURCE_CREDIBILITY.get(source_name, 3)

    # 信息密度：按摘要长度估算
    if len(summary) > 100:
        info_density = "high"
    elif len(summary) > 40:
        info_density = "medium"
    else:
        info_density = "low"

    # 生成唯一 ID（标题+链接的 MD5 前 12 位）
    raw_id = title + link
    news_id = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:12]

    # 标签：分类 + 来源（前端可据此搜索和过滤）
    tags = [category, source_name]

    return {
        "id": news_id,
        "title": title,
        "summary": summary,
        "points": [],  # RSS 无结构化要点，前端自动隐藏
        "category": category,
        "source": source_name,
        "extraSources": [],
        "publishedAt": int(published_at.timestamp() * 1000),
        "credibility": credibility,
        "infoDensity": info_density,
        "importance": 5,  # 默认中等，可按需扩展逻辑
        "hotness": 5,
        "tags": tags,
        "isMarketing": False,
        "mergedEventId": None,
        "url": link,  # 原文链接，前端标题可点击跳转
    }


def deduplicate(news_list):
    """简单去重：标题前 20 字（去空格）相同的视为同一事件，合并补充来源"""
    seen = {}
    result = []
    for news in news_list:
        key = re.sub(r"\s+", "", news["title"])[:20]
        if key in seen:
            existing = seen[key]
            if news["source"] not in existing["extraSources"]:
                existing["extraSources"].append(news["source"])
            existing["credibility"] = max(existing["credibility"], news["credibility"])
            existing["importance"] = max(existing["importance"], news["importance"])
        else:
            seen[key] = news
            result.append(news)
    return result


def main():
    all_news = []
    print("=" * 60)
    print("TechPulse RSS 抓取开始")
    print("=" * 60)

    for source_name, feed_url, category in FEEDS:
        try:
            print(f"\n[{source_name}] 抓取中: {feed_url}")
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                print(f"  ⚠ 解析失败: {feed.bozo_exception}")
                continue

            count = 0
            filtered = 0
            for entry in feed.entries[:MAX_PER_SOURCE]:
                news = parse_entry(entry, source_name, category)
                if not news["title"]:
                    continue
                if is_marketing(news["title"], news["summary"]):
                    filtered += 1
                    continue
                all_news.append(news)
                count += 1

            print(f"  ✓ 成功 {count} 条" + (f"，过滤营销 {filtered} 条" if filtered else ""))

        except Exception as e:
            print(f"  ✗ 失败: {e}")

    # 去重
    before_dedup = len(all_news)
    all_news = deduplicate(all_news)
    after_dedup = len(all_news)
    print(f"\n去重: {before_dedup} → {after_dedup}（合并 {before_dedup - after_dedup} 条）")

    # 按发布时间倒序
    all_news.sort(key=lambda x: x["publishedAt"], reverse=True)

    # 只保留最近 N 小时 + 最大输出条数
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=RECENT_HOURS)).timestamp() * 1000)
    all_news = [n for n in all_news if n["publishedAt"] > cutoff][:MAX_OUTPUT]

    # 输出 JSON
    output = {
        "generatedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
        "generatedAtStr": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "count": len(all_news),
        "sources": [s[0] for s in FEEDS],
        "news": all_news,
    }

    output_path = "news.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"完成：共 {len(all_news)} 条资讯")
    print(f"输出文件: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
