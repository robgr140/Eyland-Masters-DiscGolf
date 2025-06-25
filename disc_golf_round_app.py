from pathlib import Path
import pandas as pd
import streamlit as st
import os

# Set up paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STROKES_FILE = DATA_DIR / "strokes.csv"

# Page config
st.set_page_config(page_title="Upload Strokes", layout="centered")
st.title("eyland masters disc golf")
st.header("upload strokes from udisc")
st.subheader("upload udisc csv")

# File uploader
uploaded_file = st.file_uploader("Choose a UDisc CSV file", type="csv")

# Show content if a file is uploaded
if uploaded_file is not None:
    try:
        # Read file
        df = pd.read_csv(uploaded_file)

        # Basic validation (you can improve this)
        if "Player" not in df.columns or "Total" not in df.columns:
            st.error("This doesn't appear to be a valid UDisc export.")
        else:
            st.success("File uploaded and parsed successfully!")

            # Show preview
            st.dataframe(df.head())

            # Save to strokes.csv
            if STROKES_FILE.exists():
                existing = pd.read_csv(STROKES_FILE)
                combined = pd.concat([existing, df], ignore_index=True)
                combined.to_csv(STROKES_FILE, index=False)
                st.success("Data appended to existing strokes.csv.")
            else:
                df.to_csv(STROKES_FILE, index=False)
                st.success("strokes.csv created and saved.")
    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    if STROKES_FILE.exists():
        df_existing = pd.read_csv(STROKES_FILE)
        st.info("Showing previously uploaded stroke data:")
        st.dataframe(df_existing.head())
    else:
        st.info("No stroke data uploaded yet.")
