import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase():
    url = st.secrets["https://irvkfwzzzuijtvfngzjc.supabase.co"]
    key = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlydmtmd3p6enVpanR2Zm5nempjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTExNDI3OSwiZXhwIjoyMDg0NjkwMjc5fQ.1HptMEhjZg3QCliHOOxe_fGrbWdhRIk6JP1u2ezSxXY"]
    return create_client(url, key)

def save_game(session_id: str, game_id: str, payload: dict):
    sb = get_supabase()
    res = sb.table("mario_scores").insert({
        "session_id": session_id,
        "game_id": game_id,
        "payload": payload
    }).execute()
    return res

def load_games(session_id: str, limit: int = 50):
    sb = get_supabase()
    res = (
        sb.table("mario_scores")
        .select("id, created_at, game_id, payload")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data
