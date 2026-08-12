import os
import time

import requests

from hiker_helper import get_my_profile, get_my_top_clips, collect_trend_digest
from digest_helper import build_account_update_text, generate_trend_breakdown_and_scenarios
from snapshot_store import load_snapshot, save_snapshot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_message(text, retries=3):
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
                timeout=30,
            )
            resp.raise_for_status()
            return
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    raise last_exc


def main():
    profile = get_my_profile()
    top_clips = get_my_top_clips(profile["pk"])
    prev = load_snapshot()

    account_text = build_account_update_text(profile, top_clips, prev)
    send_message(account_text)
    time.sleep(1)

    trend_items = collect_trend_digest(num_queries=5, per_query=3)
    if trend_items:
        breakdown_text, scenarios_text = generate_trend_breakdown_and_scenarios(trend_items)
        send_message(breakdown_text)
        if scenarios_text:
            time.sleep(1)
            send_message(scenarios_text)
    else:
        send_message(
            "Сегодня не нашлось новых вирусных Reels по проверяемым темам — попробуем в следующий раз."
        )

    best_play = top_clips[0]["play_count"] if top_clips else 0
    save_snapshot(profile["follower_count"], best_play)


if __name__ == "__main__":
    main()
