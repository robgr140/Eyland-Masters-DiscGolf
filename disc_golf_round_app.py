
import streamlit as st
import pandas as pd
import os

# Initialize storage
PLAYER_FILE = "player_list.csv"
STROKES_FILE = "strokes.csv"
ROUNDS_FILE = "rounds.csv"
SKINS_FILE = "skins.csv"

def load_or_create_csv(filename, columns):
    if not os.path.exists(filename):
        pd.DataFrame(columns=columns).to_csv(filename, index=False)
    return pd.read_csv(filename)

def save_df(df, filename):
    df.to_csv(filename, index=False)

# Load persistent data
players_df = load_or_create_csv(PLAYER_FILE, ["player"])
strokes_df = load_or_create_csv(STROKES_FILE, ["round_id", "player", "total_strokes"])
rounds_df = load_or_create_csv(ROUNDS_FILE, ["round_id", "day", "round_number", "course", "challenger", "hunter"])
skins_df = load_or_create_csv(SKINS_FILE, ["round_id", "hole", "winner"])

st.title("eyland masters disc golf")

menu = st.sidebar.radio("navigate", ["upload strokes", "initialize round", "record skins", "dashboard"])

if menu == "upload strokes":
    st.header("upload strokes from udisc")
    uploaded_file = st.file_uploader("upload udisc csv", type=["csv"])
    if uploaded_file is not None:
        udisc_df = pd.read_csv(uploaded_file)
        if "Player" in udisc_df.columns and "Total" in udisc_df.columns:
            # Show preview
            st.dataframe(udisc_df)
            round_id = st.text_input("enter round ID (e.g., D1R1)")
            if round_id:
                # Update player list
                for name in udisc_df["Player"]:
                    if name not in players_df["player"].values:
                        players_df.loc[len(players_df)] = [name]
                save_df(players_df, PLAYER_FILE)

                # Add strokes
                for _, row in udisc_df.iterrows():
                    strokes_df = strokes_df[~((strokes_df["round_id"] == round_id) & (strokes_df["player"] == row["Player"]))]
                    strokes_df.loc[len(strokes_df)] = [round_id, row["Player"], int(row["Total"])]
                save_df(strokes_df, STROKES_FILE)
                st.success("strokes uploaded")

elif menu == "initialize round":
    st.header("initialize new round")
    round_id = st.text_input("round ID (e.g., D1R2)")
    day = st.text_input("day (e.g., Day 1)")
    round_number = st.number_input("round number", min_value=1, step=1)
    course = st.text_input("course name")
    challenger = st.selectbox("select challenger", players_df["player"]) if not players_df.empty else ""
    hunter = st.selectbox("select hunter (if any)", [""] + list(players_df["player"])) if not players_df.empty else ""

    if st.button("save round"):
        if round_id:
            rounds_df = rounds_df[rounds_df["round_id"] != round_id]
            rounds_df.loc[len(rounds_df)] = [round_id, day, round_number, course, challenger, hunter]
            save_df(rounds_df, ROUNDS_FILE)
            st.success(f"round {round_id} saved")

elif menu == "record skins":
    st.header("record skins results")
    round_id = st.selectbox("select round", rounds_df["round_id"]) if not rounds_df.empty else ""
    hole = st.number_input("hole number", min_value=1, max_value=18, step=1)
    winner = st.selectbox("who won the hole?", ["", "lag a", "lag b", "challenger", "hunter"])
    if st.button("record hole result"):
        if round_id and winner:
            skins_df = skins_df[~((skins_df["round_id"] == round_id) & (skins_df["hole"] == hole))]
            skins_df.loc[len(skins_df)] = [round_id, hole, winner]
            save_df(skins_df, SKINS_FILE)
            st.success("hole result recorded")

elif menu == "dashboard":
    st.header("tournament dashboard")

    if strokes_df.empty and skins_df.empty:
        st.info("no data yet")
    else:
        # Bonus calculation
        bonus_counts = skins_df["winner"].value_counts().to_dict()
        bonus_data = []
        for player in players_df["player"]:
            bonus = 0
            bonus += bonus_counts.get("challenger", 0) if rounds_df["challenger"].eq(player).any() else 0
            bonus += 1.5 * bonus_counts.get("hunter", 0) if rounds_df["hunter"].eq(player).any() else 0
            bonus_data.append((player, bonus))
        bonus_df = pd.DataFrame(bonus_data, columns=["player", "bonus"])

        merged = strokes_df.merge(bonus_df, on="player", how="left").fillna(0)
        merged["adjusted_score"] = merged["total_strokes"] - merged["bonus"]
        leaderboard = merged.groupby("player", as_index=False).agg({
            "total_strokes": "sum",
            "bonus": "sum",
            "adjusted_score": "sum"
        }).sort_values("adjusted_score")

        st.dataframe(leaderboard)

        st.bar_chart(leaderboard.set_index("player")[["adjusted_score"]])
