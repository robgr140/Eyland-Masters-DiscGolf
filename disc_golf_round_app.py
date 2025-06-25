import pandas as pd
import json
import os
import altair as alt
import streamlit as st
from datetime import datetime

# Filenames for persistence
SCORES_FILE = "all_scores.csv"
BONUS_FILE = "bonus_scores.json"

# Load or initialize scores
if os.path.exists(SCORES_FILE):
    all_scores = pd.read_csv(SCORES_FILE)
else:
    all_scores = pd.DataFrame(columns=["PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate", "Total"])

# Load or initialize bonus
if os.path.exists(BONUS_FILE):
    with open(BONUS_FILE, "r") as f:
        bonus_scores = json.load(f)
else:
    bonus_scores = {}

# Sidebar for file upload
st.sidebar.header("Upload UDisc CSV")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    required_cols = ["PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate", "Total"]
    if all(col in df.columns for col in required_cols):
        new_entries = df[required_cols]
        all_scores = pd.concat([all_scores, new_entries], ignore_index=True)
        all_scores.to_csv(SCORES_FILE, index=False)
        st.success("Scores successfully added.")
    else:
        st.error("CSV is missing required columns.")

# Sidebar bonus input
st.sidebar.header("Manual Bonus Points")
player_names = all_scores["PlayerName"].unique()
for player in player_names:
    bonus = st.sidebar.number_input(f"{player}", min_value=0.0, value=float(bonus_scores.get(player, 0)), step=0.5)
    bonus_scores[player] = bonus

# Save updated bonus scores
with open(BONUS_FILE, "w") as f:
    json.dump(bonus_scores, f)

# Dashboard
if not all_scores.empty:
    all_scores["Total"] = pd.to_numeric(all_scores["Total"], errors="coerce")
    score_summary = all_scores.groupby("PlayerName")["Total"].sum().reset_index(name="TotalStrokes")
    score_summary["Bonus"] = score_summary["PlayerName"].map(bonus_scores).fillna(0)
    score_summary["AdjustedScore"] = score_summary["TotalStrokes"] - score_summary["Bonus"]

    st.title("Discgolf Leaderboard")

    st.subheader("Leaderboard Table")
    st.dataframe(score_summary.sort_values("AdjustedScore"))

    st.subheader("Adjusted Score per Player")
    bar = alt.Chart(score_summary).mark_bar().encode(
        x=alt.X("PlayerName", sort="-y"),
        y="AdjustedScore",
        color=alt.Color("CourseName:N", legend=None),
        tooltip=["PlayerName", "TotalStrokes", "Bonus", "AdjustedScore"]
    ).properties(width=700, height=400)

    st.altair_chart(bar)

else:
    st.info("Upload at least one round to see dashboard.")
