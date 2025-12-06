import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO

# ---------------------------
# Config & Helpers
# ---------------------------

st.set_page_config(
    page_title="Mario Party Championship Tracker",
    layout="wide",
)

DEFAULT_PLAYERS = ["Amber", "Mandeep", "Rav", "Simer"]

def init_state():
    if "players" not in st.session_state:
        st.session_state.players = DEFAULT_PLAYERS.copy()
    if "games" not in st.session_state:
        # each game: {"game_id": int, "image_bytes": bytes|None, "results": {player: {...}}}
        st.session_state.games = []

def placement_points(place: int) -> int:
    mapping = {1: 10, 2: 6, 3: 3, 4: 0}
    return mapping.get(place, 0)

def bonus_star_points(stars: int) -> int:
    return stars * 2

def coin_points(coins: int, most: bool, least: bool) -> int:
    pts = 0
    if most:
        pts += 2
    if least:
        pts -= 1
    pts += min(coins // 30, 3)
    return pts

def minigame_points(rank: str) -> int:
    """
    rank: "most", "second", "none"
    """
    if rank == "most":
        return 3
    if rank == "second":
        return 1
    return 0

def compute_game_points(game):
    """
    Returns a dict: {player_name: total_points_for_this_game}
    """
    totals = {}
    for player, rec in game["results"].items():
        base = placement_points(rec["placement"])
        bonus = bonus_star_points(rec["bonus_stars"])
        coins = coin_points(rec["coins"], rec["most_coins"], rec["least_coins"])
        mini = minigame_points(rec["minigame_rank"])
        totals[player] = base + bonus + coins + mini
    return totals

def compute_all_totals(games, players):
    """
    Build:
    - per_game_df: rows = games, columns = players (points per game)
    - total_series: cumulative points per player
    """
    if not games:
        return None, None

    rows = []
    for g in games:
        pts = compute_game_points(g)
        row = {"Game": g["game_id"]}
        for p in players:
            row[p] = pts.get(p, 0)
        rows.append(row)

    per_game_df = pd.DataFrame(rows).set_index("Game")
    total_series = per_game_df.sum(axis=0).sort_values(ascending=False)
    return per_game_df, total_series


# ---------------------------
# App Layout
# ---------------------------

init_state()

st.title("🎮 Mario Party Championship Tracker")
st.caption("Upload a screenshot, enter results, and track your season.")

# --- Sidebar: player config & controls ---
st.sidebar.header("Players")
edited_players = []
for i, name in enumerate(st.session_state.players):
    new_name = st.sidebar.text_input(f"Player {i+1} name", value=name, key=f"player_name_{i}")
    edited_players.append(new_name.strip() or f"Player {i+1}")
st.session_state.players = edited_players

if st.sidebar.button("Reset all data"):
    st.session_state.games = []
    st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.write(f"Total games recorded: **{len(st.session_state.games)}**")

# --- Main: New Game Entry ---
st.subheader("1️⃣ Record a New Game")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("#### Game Info")
    next_game_id = len(st.session_state.games) + 1
    game_id = st.number_input("Game #", value=next_game_id, min_value=1, step=1)

    uploaded_img = st.file_uploader(
        "Upload end-of-game screenshot (optional)",
        type=["png", "jpg", "jpeg"],
    )

with col_right:
    if uploaded_img is not None:
        img = Image.open(uploaded_img)
        st.markdown("#### Screenshot Preview")
        st.image(img, use_column_width=True)
    else:
        st.info("Upload a screenshot to have it attached to this game (optional).")

st.markdown("#### Player Results")

results = {}
cols = st.columns(len(st.session_state.players))

for idx, player in enumerate(st.session_state.players):
    with cols[idx]:
        st.markdown(f"**{player}**")

        placement = st.selectbox(
            "Placement",
            options=[1, 2, 3, 4],
            index=idx if idx < 4 else 0,
            key=f"place_{player}_{game_id}",
        )

        bonus_stars = st.number_input(
            "Bonus Stars",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
            key=f"stars_{player}_{game_id}",
        )

        coins = st.number_input(
            "Coins (end of game)",
            min_value=0,
            max_value=999,
            value=0,
            step=1,
            key=f"coins_{player}_{game_id}",
        )

        st.markdown("Coins bonus flags:")
        most_coins = st.checkbox(
            "Most coins",
            key=f"most_{player}_{game_id}",
        )
        least_coins = st.checkbox(
            "Least coins",
            key=f"least_{player}_{game_id}",
        )

        st.markdown("Mini-games:")
        mini_rank = st.radio(
            "Mini-game result",
            options=["none", "second", "most"],
            index=0,
            key=f"mini_{player}_{game_id}",
        )

        results[player] = {
            "placement": placement,
            "bonus_stars": bonus_stars,
            "coins": coins,
            "most_coins": most_coins,
            "least_coins": least_coins,
            "minigame_rank": mini_rank,
        }

st.markdown("---")

save_col1, save_col2 = st.columns([1, 3])
with save_col1:
    if st.button("💾 Save Game"):
        image_bytes = None
        if uploaded_img is not None:
            # Store raw bytes so we can re-open later if we want
            image_bytes = uploaded_img.getvalue()

        game_record = {
            "game_id": int(game_id),
            "image_bytes": image_bytes,
            "results": results,
        }

        # If a game with same id exists, overwrite it
        existing_ids = [g["game_id"] for g in st.session_state.games]
        if game_record["game_id"] in existing_ids:
            idx = existing_ids.index(game_record["game_id"])
            st.session_state.games[idx] = game_record
        else:
            st.session_state.games.append(game_record)

        st.success(f"Game #{int(game_id)} saved.")
        st.experimental_rerun()


# ---------------------------
# History & Standings
# ---------------------------

st.subheader("2️⃣ Game History & Standings")

per_game_df, total_series = compute_all_totals(
    st.session_state.games,
    st.session_state.players
)

if per_game_df is None:
    st.info("No games recorded yet. Save a game above to see standings.")
else:
    st.markdown("#### Points per Game")
    st.dataframe(per_game_df.style.format("{:.0f}"))

    st.markdown("#### Overall Standings")
    standings_df = total_series.reset_index()
    standings_df.columns = ["Player", "Total Points"]
    st.table(standings_df)

    st.markdown("---")
    st.markdown("#### Raw Game Data (debug view)")
    st.json(st.session_state.games)
