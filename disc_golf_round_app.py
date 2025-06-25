import streamlit as st
import pandas as pd
import uuid

st.set_page_config(page_title="disc golf app", layout="wide")

# --- SESSION STATE ---
if "rounds" not in st.session_state:
    st.session_state.rounds = []

if "results" not in st.session_state:
    st.session_state.results = []

if "stroke_data" not in st.session_state:
    st.session_state.stroke_data = pd.DataFrame()

# --- ROUND INITIALIZATION ---
st.title("eyland disc golf")

tab1, tab2, tab3 = st.tabs(["initialize round", "play round", "dashboard"])

with tab1:
    st.subheader("initialize round")
    with st.form("round_init_form"):
        day = st.selectbox("day", ["day 1", "day 2", "day 3", "day 4"])
        round_number = st.number_input("round number", min_value=1, max_value=5, step=1)
        course = st.text_input("course name")
        players = st.text_area("players (comma separated)")
        include_challenger = st.checkbox("include challenger/hunter", value=True)
        challenger = hunter = None
        if include_challenger:
            challenger = st.text_input("challenger name")
            hunter = st.text_input("hunter name (optional)")
        uploaded_file = st.file_uploader("upload udisc csv", type="csv")
        submitted = st.form_submit_button("create round")
        if submitted:
            round_id = f"{day.replace(' ', '')}R{round_number}"
            player_list = [p.strip() for p in players.split(",") if p.strip()]
            st.session_state.rounds.append({
                "round_id": round_id,
                "day": day,
                "round_number": round_number,
                "course": course,
                "players": player_list,
                "challenger": challenger,
                "hunter": hunter
            })
            if uploaded_file:
                try:
                    stroke_df = pd.read_csv(uploaded_file)
                    stroke_df["round_id"] = round_id
                    st.session_state.stroke_data = pd.concat([st.session_state.stroke_data, stroke_df], ignore_index=True)
                    st.success("stroke data uploaded")
                except Exception as e:
                    st.error(f"could not process csv: {e}")
            st.success(f"round {round_id} created")

# --- PLAY ROUND / ENTER RESULTS ---
with tab2:
    st.subheader("play round")
    if not st.session_state.rounds:
        st.info("initialize at least one round first")
    else:
        selected_round = st.selectbox("select round", [r["round_id"] for r in st.session_state.rounds])
        current_round = next(r for r in st.session_state.rounds if r["round_id"] == selected_round)
        holes = list(range(1, 19))
        st.markdown("### enter hole results")
        for hole in holes:
            with st.expander(f"hole {hole}"):
                winner = st.radio(
                    f"who won hole {hole}?",
                    options=["lag a", "lag b"] +
                            ([current_round["challenger"]] if current_round["challenger"] else []) +
                            ([current_round["hunter"]] if current_round["hunter"] else []),
                    key=f"{selected_round}_hole_{hole}"
                )
                if st.button(f"save result hole {hole}", key=f"save_{selected_round}_{hole}"):
                    st.session_state.results.append({
                        "round_id": selected_round,
                        "hole": hole,
                        "winner": winner
                    })
                    st.success(f"saved hole {hole} result")

# --- DASHBOARD ---
with tab3:
    st.subheader("dashboard")
    if st.session_state.stroke_data.empty:
        st.warning("no stroke data uploaded")
    else:
        st.dataframe(st.session_state.stroke_data)

    results_df = pd.DataFrame(st.session_state.results)
    if not results_df.empty:
        bonus_df = results_df.copy()
        bonus_df["bonus"] = bonus_df["winner"].apply(lambda x: -1.5 if x.lower() == "hunter" else (-1 if x.lower() not in ["lag a", "lag b"] else -0.5))
        stroke_df = st.session_state.stroke_data
        if "Name" in stroke_df.columns and "Total" in stroke_df.columns:
            summary = stroke_df.groupby("Name")["Total"].sum().reset_index()
            summary.columns = ["name", "strokes"]
            bonus_summary = bonus_df.groupby("winner")["bonus"].sum().reset_index()
            bonus_summary.columns = ["name", "bonus"]
            merged = pd.merge(summary, bonus_summary, on="name", how="outer").fillna(0)
            merged["adjusted_score"] = merged["strokes"] + merged["bonus"]
            st.markdown("### current standings")
            st.dataframe(merged.sort_values("adjusted_score"))
        else:
            st.error("CSV must contain columns 'Name' and 'Total'")
