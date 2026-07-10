"""
隨機跳轉網站 - 後端
邏輯：使用者按下按鈕 -> 隨機挑選一個內容來源 API -> 取得隨機文章/連結 -> 回傳給前端跳轉
"""
import random
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TIMEOUT = 5.0  # 每個 API 請求最多等 5 秒，避免卡住


# ---------- 各來源的隨機邏輯 ----------

async def pick_hackernews():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        ids = r.json()
        story_id = random.choice(ids[:100])  # 只取前100筆熱門，避免抓到太舊/太冷資料
        r2 = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        item = r2.json()
        url = item.get("url")
        if not url:
            # 有些 HN 貼文沒有外部連結（純討論），改導到討論頁
            url = f"https://news.ycombinator.com/item?id={story_id}"
        return {"source": "Hacker News", "title": item.get("title", ""), "url": url}


async def pick_wikipedia():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(
            "https://zh.wikipedia.org/api/rest_v1/page/random/summary"
        )
        data = r.json()
        url = data.get("content_urls", {}).get("desktop", {}).get("page")
        return {"source": "Wikipedia", "title": data.get("title", ""), "url": url}


async def pick_devto():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get("https://dev.to/api/articles?per_page=30")
        articles = r.json()
        article = random.choice(articles)
        return {
            "source": "Dev.to",
            "title": article.get("title", ""),
            "url": article.get("url"),
        }


# 來源池：之後要新增/移除 API，只要在這裡增減即可（改用 dict，方便用名稱追蹤狀態）
SOURCES = {
    "Hacker News": pick_hackernews,
    "Wikipedia": pick_wikipedia,
    "Dev.to": pick_devto,
}


# ---------- 記憶體內狀態（重啟伺服器會歸零，v1 先這樣做） ----------

from collections import deque

RECENT_URLS_LIMIT = 50
recent_urls = deque(maxlen=RECENT_URLS_LIMIT)  # 近期已跳轉過的網址，超過上限自動丟棄最舊的

round_counter = 0        # 累計成功跳轉次數，用來計算冷卻何時解除
last_source = None       # 上一次選中的來源名稱
streak = 0                # 同一來源連續被選中的次數
cooldown_until = {}       # {來源名稱: 解除冷卻的 round 數}；該來源在此 round 之前都不能被選


def get_available_sources(current_round: int):
    """回傳目前沒有在冷卻中的來源名稱清單"""
    available = [
        name for name in SOURCES
        if cooldown_until.get(name, 0) <= current_round
    ]
    # 極端情況：全部來源都在冷卻中 -> 放寬限制，讓所有來源都可選（避免無法跳轉）
    return available if available else list(SOURCES.keys())


@app.get("/api/jump")
async def jump():
    global round_counter, last_source, streak

    current_round = round_counter + 1  # 這次跳轉暫定的 round 數
    max_attempts = 5
    result = None
    picked_source = None

    for _ in range(max_attempts):
        candidates = get_available_sources(current_round)
        picked_source = random.choice(candidates)
        try:
            candidate_result = await SOURCES[picked_source]()
        except Exception:
            continue  # 這次請求失敗，直接重試（换个来源或同一来源皆有可能）

        url = candidate_result.get("url")
        if not url:
            continue
        if url in recent_urls:
            continue  # 近期跳過這個網址，重新抽

        result = candidate_result
        break

    if result is None:
        raise HTTPException(status_code=502, detail="多次嘗試後仍無法取得不重複的內容，請再按一次跳轉")

    # ---- 更新狀態（只有成功才更新，避免髒資料）----
    recent_urls.append(result["url"])
    round_counter = current_round

    if picked_source == last_source:
        streak += 1
    else:
        streak = 1
    last_source = picked_source

    if streak >= 2:
        # 該來源下一輪暫時排除，之後自動恢復
        cooldown_until[picked_source] = round_counter + 1

    return result


# ---------- 前端靜態頁面 ----------

@app.get("/")
async def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
