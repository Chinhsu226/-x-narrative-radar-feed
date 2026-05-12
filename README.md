# x-narrative-radar-feed

Daily-refreshed JSON feed of AI 行业关键词的推特搜索结果。GitHub Actions 每天 01:00 UTC 跑 `scripts/refresh.py`，结果写到 `feed-radar.json` 并 commit 回 repo。

## 为什么

国内本地直接调 DuckDuckGo 经常被墙。架构上仿照 [zarazhangrui/follow-builders](https://github.com/zarazhangrui/follow-builders)：搜索这种"网络密集型"的活儿挪到 GitHub Actions（美国机房）跑，本地 cron 只是下载预聚合好的 JSON。

## 怎么用

下游消费者直接拉：

```bash
curl -s https://raw.githubusercontent.com/<owner>/x-narrative-radar-feed/main/feed-radar.json
```

或者本地 `x_narrative_radar.py` 加 `--from-feed <url>` 直接吃 JSON。

## 改 watchlist

编辑 `watchlist.json`，commit、push。下次 GitHub Action 自动用新 watchlist 跑。

## 手动触发

去 Actions tab → Refresh Narrative Radar Feed → Run workflow。
