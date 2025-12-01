import streamlit as st
import pandas as pd

st.title("🎮 Mario Party Championship Scoring")

st.markdown(
    """
Configure your championship below, enter results for each game, and I’ll calculate 
the total points with all bonuses applied.
"""
)

# --- CONFIGURATION ---
num_players = st.number_input("Number of players", min_value=2, max_value=8, value=4, step=1)
num_games = st.number_input("Number of games", min_value=1, max_value=20, value=10, step=1)

st.subheader("Player Names")
players = []
for i in range(num_players):
    name = st.text_input(f"Player {i+1} name", value=f"Player {i+1}")
    players.append(name)

st.markdown("---")
st.subheader("Game Results Input")

# Data storage (per-game, per-player)
placements = {p: [] for p in players}
bonus_stars = {p: [] for p in players}
coins_held = {p: [] for p in players}
minigame_wins = {p: [] for p in players}

placement_points_map = {1: 10, 2: 6, 3: 3, 4: 0}

# --- INPUT TABLES ---
for g in range(1, num_games + 1):
    st.markdown(f"### Game {g}")
    cols = st.columns([2, 1, 1, 1, 1])
    cols[0].markdown("**Player**")
    cols[1].markdown("**Placement (1–4)**")
    cols[2].markdown("**Bonus Stars**")
    cols[3].markdown("**Coins (end)**")
    cols[4].markdown("**Mini-game Wins**")

    for p in players:
        c0, c1, c2, c3, c4 = st.columns([2, 1, 1, 1, 1])
        c0.write(p)
        place = c1.number_input(
            f"Placement G{g} - {p}",
            min_value=1,
            max_value=4,
            value=1,
            step=1,
            key=f"place_{g}_{p}"
        )
        stars = c2.number_input(
            f"Bonus Stars G{g} - {p}",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
            key=f"star_{g}_{p}"
        )
        coins = c3.number_input(
            f"Coins G{g} - {p}",
            min_value=0,
            max_value=999,
            value=0,
            step=1,
            key=f"coin_{g}_{p}"
        )
        mgwins = c4.number_input(
            f"Mini-game Wins G{g} - {p}",
            min_value=0,
            max_value=50,
            value=0,
            step=1,
            key=f"mg_{g}_{p}"
        )

        placements[p].append(place)
        bonus_stars[p].append(stars)
        coins_held[p].append(coins)
        minigame_wins[p].append(mgwins)

st.markdown("---")

# --- CONSISTENCY BONUS CALCULATION ---
def consistency_bonus(placement_list):
    """
    Consistency rules (applied per player across all games):
      - Back-to-back wins (1st place in two consecutive games): +2 points (once)
      - Top 2 in 3 straight games: +3 points (once)
      - No 4th places in any 5-game stretch: +2 points (once)
    """
    n = len(placement_list)
    points = 0

    # Back-to-back wins
    back_to_back = any(
        placement_list[i] == 1 and placement_list[i + 1] == 1
        for i in range(n - 1)
    )
    if back_to_back:
        points += 2

    # Top 2 in 3 straight
    top2_3_straight = any(
        all(placement_list[i + k] <= 2 for k in range(3))
        for i in range(n - 2)
    )
    if top2_3_straight:
        points += 3

    # No 4th places in any 5-game window
    if n >= 5:
        no_fourth_5_games = any(
            all(placement_list[i + k] != 4 for k in range(5))
            for i in range(n - 4)
        )
        if no_fourth_5_games:
            points += 2

    return points

# --- SCORING BUTTON ---
if st.button("Calculate Scores"):
    # Initialize scoring breakdown
    placement_points = {p: 0 for p in players}
    bonus_star_points = {p: 0 for p in players}
    coin_points = {p: 0 for p in players}
    minigame_points = {p: 0 for p in players}
    consistency_points = {p: 0 for p in players}

    # Per-game scoring
    for g in range(num_games):
        # Coins — determine most / least per game
        game_coins = {p: coins_held[p][g] for p in players}
        max_coins = max(game_coins.values())
        min_coins = min(game_coins.values())

        # Mini-games — determine most / second per game
        game_mg = {p: minigame_wins[p][g] for p in players}
        max_mg = max(game_mg.values())
        sorted_mg_vals = sorted(set(game_mg.values()), reverse=True)
        mg_first = sorted_mg_vals[0] if sorted_mg_vals else 0
        mg_second = sorted_mg_vals[1] if len(sorted_mg_vals) > 1 else None

        for p in players:
            # Placement points
            place = placements[p][g]
            placement_points[p] += placement_points_map.get(place, 0)

            # Bonus stars: 2 pts per star
            stars = bonus_stars[p][g]
            bonus_star_points[p] += 2 * stars

            # Coin scoring:
            #   - Most coins: +2
            #   - Least coins: -1
            #   - Every 30 coins (floor), up to 3 points
            c = coins_held[p][g]
            if c == max_coins and max_coins > 0:
                coin_points[p] += 2
            if c == min_coins:
                coin_points[p] -= 1
            coin_points[p] += min(c // 30, 3)

        # Mini-game scoring:
        #   - Most wins: +3
        #   - Second most: +1
        if mg_first is not None and mg_first > 0:
            for p in players:
                if game_mg[p] == mg_first and mg_first > 0:
                    minigame_points[p] += 3

        if mg_second is not None and mg_second > 0:
            # Only award second place if it’s distinct from first
            for p in players:
                if game_mg[p] == mg_second and mg_second > 0:
                    minigame_points[p] += 1

    # Consistency bonuses across all games
    for p in players:
        consistency_points[p] = consistency_bonus(placements[p])

    # Total scoring
    total_points = {}
    for p in players:
        total_points[p] = (
            placement_points[p]
            + bonus_star_points[p]
            + coin_points[p]
            + minigame_points[p]
            + consistency_points[p]
        )

    # Build results table
    data = []
    for p in players:
        data.append(
            {
                "Player": p,
                "Placement Pts": placement_points[p],
                "Bonus Star Pts": bonus_star_points[p],
                "Coin Pts": coin_points[p],
                "Mini-game Pts": minigame_points[p],
                "Consistency Pts": consistency_points[p],
                "TOTAL": total_points[p],
            }
        )

    df = pd.DataFrame(data).sort_values("TOTAL", ascending=False)
    st.subheader("Final Standings")
    st.table(df.reset_index(drop=True))
