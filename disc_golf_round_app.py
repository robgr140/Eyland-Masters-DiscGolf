import streamlit as st
import pandas as pd
import uuid

st.set_page_config(page_title="Disc Golf Tracker", layout="wide")

st.title("Disc Golf Tracker")

# Session state initialization
if 'rounds' not in st.session_state:
    st.session_state.rounds = []
if 'results' not in st.session_state:
    st.session_state.results = []
if 'strokes' not in st.session_state:
    st.session_state.strokes = pd.DataFrame()

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["initialize round", "play round", "dashboard"])

### PAGE 1: initialize round ###
if page == "initialize round":
    st.header("Initialize Round")
    
    with st.form("round_form"):
        day = st.selectbox("Select day", ["Day 1", "Day 2", "Day 3", "Day 4"])
        round_number = st.number_input("Round number", min_value=1, max_value=10, step=1)
        course = st.text_input("Course")
        challenger = st.text_input("Challenger")
        hunter = st.text_input("Hunter (if any, optional)", value="")

        team_a = st.text_input("Team A (comma-separated)")
        team_b = st.text_input("Team B (comma-separated)")

        submitted = st.form_submit_button("Save round")

        if submitted:
            round_id = f"D{day[-1]}R{round_number}"
            st.session_state.rounds.append({
                "round_id": round_id,
                "day": day,
                "round_number": round_number,
                "course": course,
                "challenger": challenger,
                "hunter": hunter,
                "team_a": [name.strip() for name in team_a.split(",")],
                "team_b": [name.strip() for name in team_b.split(",")]
            })
            st.success(f"Round {round_id} saved.")

    st.subheader("Current rounds")
    if st.session_state.rounds:
        st.dataframe(pd.DataFrame(st.session_state.rounds))

    st.subheader("Upload UDisc stroke CSV")
    uploaded_file = st.file_uploader("Upload UDisc strokes CSV", type="csv")
    if uploaded_file:
        st.session_state.strokes = pd.read_csv(uploaded_file)
        st.success("Stroke data uploaded.")

### PAGE 2: play round ###
elif page == "play round":
    st.header("Play Round: Record Skins Results")

    if not st.session_state.rounds:
        st.warning("Please initialize a round first.")
    else:
        selected_round = st.selectbox("Select round", [r["round_id"] for r in st.session_state.rounds])
        round_info = next(r for r in st.session_state.rounds if r["round_id"] == selected_round)

        with st.form("skins_form"):
            st.markdown("### Enter skins results (per hole winner)")
            num_holes = st.number_input("Number of holes", min_value=1, max_value=24, step=1)
            results = []
            for hole in range(1, num_holes + 1):
                winner = st.selectbox(
                    f"Hole {hole} winner",
                    ["", "Team A", "Team B", "Challenger", "Hunter"],
                    key=f"hole_{hole}_winner"
                )
                results.append({"round_id": selected_round, "hole": hole, "winner": winner})

            save = st.form_submit_button("Save results")
            if save:
                st.session_state.results.extend(results)
                st.success("Skins results saved.")

        st.subheader("Current skins results")
        st.dataframe(pd.DataFrame(st.session_state.results))

### PAGE 3: dashboard ###
elif page == "dashboard":
    st.header("Dashboard")

    if st.session_state.strokes.empty:
        st.warning("No stroke data uploaded yet.")
    else:
        bonus_df = pd.DataFrame(st.session_state.results)

        # Count bonuses
        bonus_df = bonus_df[bonus_df["winner"] != ""]
        bonus_points = bonus_df.groupby("winner").size().reset_index(name="bonus")

        # Combine with strokes
        strokes_df = st.session_state.strokes.copy()
        strokes_df.columns = [c.lower() for c in strokes_df.columns]

        if "player" not in strokes_df.columns or "strokes" not in strokes_df.columns:
            st.error("CSV must contain columns: 'player', 'strokes'")
        else:
            strokes_df = strokes_df.merge(bonus_points, how="left", left_on="player", right_on="winner")
            strokes_df["bonus"] = strokes_df["bonus"].fillna(0)
            strokes_df["adjusted_score"] = strokes_df["strokes"] - strokes_df["bonus"]

            st.subheader("Leaderboard")
            st.dataframe(strokes_df[["player", "strokes", "bonus", "adjusted_score"]].sort_values("adjusted_score"))
