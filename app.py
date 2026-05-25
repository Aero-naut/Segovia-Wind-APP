import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Segovia Wind System", layout="wide")

# -------------------------
# LOCATION (Segovia fixed)
# -------------------------
LAT = 40.949
LON = -4.119

# -------------------------
# DATA FETCH (Open-Meteo)
# -------------------------
def fetch_wind(date):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&hourly=windspeed_10m,winddirection_10m"
        "&forecast_days=3"
    )

    data = requests.get(url).json()

    df = pd.DataFrame({
        "time": data["hourly"]["time"],
        "wind": data["hourly"]["windspeed_10m"],
        "dir": data["hourly"]["winddirection_10m"],
    })

    df["time"] = pd.to_datetime(df["time"])
    df = df[df["time"].dt.date == pd.to_datetime(date).date()]

    return df

# -------------------------
# LLJ / RISK ENGINE
# -------------------------
def risk_score(df):
    if df.empty:
        return 0, "No data"

    early = df.iloc[:6]

    mean = early["wind"].mean()
    maxv = early["wind"].max()
    std = early["wind"].std()

    score = 0

    # wind level
    if mean > 20:
        score += 40
    elif mean > 12:
        score += 20

    # gust factor
    if maxv - mean > 8:
        score += 25

    # variability (shear proxy)
    if std > 5:
        score += 20

    score = min(100, score)

    if score < 30:
        label = "🟢 LOW RISK"
    elif score < 60:
        label = "🟡 MODERATE RISK"
    else:
        label = "🔴 HIGH RISK"

    return score, label

# -------------------------
# UI
# -------------------------
st.title("🎈 Segovia Early Wind & LLJ Risk System")

date = st.date_input("Select date", datetime.now())

if st.button("Run Analysis"):

    df = fetch_wind(date)

    st.subheader("📊 Wind Profile (10m)")

    st.line_chart(df.set_index("time")[["wind"]])

    score, label = risk_score(df)

    st.subheader("⚠️ Risk Assessment")
    st.write(f"### {label} ({score}/100)")

    st.subheader("📋 Raw Data")
    st.dataframe(df)

    st.subheader("🧠 Interpretation")
    st.info(
        "This is a prototype LLJ-risk model based on surface wind variability. "
        "Future versions will include vertical wind (300m / 850hPa) and Sierra-channeling index."
    )
