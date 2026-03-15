# scoreboard.py
import streamlit as st
import pandas as pd

from score_calculator import (
    compute_game_points,
    PLACEMENT_POINTS,
    BONUS_STAR_POINTS,
    COIN_THRESHOLD_POINTS,
    COIN_THRESHOLD,
    COIN_THRESHOLD_MAX,
    MINIGAME_MOST_WINS_POINTS,
    MINIGAME_SECOND_WINS_POINTS,
)
from consistency import compute_consistency_bonuses


def compute_game_points_breakdown(game, players):
    """
    Return a detailed breakdown of points per rule, per player, for ONE game.
    """
    results = game["results"]
    breakdown = {p: {} for p in players}

    coin_values = {p: int(results[p]["coins"]) for p in players}
    max_coins = max(coin_values.values())
    min_coins = min(coin_values.values())

    mg_wins = {p: int(results[p].get("minigame_wins", 0)) for p in players}
    sorted_unique_mg = sorted(set(mg_wins.values()), reverse=True)

    for p in players:
        r = results[p]

        placement = int(r["placement"])
        placement_pts = PLACEMENT_POINTS.get(placement, 0)

        bonus_stars = int(r["bonus_stars"])
        bonus_star_pts = bonus_stars * BONUS_STAR_POINTS

        coins = int(r["coins"])
        threshold_units = min(coins // COIN_THRESHOLD, COIN_THRESHOLD_MAX)
        coin_threshold_pts = threshold_units * COIN_THRESHOLD_POINTS

        coin_most_pts = 0
        coin_least_pts = 0
        if coin_values[p] == max_coins and max_coins > 0:
            coin_most_pts = 2
        if coin_values[p] == min_coins:
            coin_least_pts = -1

        items_pts = 1 if r.get("most_items_used", False) else 0
        spaces_pts = 1 if r.get("most_spaces_travelled", False) else 0

        minigame_pts = 0
        if sorted_unique_mg and sorted_unique_mg[0] > 0:
            if mg_wins[p] == sorted_unique_mg[0]:
                minigame_pts += MINIGAME_MOST_WINS_POINTS
            elif (
                len(sorted_unique_mg) > 1
                and sorted_unique_mg[1] > 0
                and mg_wins[p] == sorted_unique_mg[1]
            ):
                minigame_pts += MINIGAME_SECOND_WINS_POINTS

        base_total = (
            placement_pts
            + bonus_star_pts
            + coin_threshold_pts
            + coin_most_pts
            + coin_least_pts
            + items_pts
            + spaces_pts
            + minigame_pts
        )

        breakdown[p] = {
            "placement_pts": placement_pts,
            "bonus_star_pts": bonus_star_pts,
            "coin_threshold_pts": coin_threshold_pts,
            "coin_most_pts": coin_most_pts,
            "coin_least_pts": coin_least_pts,
            "items_pts": items_pts,
            "spaces_pts": spaces_pts,
            "minigame_pts": minigame_pts,
            "base_total": base_total,
        }

    return breakdown


def assign_ranks(total_points_by_player):
    """Standard competition ranking (1,2,2,4) with ties."""
    sorted_players = sorted(
        total_points_by_player.items(), key=lambda x: x[1], reverse=True
    )

    ranks = {}
    last_points = None
    last_rank = 0

    for idx, (player, pts) in enumerate(sorted_players, start=1):
        if pts != last_points:
            rank = idx
            last_rank = rank
            last_points = pts
        else:
            rank = last_rank
        ranks[player] = rank

    return ranks


def build_streamlit_cumulative_chart(games_sorted, players):
    running_totals = {p: 0 for p in players}
    chart_rows = []

    for g in games_sorted:
        game_id = g["game_id"]
        game_points = g["points"]

        row = {"Game": game_id}
        for p in players:
            running_totals[p] += int(game_points.get(p, 0))
            row[p] = running_totals[p]

        chart_rows.append(row)

    if not chart_rows:
        st.info("No games available for chart yet.")
        return

    df = pd.DataFrame(chart_rows).set_index("Game")
    st.subheader("Points Progression")
    st.line_chart(df)


def scoreboard_page(players):
    st.header("Scoreboard")

    games = st.session_state.games

    if not games:
        st.info("No games recorded yet. Add a game on the Calculate Scores page.")
        return

    base_totals = {p: 0 for p in players}
    per_game_rows = []
    wins = {p: 0 for p in players}
    podiums = {p: 0 for p in players}

    games_sorted = sorted(games, key=lambda g: g.get("game_id", 0))
    total_games = len(games_sorted)
    games_remaining = max(0, 10 - total_games)

    build_streamlit_cumulative_chart(games_sorted, players)

    for g in games_sorted:
        game_id = g["game_id"]
        results = g["results"]
        breakdown = compute_game_points_breakdown(g, players)

        for p in players:
            pl = int(results[p]["placement"])
            br = breakdown[p]
            base_totals[p] += br["base_total"]

            if pl == 1:
                wins[p] += 1
            if pl in (1, 2, 3):
                podiums[p] += 1

            row = {
                "Game": game_id,
                "Player": p,
                "Place": pl,
                "Placement": br["placement_pts"],
                "Bonus Stars": br["bonus_star_pts"],
                "Coin Threshold": br["coin_threshold_pts"],
                "Most Coins": br["coin_most_pts"],
                "Least Coins": br["coin_least_pts"],
                "Items": br["items_pts"],
                "Spaces": br["spaces_pts"],
                "Minigames": br["minigame_pts"],
                "Game Total": br["base_total"],
            }
            per_game_rows.append(row)

    # ---------- Consistency bonuses ----------
    consistency_totals, per_game_consistency = compute_consistency_bonuses(
        games_sorted, players
    )

    # ---------- Final totals & ranks ----------
    final_totals = {
        p: base_totals[p] + consistency_totals.get(p, 0) for p in players
    }
    ranks = assign_ranks(final_totals)

    rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣"}
    sorted_players = sorted(players, key=lambda p: ranks[p])

    # ---------- Metric cards ----------
    st.subheader(f"Overall Standings — Game {total_games} of 10  ({games_remaining} to go)")
    metric_cols = st.columns(len(players))
    for i, p in enumerate(sorted_players):
        with metric_cols[i]:
            rank_label = rank_emojis.get(ranks[p], f"{ranks[p]}th")
            st.metric(
                label=f"{rank_label} {p}",
                value=f"{final_totals[p]} pts",
                help=f"Wins: {wins[p]}  |  Podiums: {podiums[p]}  |  Consistency bonus: +{consistency_totals.get(p, 0)}",
            )

    # ---------- Detailed standings table ----------
    st.subheader("Detailed Standings")
    standings_rows = []
    for p in sorted_players:
        standings_rows.append({
            "Rank": rank_emojis.get(ranks[p], str(ranks[p])),
            "Player": p,
            "Wins": wins[p],
            "Podiums": podiums[p],
            "Base Points": base_totals[p],
            "Consistency Bonus": consistency_totals.get(p, 0),
            "Total Points": final_totals[p],
        })

    standings_df = pd.DataFrame(standings_rows).reset_index(drop=True)
    st.dataframe(standings_df, use_container_width=True, hide_index=True)

    # ---------- Per-game breakdown ----------
    st.subheader("Per-game breakdown")
    for row in per_game_rows:
        gid = row["Game"]
        p = row["Player"]
        cb = per_game_consistency.get(p, {}).get(gid, 0)
        row["Consistency"] = cb
        row["Total"] = row["Game Total"] + cb

    breakdown_df = pd.DataFrame(per_game_rows).sort_values(["Game", "Player"])
    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    # Expose standings for summary page
    st.session_state.current_standings = standings_df
