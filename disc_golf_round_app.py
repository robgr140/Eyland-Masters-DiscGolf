import streamlit as st
import pandas as pd
import os

# Constants for file storage
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

STROKES_FILE = os.path.join(DATA_DIR, "strokes.csv")
ROUNDS_FILE = os.path.join(DATA_DIR, "rounds.csv")
SKINS_FILE = os.path.join(DATA_DIR, "skins.csv")

# Load or create empty DataFrames
def load_csv(path, columns):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=columns)

strokes_df = load_csv(STROKES_FILE, ["player", "hole", "score", "round_id"])
rounds_df = load_csv(ROUNDS_FILE, ["round_id", "day", "round_number", "course", "challenger", "hunter"])
skins_df = load_csv(SKINS_FILE, ["round_id", "hole", "winner"])

# Sidebar nav
page = st.sidebar.selectbox("view", ["upload strokes", "initialize round", "record skins", "dashboard"])

import csv

# Upload strokes
if page == "upload strokes":
    st.header("upload udisc strokes")
    uploaded_file = st.file_uploader("upload udisc csv", type="csv")
    
    if uploaded_file:
        try:
            # Try to auto-detect delimiter
            sample = uploaded_file.read(2048).decode("utf-8")
            uploaded_file.seek(0)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
            
            # Load CSV with detected delimiter
            df = pd.read_csv(uploaded_file, delimiter=delimiter)
            
            # Show columns for debugging
            st.write("detected columns:", list(df.columns))
            
            expected_cols = ["PlayerName", "CourseName", "StartDate"] + [f"Hole{i}" for i in range(1, 19)]
            missing = [col for col in expected_cols if col not in df.columns]
            
            if missing:
                st.error(f"missing required columns: {missing}")
            else:
                long_format_rows = []
                for _, row in df.iterrows():
                    player = row["PlayerName"]
                    course = row["CourseName"]
                    date = pd.to_datetime(row["StartDate"]).date().isoformat()
                    round_id = f"{course}-{date}".replace(" ", "")
                    for i in range(1, 19):
                        score = row[f"Hole{i}"]
                        if pd.notna(score):
                            long_format_rows.append({
                                "player": player,
                                "hole": i,
                                "score": int(score),
                                "round_id": round_id
                            })

                new_data = pd.DataFrame(long_format_rows)
                strokes_df = pd.concat([strokes_df, new_data], ignore_index=True)
                strokes_df.to_csv(STROKES_FILE, index=False)
                st.success(f"{len(new_data)} strokes imported")
        except Exception as e:
            st.error(f"upload failed: {e}")


# Initialize round
elif page == "initialize round":
    st.header("initialize round")
    with st.form("round_form"):
        round_id = st.text_input("round id")
        day = st.text_input("day")
        round_number = st.number_input("round number", min_value=1)
        course = st.text_input("course")
        challenger = st.text_input("challenger")
        hunter = st.text_input("hunter (optional)", value="")
        submit = st.form_submit_button("save")
        if submit:
            new_row = pd.DataFrame([{
                "round_id": round_id,
                "day": day,
                "round_number": round_number,
                "course": course,
                "challenger": challenger,
                "hunter": hunter
            }])
            rounds_df = pd.concat([rounds_df, new_row], ignore_index=True)
            rounds_df.to_csv(ROUNDS_FILE, index=False)
            st.success("round saved")

# Record skins
elif page == "record skins":
    st.header("record skins")
    if rounds_df.empty:
        st.warning("no rounds found")
    else:
        with st.form("skin_form"):
            round_id = st.selectbox("round id", rounds_df["round_id"].unique())
            hole = st.number_input("hole", min_value=1, max_value=18)
            winner = st.selectbox("winner", ["Lag A", "Lag B", "Challenger", "Hunter"])
            submit_skin = st.form_submit_button("save")
            if submit_skin:
                new_row = pd.DataFrame([{
                    "round_id": round_id,
                    "hole": hole,
                    "winner": winner
                }])
                skins_df = pd.concat([skins_df, new_row], ignore_index=True)
                skins_df.to_csv(SKINS_FILE, index=False)
                st.success("saved")

# Dashboard
elif page == "dashboard":
    st.header("leaderboard")

    if strokes_df.empty:
        st.warning("no stroke data yet")
    else:
        bonus_counts = skins_df["winner"].value_counts().rename("bonus").reset_index()
        bonus_counts.columns = ["player", "bonus"]

        total_scores = strokes_df.groupby("player")["score"].sum().reset_index()
        total_scores = total_scores.merge(bonus_counts, on="player", how="left")
        total_scores["bonus"] = total_scores["bonus"].fillna(0)
        total_scores["adjusted"] = total_scores["score"] - total_scores["bonus"]

        st.subheader("score table")
        st.dataframe(total_scores.sort_values("adjusted"))

        st.subheader("chart")
        st.bar_chart(total_scores.set_index("player")[["score", "adjusted"]])
