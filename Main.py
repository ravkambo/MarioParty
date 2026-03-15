# Main.py
import os

import streamlit as st
from uuid import uuid4

from score_calculator import score_calculator_page
from scoreboard import scoreboard_page
from summary_storage import summary_storage_page
from consistency import compute_consistency_bonuses
from storage import load_data, save_data
from supabase_db import load_games


PLAYERS = ["Amber", "Mandeep", "Rav", "Simer"]


def init_state():
    if "session_id" not in st.session_state:
        try:
            league_id = st.secrets.get("LEAGUE_ID")
        except Exception:
            league_id = None
        st.session_state.session_id = (
            league_id
            or os.getenv("LEAGUE_ID")
            or "default_league"
        )

    if "games" not in st.session_state or "summaries" not in st.session_state:
        # Try loading from Supabase first, fall back to local JSON
        try:
            rows = load_games(st.session_state.session_id)
            games = [row["payload"] for row in rows]
            # Supabase returns newest-first; reverse to get chronological order
            games = list(reversed(games))
        except Exception:
            games, _ = load_data()

        _, summaries = load_data()
        st.session_state.games = games
        st.session_state.summaries = summaries

    if "next_game_id" not in st.session_state:
        # derive next_game_id from existing games
        games = st.session_state.games
        if isinstance(games, list) and games:
            max_id = max(g.get("game_id", 0) for g in games)
            st.session_state.next_game_id = max_id + 1
        else:
            st.session_state.next_game_id = 1



def main():
    st.set_page_config(page_title="Mario Party Championship", layout="wide")
    init_state()

    st.title("Mario Party Championship – 2025 Rules")

    page = st.sidebar.radio(
        "Navigation",
        ["Calculate Scores", "Scoreboard", "Summary Sheets"],
    )

    if page == "Calculate Scores":
        score_calculator_page(PLAYERS)
    elif page == "Scoreboard":
        scoreboard_page(PLAYERS)
    elif page ==  "Summary Sheets":
        summary_storage_page(PLAYERS)


if __name__ == "__main__":
    main()
