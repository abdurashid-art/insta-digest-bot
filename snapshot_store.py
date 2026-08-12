import json
import os

SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "account_snapshot.json")


def load_snapshot():
    if not os.path.exists(SNAPSHOT_PATH):
        return None
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(follower_count, best_play_count):
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"follower_count": follower_count, "best_play_count": best_play_count},
            f,
            ensure_ascii=False,
            indent=2,
        )
