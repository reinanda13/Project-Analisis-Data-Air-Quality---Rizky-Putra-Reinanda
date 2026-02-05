import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium

from branca.colormap import LinearColormap
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Air Quality Dashboard - Rizky Putra Reinanda",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
def load_data():
    df = pd.read_csv("dashboard/all_data.csv")
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    return df

df = load_data()

# Sidebar
with st.sidebar:
    st.sidebar.title("🔎 Filter Data")

    # Station
    stations = sorted(df["station"].unique())
    selected_station = st.sidebar.multiselect(
        "Station",
        stations,
        default=stations
    )

    # Tanggal
    date_range = st.sidebar.date_input(
        "Rentang Tanggal",
        value=[
            df["date"].min().date(),
            df["date"].max().date()
        ]
    )
    # Validasi rentang tanggal
    if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
        st.sidebar.error("Mohon pilih **rentang tanggal** yang valid.")
        st.stop()

    start_date, end_date = date_range

    # Jam
    hours = sorted(df["hour"].unique())
    selected_hour = st.sidebar.multiselect(
        "Jam",
        hours,
        default=hours
    )

    # Data Filter
    start_date, end_date = date_range
    filtered_df = df[
        (df["station"].isin(selected_station)) &
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date)) &
        (df["hour"].isin(selected_hour))
    ]

# Title
st.title("🌏 Air Quality Analysis Dashboard")
st.markdown(
    f"""
    Analisis kualitas udara berdasarkan **PM2.5 & PM10**  
    📅 Periode: **{start_date} s.d. {end_date}**  
    📋 Total data: **{len(filtered_df):,} baris**
    """
)

# Summary Data
st.subheader("📊 Ringkasan Kualitas Udara")

col1, col2, col3, col4 = st.columns(4)

avg_pm25 = filtered_df["PM2.5"].mean()
avg_pm10 = filtered_df["PM10"].mean()

peak_hour = filtered_df.groupby("hour")["PM2.5"].mean().idxmax()

worst_station = filtered_df.groupby("station")["PM2.5"].mean().idxmax()

with col1:
    st.metric(
        label="Rata-rata PM2.5 (µg/m³)",
        value=f"{avg_pm25:.2f}"
    )

with col2:
    st.metric(
        label="Rata-rata PM10 (µg/m³)",
        value=f"{avg_pm10:.2f}"
    )

with col3:
    st.metric(
        label="Jam Terpolusi",
        value=f"{peak_hour}.00"
    )

with col4:
    st.metric(
        label="Station Terburuk",
        value=worst_station
    )

# ============================================================
# TITLE
# ============================================================
st.title("🌏 Air Quality Analysis Dashboard")

st.markdown(
    f"""
    Dashboard ini dibuat untuk menjawab **2 pertanyaan analisis data** berikut:

    1. **Bagaimana tren tingkat polusi PM2.5 dari tahun ke tahun di berbagai stasiun?**  
    2. **Jam berapakah rata-rata pencemaran udara meningkat secara global berdasarkan PM2.5?**

    📅 Periode Data: **{start_date} s.d. {end_date}**  
    📊 Total Observasi: **{len(filtered_df):,} baris**
    """
)

# ============================================================
# PERTANYAAN 1
# Tren PM2.5 dari Tahun ke Tahun di Berbagai Stasiun
# ============================================================
st.subheader("📈 Pertanyaan 1: Tren PM2.5 dari Tahun ke Tahun di Berbagai Stasiun")

yearly_pm25 = (
    filtered_df
    .groupby(["year", "station"])["PM2.5"]
    .mean()
    .reset_index()
)

fig1, ax1 = plt.subplots(figsize=(18, 7))

sns.lineplot(
    data=yearly_pm25,
    x="year",
    y="PM2.5",
    hue="station",
    marker="o",
    ax=ax1
)

ax1.set_title("Tren Rata-rata PM2.5 per Tahun di Setiap Stasiun", fontsize=16)
ax1.set_xlabel("Tahun")
ax1.set_ylabel("Rata-rata PM2.5 (µg/m³)")
ax1.grid(True, linestyle="--", alpha=0.5)

st.pyplot(fig1)

# ============================================================
# PERTANYAAN 2
# Jam Peningkatan Rata-rata PM2.5 Global
# ============================================================
st.subheader("⏰ Pertanyaan 2: Jam Peningkatan Rata-rata PM2.5 Global")

hourly_pm25 = (
    filtered_df
    .groupby("hour")["PM2.5"]
    .mean()
    .reset_index()
)

peak_hour = hourly_pm25.loc[hourly_pm25["PM2.5"].idxmax(), "hour"]

fig2, ax2 = plt.subplots(figsize=(18, 6))

ax2.plot(
    hourly_pm25["hour"],
    hourly_pm25["PM2.5"],
    marker="o",
    linewidth=2
)

ax2.axvline(
    peak_hour,
    linestyle="--",
    alpha=0.7,
    label=f"Puncak Polusi: {peak_hour}.00"
)

ax2.set_title("Rata-rata Konsentrasi PM2.5 Berdasarkan Jam", fontsize=16)
ax2.set_xlabel("Jam")
ax2.set_ylabel("Rata-rata PM2.5 (µg/m³)")
ax2.set_xticks(range(0, 24))
ax2.legend()
ax2.grid(True, linestyle="--", alpha=0.5)

st.pyplot(fig2)
