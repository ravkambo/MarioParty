# score_calculator.py
import streamlit as st
from supabase_db import load_games, save_game


# ========= RULESET (single-game scoring) =========
PLACEMENT_POINTS = {1: 8, 2: 6, 3: 4, 4: 2}
BONUS_STAR_POINTS = 2
COIN_THRESHOLD_POINTS = 1
COIN_THRESHOLD = 30
COIN_THRESHOLD_MAX = 3
MINIGAME_MOST_WINS_POINTS = 3
MINIGAME_SECOND_WINS_POINTS = 1


def compute_game_points(game, players):
    """
    Compute total points per player for THIS game only.

    game["results"][player]:
      {
        "placement": int,
        "bonus_stars": int,
        "coins": int,
        "minigame_wins": int,
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

    # --- Most / least coins ---
    coin_values = {p: int(results[p]["coins"]) for p in players}
    max_coins = max(coin_values.values())
    min_coins = min(coin_values.values())

    for p in players:
        if coin_values[p] == max_coins and max_coins > 0:
            points[p] += 2
    for p in players:
        if coin_values[p] == min_coins:
            points[p] -= 1

    # --- Items & movement ---
    for p in players:
        if results[p].get("most_items_used", False):
            points[p] += 1
        if results[p].get("most_spaces_travelled", False):
            points[p] += 1

    # --- Minigame wins: most +3, second-most +1, ties get full points ---
    mg_wins = {p: int(results[p].get("minigame_wins", 0)) for p in players}
    sorted_unique_mg = sorted(set(mg_wins.values()), reverse=True)
    if sorted_unique_mg and sorted_unique_mg[0] > 0:
        most_wins = sorted_unique_mg[0]
        for p in players:
            if mg_wins[p] == most_wins:
                points[p] += MINIGAME_MOST_WINS_POINTS
        if len(sorted_unique_mg) > 1 and sorted_unique_mg[1] > 0:
            second_wins = sorted_unique_mg[1]
            for p in players:
                if mg_wins[p] == second_wins:
                    points[p] += MINIGAME_SECOND_WINS_POINTS

    return points


def score_calculator_page(players):
    st.header("Enter Game Results")

    game_id = st.session_state.next_game_id
    st.subheader(f"Game {game_id}")

    cols = st.columns(len(players))
    raw_results = {}

    # -------- Per-player inputs --------
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

            minigame_wins = st.number_input(
                "Minigame wins",
                min_value=0,
                max_value=99,
                step=1,
                key=f"{player}_minigame_wins_{game_id}",
            )

            raw_results[player] = {
                "placement": placement,
                "bonus_stars": bonus_stars,
                "coins": coins,
                "minigame_wins": minigame_wins,
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

    # -------- Live score preview --------
    preview_game = {"game_id": game_id, "results": raw_results}
    preview_points = compute_game_points(preview_game, players)

    st.subheader("Score Preview")
    preview_cols = st.columns(len(players))
    for i, player in enumerate(players):
        with preview_cols[i]:
            st.metric(label=player, value=f"{preview_points[player]} pts")

    st.markdown("---")

    if st.button("✅ Save Game"):
        game = {
            "game_id": game_id,
            "results": raw_results,
        }

        game_points = compute_game_points(game, players)
        game["points"] = game_points

        st.session_state.games.append(game)
        st.session_state.next_game_id += 1

        st.success(f"Game {game_id} saved!")

        # Clean results card
        place_emoji = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣"}
        sorted_by_pts = sorted(players, key=lambda p: game_points[p], reverse=True)
        result_cols = st.columns(len(players))
        for i, player in enumerate(sorted_by_pts):
            with result_cols[i]:
                pl = raw_results[player]["placement"]
                st.metric(
                    label=f"{place_emoji.get(pl, str(pl))} {player}",
                    value=f"{game_points[player]} pts",
                )

        try:
            save_game(
                session_id=st.session_state.session_id,
                game_id=str(game_id),
                payload=game,
            )
        except Exception as exc:
            st.error(f"Supabase save failed: {exc}")

    # -------- Supabase debug (collapsed) --------
    with st.expander("Saved games (debug)"):
        try:
            saved = load_games(st.session_state.session_id)
            st.write(f"Total saved: {len(saved)}")
            for row in saved:
                label = row.get("created_at") or f"ID {row.get('id', 'n/a')}"
                with st.expander(f"{label} — Game {row['game_id']}"):
                    st.json(row["payload"])
        except Exception as exc:
            st.error(f"Supabase load failed: {exc}")
