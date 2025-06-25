import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Discgolf Dashboard", layout="wide")

st.title("Discgolf Round Tracker")

uploaded_files = st.file_uploader("Upload UDisc CSV files", type=["csv"], accept_multiple_files=True)

all_scores = pd.DataFrame()

if uploaded_files:
    for file in uploaded_files:
        df = pd.read_csv(file)

        required_columns = {"PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate", "Total"}
        if not required_columns.issubset(df.columns):
            st.error(f"File {file.name} is missing required columns.")
            continue

        df = df[list(required_columns)]
        df["SourceFile"] = file.name
        all_scores = pd.concat([all_scores, df], ignore_index=True)

if not all_scores.empty:
    st.subheader("Aggregated Scores")

    all_scores["Total"] = pd.to_numeric(all_scores["Total"], errors="coerce")

    summary = all_scores.groupby("PlayerName").agg(
        TotalStrokes=("Total", "sum"),
        CoursesPlayed=("CourseName", "nunique")
    ).reset_index()

    if "bonus_scores" not in st.session_state:
        st.session_state.bonus_scores = {}

    st.sidebar.subheader("Enter bonus strokes (subtracts from total)")
    for player in summary["PlayerName"]:
        bonus = st.sidebar.number_input(f"{player}", min_value=0, max_value=100, value=0, step=1, key=f"bonus_{player}")
        st.session_state.bonus_scores[player] = bonus

    summary["Bonus"] = summary["PlayerName"].map(st.session_state.bonus_scores)
    summary["AdjustedScore"] = summary["TotalStrokes"] - summary["Bonus"]

    st.dataframe(summary)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(summary["PlayerName"], summary["AdjustedScore"], color="mediumseagreen")
    ax.set_title("Adjusted Score per Player (Lower is Better)")
    ax.set_ylabel("Adjusted Strokes")
    ax.set_xlabel("Player")

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval - 2, round(yval, 1), ha="center", va="bottom", color="black")

    st.pyplot(fig)

else:
    st.info("Upload at least one valid UDisc CSV file to begin.")
