# score_calculator.py
import streamlit as st
from supabase_db import load_games, save_game



# ========= RULESET (single-game scoring) =========
# 1. Placement: 1st 8, 2nd 6, 3rd 4, 4th 2
PLACEMENT_POINTS = {1: 8, 2: 6, 3: 4, 4: 2}

# 2. Bonus Stars: +2 per star
BONUS_STAR_POINTS = 2

# 3. Coins:
#    - +2 for most coins
#    - -1 for least coins
#    - +1 per 30 coins, max +3
COIN_THRESHOLD_POINTS = 1
COIN_THRESHOLD = 30
COIN_THRESHOLD_MAX = 3


def compute_game_points(game, players):
    """
    Compute total points per player for THIS game only.

    game["results"][player]:
      {
        "placement": int,
        "bonus_stars": int,
        "coins": int,
        "most_items_used": bool,
        "most_spaces_travelled": bool,
      }
    """
    results = game["results"]
    points = {p: 0 for p in players}

    # --- Placement + bonus stars + coin thresholds ---
    for p in players:
        r = results[p]

        placement = int(r["placement"])
        points[p] += PLACEMENT_POINTS.get(placement, 0)

        bonus_stars = int(r["bonus_stars"])
        points[p] += bonus_stars * BONUS_STAR_POINTS

        coins = int(r["coins"])
        threshold_bonus = min(coins // COIN_THRESHOLD, COIN_THRESHOLD_MAX)
        points[p] += threshold_bonus * COIN_THRESHOLD_POINTS

    # --- Most / least coins (from coin values) ---
    coin_values = {p: int(results[p]["coins"]) for p in players}
    max_coins = max(coin_values.values())
    min_coins = min(coin_values.values())

    # Most coins: +2 (ties allowed)
    for p in players:
        if coin_values[p] == max_coins and max_coins > 0:
            points[p] += 2

    # Least coins: -1 (ties allowed)
    for p in players:
        if coin_values[p] == min_coins:
            points[p] -= 1

    # --- Items & movement via single-winner flags ---
    for p in players:
        if results[p].get("most_items_used", False):
            points[p] += 1
        if results[p].get("most_spaces_travelled", False):
            points[p] += 1

    return points


def score_calculator_page(players):
    st.header("1️⃣ Enter & Calculate Scores (Single Game)")

    game_id = st.session_state.next_game_id
    st.subheader(f"New Game (Game ID: {game_id})")

    cols = st.columns(len(players))
    raw_results = {}

    # -------- Per-player numeric inputs --------
    for i, player in enumerate(players):
        with cols[i]:
            st.markdown(f"### {player}")

            placement = st.selectbox(
                "Placement",
                options=[1, 2, 3, 4],
                index=0,
                key=f"{player}_placement_{game_id}",
            )

            bonus_stars = st.number_input(
                "Bonus stars",
                min_value=0,
                max_value=10,
                step=1,
                key=f"{player}_bonus_{game_id}",
            )

            coins = st.number_input(
                "Coins",
                min_value=0,
                max_value=999,
                step=1,
                key=f"{player}_coins_{game_id}",
            )

            raw_results[player] = {
                "placement": placement,
                "bonus_stars": bonus_stars,
                "coins": coins,
                "most_items_used": False,
                "most_spaces_travelled": False,
            }

    st.markdown("---")

    # -------- Single-winner selectors --------
    st.subheader("Single-winner bonuses")

    most_items_winner = st.radio(
        "Most items used (+1)",
        options=["None"] + players,
        index=0,
        horizontal=True,
        key=f"most_items_winner_{game_id}",
    )

    most_spaces_winner = st.radio(
        "Most spaces travelled (+1)",
        options=["None"] + players,
        index=0,
        horizontal=True,
        key=f"most_spaces_winner_{game_id}",
    )

    if most_items_winner != "None":
        raw_results[most_items_winner]["most_items_used"] = True

    if most_spaces_winner != "None":
        raw_results[most_spaces_winner]["most_spaces_travelled"] = True

    st.markdown("---")

    if st.button("✅ Calculate & Save Game"):
        game = {
            "game_id": game_id,
            "results": raw_results,
        }

        game_points = compute_game_points(game, players)
        game["points"] = game_points

        st.session_state.games.append(game)
        st.session_state.next_game_id += 1

        st.success(f"Game {game_id} saved.")
        st.write("Points for this game:")
        st.json(game_points)

        try:
            save_game(
                session_id=st.session_state.session_id,
                game_id=str(game_id),
                payload=game,
            )
            st.success("Saved to Supabase!")
        except Exception as exc:
            st.error(f"Supabase save failed: {exc}")

    st.divider()
    st.subheader("Supabase Saved Games")

    try:
        saved = load_games(st.session_state.session_id)
    except Exception as exc:
        st.error(f"Supabase load failed: {exc}")
        saved = []

    st.write(f"Saved games: {len(saved)}")
    for row in saved:
        label = row.get("created_at") or f"ID {row.get('id', 'n/a')}"
        with st.expander(f"{label} — Game {row['game_id']}"):
            st.json(row["payload"])
