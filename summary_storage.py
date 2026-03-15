# summary_storage.py
import streamlit as st
import pandas as pd


def summary_storage_page(players):
    st.header("Summary Sheets")

    summaries = st.session_state.summaries

    # Save current standings as snapshot
    st.subheader("Save current standings as a summary")

    label = st.text_input("Summary label (e.g., 'After Night 1')")

    if st.button("📌 Save summary from current standings"):
        if "current_standings" not in st.session_state:
            st.warning("Go to the Scoreboard page first to generate standings.")
        elif not label.strip():
            st.warning("Please enter a label.")
        else:
            df = st.session_state.current_standings
            snapshot = {
                "label": label.strip(),
                "standings": df.to_dict(orient="records"),
            }
            summaries.append(snapshot)
            st.session_state.summaries = summaries
            st.success(f"Saved summary: {label.strip()}")

    st.markdown("---")

    # List existing summaries
    st.subheader("Saved summaries")

    if not summaries:
        st.info("No summaries saved yet.")
        return

    labels = [s["label"] for s in summaries]
    chosen_label = st.selectbox("Choose a summary to view", labels)

    selected = next(s for s in summaries if s["label"] == chosen_label)
    st.markdown(f"### {selected['label']}")

    df = pd.DataFrame(selected["standings"])
    st.table(df)
