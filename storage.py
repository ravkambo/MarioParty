# storage.py
import json
import os

DATA_FILE = "marioparty_data.json"


def load_data():
    """
    Load games + summaries from disk.
    Returns: (games, summaries)
    """
    if not os.path.exists(DATA_FILE):
        # Nothing saved yet
        return [], []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # Corrupt file or empty, start fresh
        return [], []

    games = data.get("games", [])
    summaries = data.get("summaries", [])
    return games, summaries


def save_data(games, summaries):
    """
    Save games + summaries to disk as JSON.
    """
    data = {
        "games": games,
        "summaries": summaries,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
