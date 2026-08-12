import os
import random
import time
import requests

HIKER_KEY = os.environ["HIKERAPI_KEY"]
BASE = "https://api.hikerapi.com"
HEADERS = {"x-access-key": HIKER_KEY}


def _get(url, params, retries=3):
    """GET с повторными попытками — страхует от случайных сетевых обрывов."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    raise last_exc

MY_USERNAME = "future.dentt"

# Ротация запросов на вирусные reels — берём по 3-4 за прогон, чтобы не тратить
# лишние платные запросы HikerAPI и каждый раз получать что-то новое.
QUERY_POOL = [
    "day in my life",
    "study with me",
    "pov student",
    "storytime",
    "medical school",
    "college life",
    "жизнь студента",
    "учеба в меде",
    "лайфхак",
    "универ",
    "истории из жизни",
    "медицинский университет",
    "get ready with me",
    "before and after transformation",
    "life hack",
    "до и после",
    "работа мечты",
    "relatable",
    "funny fail",
    "смешные моменты",
]

VIEWS_MIN = 300_000
VIEWS_MAX = 10_000_000


def get_my_profile():
    r = _get(f"{BASE}/v1/user/by/username", {"username": MY_USERNAME})
    return r.json()


def get_my_top_clips(user_id, amount=5):
    r = _get(f"{BASE}/gql/user/clips",
             {"user_id": user_id, "sort_by_views": "true", "flat": "true"})
    items = r.json().get("items", [])
    out = []
    for it in items[:amount]:
        caption = (it.get("caption") or {})
        text = caption.get("text", "") if isinstance(caption, dict) else ""
        out.append({
            "play_count": it.get("play_count"),
            "like_count": it.get("like_count"),
            "comment_count": it.get("comment_count"),
            "caption": text,
        })
    return out


def search_viral_reels(query, limit=5):
    r = _get(f"{BASE}/v2/search/reels", {"query": query})
    data = r.json()
    results = []
    for mod in data.get("reels_serp_modules", []):
        for c in mod.get("clips", []):
            m = c.get("media", {})
            play = m.get("play_count") or 0
            if not (VIEWS_MIN <= play <= VIEWS_MAX):
                continue
            user = m.get("user") or {}
            caption = (m.get("caption") or {})
            text = caption.get("text", "") if isinstance(caption, dict) else ""
            results.append({
                "query": query,
                "username": user.get("username"),
                "play_count": play,
                "like_count": m.get("like_count"),
                "comment_count": m.get("comment_count"),
                "caption": text[:300],
            })
    results.sort(key=lambda x: -x["play_count"])
    return results[:limit]


def collect_trend_digest(num_queries=4, per_query=3):
    """Берёт случайные num_queries запросов из пула и собирает вирусные reels."""
    queries = random.sample(QUERY_POOL, min(num_queries, len(QUERY_POOL)))
    found = []
    seen_usernames_captions = set()
    for q in queries:
        for item in search_viral_reels(q, limit=per_query):
            key = (item["username"], item["caption"][:60])
            if key in seen_usernames_captions:
                continue
            seen_usernames_captions.add(key)
            found.append(item)
    found.sort(key=lambda x: -x["play_count"])
    return found
