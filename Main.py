import streamlit as st
import pandas as pd
from PIL import Image


from scoring import compute_game_points
from consistency import compute_consistency_bonuses
from state import init_state, save_games

import base64
import json
import requests
import streamlit as st

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = st.secrets["REPO_OWNER"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = st.secrets["FILE_PATH"]
BRANCH = st.secrets.get("BRANCH", "main")

API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"


def load_games():
    """
    Fetch games.json from GitHub and return (games_list, sha).
    games_list is a Python list; sha is required for updating.
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    params = {"ref": BRANCH}

    r = requests.get(API_URL, headers=headers, params=params)
    r.raise_for_status()
    data = r.json()

    # GitHub returns base64-encoded file contents
    content_str = base64.b64decode(data["content"]).decode("utf-8")
    games = json.loads(content_str)  # this matches your list structure

    sha = data["sha"]
    return games, sha


def save_games(games, sha, message="Update games.json from Streamlit"):
    """
    Update games.json in GitHub with new contents.
    You MUST include the previous sha.
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    new_content = json.dumps(games, indent=2)
    b64_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": message,
        "content": b64_content,
        "sha": sha,
        "branch": BRANCH,
    }

    r = requests.put(API_URL, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()


st.set_page_config(page_title="Mario Party Championship Tracker", layout="wide")
init_state()

st.title("🎮 Mario Party Championship Tracker")

#Bonus Star Tracker 
bonus_star_tracker = {}



# Sidebar – Players
st.sidebar.header("Players")
edited_players = []
for i, name in enumerate(st.session_state.players):
    edited_players.append(st.sidebar.text_input(f"Player {i+1}", value=name))
st.session_state.players = edited_players

# New Game Entry
st.subheader("New Game Entry")

game_id = st.number_input("Game #", min_value=1, value=len(st.session_state.games) + 1)
uploaded_img = st.file_uploader("Upload Screenshot", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(Image.open(uploaded_img), width=350)

st.markdown("### Player Results")
results = {}
cols = st.columns(len(st.session_state.players))

for i in range(len(st.session_state.players)):
    with cols[i]:
        player = st.selectbox(
            "Player Name",
            options=st.session_state.players,
            key=f"name_{i}_{game_id}"
        )
        placement = st.selectbox("Placement", [1, 2, 3, 4], key=f"p{i}_{game_id}")
        stars = st.number_input("Bonus Stars", min_value=0, step=1, key=f"s{i}_{game_id}")
        coins = st.number_input("Coins", min_value=0, step=1, key=f"c{i}_{game_id}")
        most = st.checkbox("Most Coins", key=f"mc{i}_{game_id}")
        least = st.checkbox("Least Coins", key=f"lc{i}_{game_id}")
        mini = st.radio("Mini-Game", ["none", "second", "most"], key=f"m{i}_{game_id}")

        results[player] = {
            "placement": placement,
            "bonus_stars": stars,
            "coins": coins,
            "most_coins": False, #Auto fill based on input
            "least_coins": False, #Auto fill based on input
            "minigame_rank": mini
        }

if st.button("Save Game"):
    # ✅ Auto-detect most/least coins
    coin_values = {player: results[player]["coins"] for player in results}

    max_coins = max(coin_values.values())
    min_coins = min(coin_values.values())

    for player in results:
        results[player]["most_coins"] = (results[player]["coins"] == max_coins)
        results[player]["least_coins"] = (results[player]["coins"] == min_coins)

    # ✅ Optional: save screenshot
    image_path = None
    if uploaded_img is not None:
        import os
        os.makedirs("images", exist_ok=True)
        ext = uploaded_img.name.split(".")[-1].lower()
        filename = f"game_{int(game_id)}.{ext}"
        image_path = os.path.join("images", filename)
        with open(image_path, "wb") as f:
            f.write(uploaded_img.getvalue())

    # ✅ Save game record
    game_record = {
        "game_id": int(game_id),
        "results": results,
        "image_path": image_path,
    }

    st.session_state.games.append(game_record)
    save_games(st.session_state.games)
    st.rerun()



# Scoring Displays
if st.session_state.games:
    all_rows = []
    for g in st.session_state.games:
        row = {"Game": g["game_id"]}
        pts = compute_game_points(g["results"])
        row.update(pts)
        all_rows.append(row)

    df = pd.DataFrame(all_rows).set_index("Game")
    base_totals = df.sum()

    consistency = compute_consistency_bonuses(st.session_state.games, st.session_state.players)
    consistency_series = pd.Series(consistency)

    grand_totals = base_totals + consistency_series

    st.subheader("Leaderboard")
    st.dataframe(pd.DataFrame({
        "Base Points": base_totals,
        "Consistency Bonus": consistency_series,
        "Total": grand_totals
    }))

    st.subheader("Points Per Game")
    st.dataframe(df)
