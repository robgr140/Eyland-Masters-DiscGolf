import streamlit as st
import pandas as pd
import os
import json
import altair as alt

# --- File setup ---
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

STROKE_FILE = os.path.join(DATA_FOLDER, "udisc_scores.csv")
BONUS_FILE = os.path.join(DATA_FOLDER, "bonus_scores.json")

# --- Load or initialize bonus scores ---
if os.path.exists(BONUS_FILE):
    with open(BONUS_FILE, "r") as f:
        bonus_scores = json.load(f)
else:
    bonus_scores = {}

# --- Title ---
st.title("Disc Golf Dashboard")

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload UDisc CSV export", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.to_csv(STROKE_FILE, index=False)
    st.success("CSV uploaded successfully.")

# --- Load strokes ---
if os.path.exists(STROKE_FILE):
    scores_df = pd.read_csv(STROKE_FILE)

    # Ensure required columns
    required = ["PlayerName", "CourseName", "Total"]
    if all(col in scores_df.columns for col in required):
        scores_df["PlayerName"] = scores_df["PlayerName"].astype(str).str.strip()

        # --- Bonus input ---
        st.subheader("Bonus (manual input)")
        for player in scores_df["PlayerName"].unique():
            previous = bonus_scores.get(player, 0)
            bonus_scores[player] = st.number_input(f"{player} bonus", value=float(previous), step=0.5)

        # Save bonus
        with open(BONUS_FILE, "w") as f:
            json.dump(bonus_scores, f)

        # --- Combine and compute ---
        scores_df["Bonus"] = scores_df["PlayerName"].map(bonus_scores)
        scores_df["Adjusted Score"] = scores_df["Total"] - scores_df["Bonus"]

        # --- Show dashboard table ---
        st.subheader("Leaderboard")
        st.dataframe(scores_df[["PlayerName", "CourseName", "Total", "Bonus", "Adjusted Score"]])

        # --- Plot chart ---
        st.subheader("Adjusted Scores")
        chart = alt.Chart(scores_df).mark_bar().encode(
            x=alt.X("PlayerName:N", sort="-y"),
            y="Adjusted Score:Q",
            color="CourseName:N",
            tooltip=["PlayerName", "CourseName", "Total", "Bonus", "Adjusted Score"]
        ).properties(width=700)
        st.altair_chart(chart, use_container_width=True)

    else:
        st.error("CSV missing required columns: PlayerName, CourseName, Total.")
else:
    st.info("Please upload a UDisc CSV to begin.")
