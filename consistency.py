# consistency.py

def compute_consistency_bonuses(games, players):
    """
    Compute total consistency bonus points per player based on the full season.

    Rules implemented (2025 ruleset):
      - Back-to-back Top 2 finishes: +2 pts (granted on the second game).
      - Top 2 in three straight games: +3 pts (granted on the third game).
      - No 4th places in the last five games: +2 pts
        * checked after Games 5 (Games 1–5)
        * and after Game 10 (Games 6–10).

    Returns:
      total_bonus: dict[player] -> int (sum of all consistency bonuses)
      per_game_bonus: dict[player] -> dict[game_id] -> int
                      (how many bonus points applied in each game)
    """
    # Sort games by game_id to get season order
    games_sorted = sorted(games, key=lambda g: g.get("game_id", 0))

    # Build per-player placement timeline: list of (game_id, placement)
    placements = {p: [] for p in players}
    for g in games_sorted:
        gid = g.get("game_id")
        results = g.get("results", {})
        for p in players:
            if p in results and "placement" in results[p]:
                placements[p].append((gid, int(results[p]["placement"])))

    # Initialize per-game bonus buckets
    per_game_bonus = {
        p: {gid: 0 for gid, _ in placements[p]} for p in players
    }

    for p in players:
        pl_list = placements[p]
        n = len(pl_list)
        if n == 0:
            continue

        # ---------- Back-to-back Top 2 ----------
        # If player is Top 2 in games i-1 and i, give +2 on game i
        for i in range(1, n):
            gid_prev, pl_prev = pl_list[i - 1]
            gid_curr, pl_curr = pl_list[i]
            if pl_prev <= 2 and pl_curr <= 2:
                per_game_bonus[p][gid_curr] += 2

        # ---------- Top 2 in three straight ----------
        # If player is Top 2 in games i-2, i-1, i, give +3 on game i
        for i in range(2, n):
            gid1, pl1 = pl_list[i - 2]
            gid2, pl2 = pl_list[i - 1]
            gid3, pl3 = pl_list[i]
            if pl1 <= 2 and pl2 <= 2 and pl3 <= 2:
                per_game_bonus[p][gid3] += 3

        # ---------- No 4th places in last 5 ----------
        # Window 1: Games 1–5, bonus applied at game 5
        if n >= 5:
            window1 = pl_list[0:5]
            if all(pl != 4 for _, pl in window1):
                gid5, _ = pl_list[4]
                per_game_bonus[p][gid5] += 2

        # Window 2: Games 6–10, bonus applied at game 10
        # (Assuming a 10-game season, so use entries 5–9 as "games 6–10")
        if n >= 10:
            window2 = pl_list[5:10]
            if all(pl != 4 for _, pl in window2):
                gid10, _ = pl_list[9]
                per_game_bonus[p][gid10] += 2

    # Sum total consistency bonus per player
    total_bonus = {
        p: sum(per_game_bonus[p].values()) for p in players
    }

    return total_bonus, per_game_bonus
