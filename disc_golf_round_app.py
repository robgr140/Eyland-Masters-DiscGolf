
import streamlit as st
import pandas as pd
import uuid

st.set_page_config(page_title="Disc Golf Match Tracker", layout="wide")

st.title("Disc Golf Match Tracker")

# Session state initialization
if "rounds" not in st.session_state:
    st.session_state.rounds = []

if "matches" not in st.session_state:
    st.session_state.matches = []

if "scorecards" not in st.session_state:
    st.session_state.scorecards = []

if "bonus" not in st.session_state:
    st.session_state.bonus = []

# Navigation
tabs = st.tabs(["🆕 Initialize Round", "🎯 Play Round", "📊 Dashboard"])

# ------------------ Initialize Round ------------------
with tabs[0]:
    st.header("🆕 Initialize New Round")

    with st.form("round_form"):
        day = st.selectbox("Day", ["Day 1", "Day 2", "Day 3", "Day 4"])
        round_number = st.number_input("Round Number", min_value=1, step=1)
        course = st.text_input("Course")
        players = st.text_area("Enter all player names, one per line").splitlines()
        challenger = st.selectbox("Select Challenger", players if players else [""])
        hunter = st.selectbox("Select Hunter (optional)", [""] + players if players else [""])
        submitted = st.form_submit_button("Create Round")

        if submitted:
            round_id = f"D{day[-1]}R{round_number}"
            st.session_state.rounds.append({
                "Round ID": round_id,
                "Day": day,
                "Round Number": round_number,
                "Course": course,
                "Challenger": challenger,
                "Hunter": hunter,
                "Players": players
            })
            st.success(f"Round {round_id} initialized.")

# ------------------ Play Round ------------------
with tabs[1]:
    st.header("🎯 Play Round")

    if not st.session_state.rounds:
        st.warning("Please initialize a round first.")
    else:
        round_ids = [r["Round ID"] for r in st.session_state.rounds]
        selected_round = st.selectbox("Select Round", round_ids)

        current_round = next(r for r in st.session_state.rounds if r["Round ID"] == selected_round)
        holes = list(range(1, 19))

        st.write("### Enter Hole Winners")
        match_results = {}
        for hole in holes:
            winner = st.selectbox(
                f"Hole {hole} Winner",
                ["", "Lag A", "Lag B", current_round["Challenger"], current_round["Hunter"]],
                key=f"hole_{hole}"
            )
            match_results[hole] = winner

        if st.button("Submit Match Results"):
            st.session_state.matches.append({
                "Round ID": selected_round,
                "Results": match_results
            })
            st.success(f"Match results submitted for {selected_round}.")

# ------------------ Dashboard ------------------
with tabs[2]:
    st.header("📊 Dashboard")

    if not st.session_state.rounds:
        st.info("No rounds to display.")
    else:
        for rnd in st.session_state.rounds:
            st.subheader(f"Round {rnd['Round ID']} - {rnd['Course']}")
            st.write("Challenger:", rnd["Challenger"])
            st.write("Hunter:", rnd["Hunter"])
            st.write("Players:", ", ".join(rnd["Players"]))

        st.divider()

        st.subheader("Match Results")
        if not st.session_state.matches:
            st.info("No match data available.")
        else:
            for match in st.session_state.matches:
                st.write(f"**{match['Round ID']}**")
                df = pd.DataFrame(list(match["Results"].items()), columns=["Hole", "Winner"])
                st.dataframe(df, use_container_width=True)
