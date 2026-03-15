# pages/1_Rules.py

import streamlit as st

st.title("📜 Mario Party Championship Rules (2025)")

st.caption("Balanced competition-ready ruleset for the 10-game season.")

# 1. Placement Points
st.header("1. Placement Points")

st.markdown("""
Final placement in each game awards points as follows:

- 🥇 **1st place:** 8 points  
- 🥈 **2nd place:** 6 points  
- 🥉 **3rd place:** 4 points  
- 🪙 **4th place:** 2 points  
""")

# 2. Bonus Stars
st.header("2. Bonus Stars")

st.markdown("""
- Each **Bonus Star** earned is worth **+2 points**.  
- Bonus Stars are added **on top** of placement points.
""")

# 3. Coins
st.header("3. Coins")

st.markdown("""
Coin-related bonuses are awarded **after** the game ends:

- **Most coins held at game end:** +2 points  
- **Least coins held at game end:** −1 point  
- **Coin threshold bonus:** +1 point for every **30 coins** held at game end  
  - Capped at **maximum +3 points** from this threshold.  
""")

# 4. Minigames
st.header("4. Minigames")

st.markdown("""
Minigame performance gives extra points:

- **Most minigame wins:** +3 points  
- **Second-most minigame wins:** +1 point  
- **Ties:**  
  - Tied players each receive the **full listed points** (no splitting, no half-points).  
""")

# 5. Consistency Bonuses
st.header("5. Consistency Bonuses")

st.markdown("""
Consistency is rewarded across the season:

- **Back-to-back Top 2 finishes:**  
  - **+2 points**, awarded on the **second** consecutive Top 2 game.  

- **Top 2 in three straight games:**  
  - **+3 points**, awarded on the **third** consecutive Top 2 game.  

- **No 4th places in the last five games:**  
  - **+2 points**, checked after **Game 5** and **Game 10**.  

All of the above use **effective placement**, meaning **after any handicap effects** (like Safety Shell) are applied.
""")

# 6. Items & Movement
st.header("6. Items & Movement")

st.markdown("""
Extra bonuses to reward active play:

- **Most items used in a game:** +1 point  
- **Most spaces travelled in a game:** +1 point  
""")

# 7. Handicap — “Safety Shell”
st.header("7. Handicap — “Safety Shell”")

st.markdown("""
The **Safety Shell** keeps players engaged if they fall behind:

- A player earns **one Safety Shell** after **two consecutive actual 4th-place finishes**.  
- A player may hold **at most 1 shell at a time**.  

When a Safety Shell is active, on the **next game only**:

1. The player's **placement counts as one rank higher** for:
   - Scoring  
   - Streak / consistency checks  

2. If the player starts that game in **overall last place in the standings**, they gain an **extra +1 point**.

- The shell is **consumed** after that game (used once, then gone).  
- **Important:** Intentional throwing to gain a Safety Shell **voids that shell and any associated points.**
""")

# 8. Season Format
st.header("8. Season Format")

st.markdown("""
- The championship is played over **10 total games**.  
- After Game 10, each player **drops their two lowest-scoring games**.  
- Final standings are based on each player’s **best 8 game totals**.
""")

# 9. Tie-Break Order
st.header("9. Tie-Break Order")

st.markdown("""
If players are tied on total points after drops, resolve ties in this order:

1. **Most 1st-place finishes**  
2. **Most Bonus Stars** over the full season  
3. **Most minigame wins** over the full season  
4. **Higher head-to-head placements**  
5. **10-turn sudden-death playoff game**  
""")

# 10. Sportsmanship
st.header("10. Sportsmanship")

st.markdown("""
- **Intentional throwing** of games to gain a Safety Shell **voids that shell** and any points from it.  
- All ties award **full listed points** to each tied player.  
- **No half-points** are ever awarded in this ruleset.
""")

st.markdown("---")
st.caption("These rules are the single source of truth for scoring, bonuses, handicaps, and tie-breaks in the 2025 Mario Party Championship.")
