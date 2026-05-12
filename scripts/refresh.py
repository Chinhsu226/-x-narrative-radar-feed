#!/usr/bin/env python3
"""
Run from GitHub Actions: 把 watchlist 里每个关键词扔进 DDG 搜 site:x.com，
收集 URL + title + snippet 写到 feed-radar.json，commit 回 repo。

下游消费：本地 x_narrative_radar.py 用 --from-feed 拉这个 JSON，跳过本地搜索。
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ddgs import DDGS

REPO_ROOT = Path(__file__).parent.parent
WATCHLIST = REPO_ROOT / "watchlist.json"
OUTPUT = REPO_ROOT / "feed-radar.json"
TIMELIMIT = "w"   # week 窗口


def search_one(query, max_results=10, retries=2):
    for attempt in range(retries):
        try:
            ddgs = DDGS(timeout=25)
            results = list(ddgs.text(
                f"site:x.com {query}",
                max_results=max_results,
                timelimit=TIMELIMIT,
            ))
            tweets = []
            for r in results:
                url = r.get("href", "")
                if "/status/" in url and "x.com" in url:
                    url = url.split("?")[0]
                    tweets.append({
                        "url": url,
                        "search_title": r.get("title", ""),
                        "search_snippet": r.get("body", ""),
                    })
            return tweets
        except Exception as e:
            print(f"  WARN: '{query[:40]}' attempt {attempt+1}: {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(3)
    return []


def load_watchlist():
    wl = json.loads(WATCHLIST.read_text())
    tier_map = {
        "tier1_kimi_direct": "🎯 Kimi直接相关",
        "tier2_competitive": "⚔️ 竞品大厂动态",
        "tier3_narrative_field": "📡 AI叙事热帖",
        "tier4_startup_growth": "🚀 初创增长打法",
        "tier4_macro": "🌍 宏观趋势",
        "tier5_discovery": "🔭 新产品发现层",
        "tier5_business_narrative": "💰 商业化叙事",
    }
    tiers = {}
    for key, label in tier_map.items():
        td = wl.get(key)
        if isinstance(td, dict) and "keywords" in td:
            tiers[key] = {
                "label": td.get("label", label),
                "keywords": td["keywords"],
            }
    return tiers


def main():
    tiers = load_watchlist()
    if not tiers:
        print("FATAL: 0 tiers in watchlist", file=sys.stderr)
        sys.exit(1)

    total_kw = sum(len(t["keywords"]) for t in tiers.values())
    print(f"Searching {total_kw} keywords across {len(tiers)} tiers...", file=sys.stderr)

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "lookbackTimelimit": TIMELIMIT,
        "watchlistVersion": "v5",
        "tiers": {},
    }
    total_results = 0
    failed_kw = 0
    failed_kw_list = []

    for tier_key, tier_data in tiers.items():
        print(f"\n=== {tier_data['label']} ({len(tier_data['keywords'])} kw) ===", file=sys.stderr)
        tier_out = {"label": tier_data["label"], "keywords": {}}
        for kw in tier_data["keywords"]:
            results = search_one(kw, max_results=10)
            tier_out["keywords"][kw] = results
            total_results += len(results)
            if not results:
                failed_kw += 1
                failed_kw_list.append(kw)
            print(f"  '{kw[:40]}': {len(results)} results", file=sys.stderr)
            time.sleep(1.5)
        output["tiers"][tier_key] = tier_out

    output["totalResults"] = total_results
    output["failedKeywords"] = failed_kw
    output["failedKeywordsList"] = failed_kw_list

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n✅ Wrote {OUTPUT} -- {total_results} URLs total, {failed_kw}/{total_kw} keywords empty", file=sys.stderr)

    if total_results == 0:
        print("FATAL: 0 results across all keywords; not committing empty feed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
