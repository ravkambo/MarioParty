import os

import streamlit as st
from supabase import create_client

def _get_secret(name: str):
    if name in st.secrets:
        return st.secrets[name]
    return os.getenv(name)


@st.cache_resource
def get_supabase():
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError(
            "Supabase credentials missing. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY)."
        )
    return create_client(url, key)

def save_game(session_id: str, game_id: str, payload: dict):
    sb = get_supabase()
    res = sb.table("mario_scores").insert({
        "session_id": session_id,
        "game_id": game_id,
        "payload": payload
    }).execute()
    if res.error:
        raise RuntimeError(f"Supabase insert failed: {res.error}")
    return res

def load_games(session_id: str, limit: int = 50):
    sb = get_supabase()
    res = (
        sb.table("mario_scores")
        .select("id, game_id, payload")
        .eq("session_id", session_id)
        .order("id", desc=True)
        .limit(limit)
        .execute()
    )
    if res.error:
        raise RuntimeError(f"Supabase load failed: {res.error}")
    return res.data
