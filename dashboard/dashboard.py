import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import folium

from branca.colormap import LinearColormap
from streamlit_folium import st_folium

# Konfigurasi Halaman
st.set_page_config(
    page_title="Air Quality Dashboard - Rizky Putra Reinanda",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Fungsi Load Data (Optimasi Path)
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "all_data.csv")
    
    if not os.path.exists(file_path):
        st.error(f"File tidak ditemukan di: {file_path}")
        st.stop()
        
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    return df

df = load_data()

# 2. Sidebar Filter
with st.sidebar:
    st.title("🔎 Filter Panel")
    
    stations = sorted(df["station"].unique())
    selected_station = st.multiselect("Pilih Stasiun", stations, default=stations)

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input("Rentang Waktu", value=[min_date, max_date], min_value=min_date, max_value=max_date)

    hours = sorted(df["hour"].unique())
    selected_hour = st.multiselect("Pilih Jam Operasional", hours, default=hours)

# Proteksi jika filter kosong
if not selected_station or not isinstance(date_range, (list, tuple)) or len(date_range) < 2:
    st.warning("Silakan pilih stasiun dan rentang tanggal pada sidebar.")
    st.stop()

start_date, end_date = date_range

# Aplikasi Filter Data
mask = (
    (df["station"].isin(selected_station)) &
    (df["date"] >= pd.to_datetime(start_date)) &
    (df["date"] <= pd.to_datetime(end_date)) &
    (df["hour"].isin(selected_hour))
)
filtered_df = df.loc[mask]

# 3. Header Dashboard
st.title("🌏 Air Quality Analysis Dashboard")
st.markdown(f"Analisis berdasarkan pertanyaan bisnis yang ditentukan: **Tren Tahunan** dan **temperatur**.")

# 4. Ringkasan Statistik (Metrics)
col1, col2, col3, col4 = st.columns(4)
if not filtered_df.empty:
    with col1:
        st.metric("Rata-rata PM2.5", f"{filtered_df['PM2.5'].mean():.2f} µg/m³")
    with col2:
        st.metric("Rata-rata PM10", f"{filtered_df['PM10'].mean():.2f} µg/m³")
    with col3:
        p_hour = filtered_df.groupby("hour")["PM2.5"].mean().idxmax()
        st.metric("Jam Puncak Polusi", f"{p_hour}.00")
    with col4:
        w_station = filtered_df.groupby("station")["PM2.5"].mean().idxmax()
        st.metric("Stasiun Terburuk", w_station)

st.divider()

# --- PERTANYAAN 1: TREN TAHUNAN ---
st.subheader("📈 1. Tren PM2.5 dari Tahun ke Tahun di Berbagai Stasiun")
yearly_df = filtered_df.groupby(["year", "station"])["PM2.5"].mean().reset_index()

fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.lineplot(data=yearly_df, x="year", y="PM2.5", hue="station", marker="o", ax=ax1)
ax1.set_title("Rata-rata Konsentrasi PM2.5 Tahunan", fontsize=14)
ax1.set_ylabel("PM2.5 (µg/m³)")
ax1.set_xlabel("Tahun")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig1)

with st.expander("Lihat Insight Tren Tahunan"):
    st.write("""
    Berdasarkan visualisasi, konsentrasi PM2.5 menunjukkan pola fluktuatif dengan penurunan seragam pada 2016, 
    namun naik signifikan di hampir semua stasiun pada 2017. Stasiun **Wanshouxigong** mencatat tingkat tertinggi 
    secara konsisten, sementara **Dingling** relatif lebih rendah karena faktor lokasi wilayah pinggiran.
    """)

# --- PENGARUH TEMPERATUR ---
st.subheader("🌡️ Pengaruh Temperatur terhadap PM2.5 dan PM10 secara global")

df_temp = filtered_df.copy()
df_temp["temp_bin"] = pd.cut(df_temp["TEMP"], bins=10)
temp_pm = df_temp.groupby("temp_bin", observed=True)[["PM2.5", "PM10"]].median()

fig3, ax3 = plt.subplots(figsize=(12, 6))
ax3.plot(temp_pm.index.astype(str), temp_pm["PM2.5"], marker="o", label="PM2.5", color='blue')
ax3.plot(temp_pm.index.astype(str), temp_pm["PM10"], marker="o", label="PM10", color='orange')
ax3.set_xlabel("\nRentang Temperatur", fontsize=12)
ax3.set_ylabel("Konsentrasi Polutan (µg/m³)\n", fontsize=12)
plt.xticks(rotation=45)
ax3.legend()
ax3.grid(True, linestyle='--', alpha=0.6)
st.pyplot(fig3)

with st.expander("Lihat Insight Temperatur"):
    st.write("""
    Temperatur dingin hingga menengah berkorelasi dengan tingginya polutan PM2.5 dan PM10 secara global. 
    Pola harian menunjukkan peningkatan polusi pada jam-jam tertentu yang berkaitan dengan aktivitas manusia dan kondisi atmosfer.
    """)

# --- GEOSPASIAL ANALYSIS ---
st.divider()
st.subheader("🗺️ Peta Persebaran Rata-rata PM2.5 per Stasiun")

# Agregasi data untuk peta
station_pm25 = filtered_df.groupby("station")["PM2.5"].mean().reset_index()

station_coords = {
    "Aotizhongxin": (40.00, 116.41),
    "Changping": (40.20, 116.23),
    "Dingling": (40.30, 116.22),
    "Dongsi": (39.93, 116.42),
    "Guanyuan": (39.94, 116.36),
    "Gucheng": (39.93, 116.23),
    "Huairou": (40.36, 116.64),
    "Nongzhanguan": (39.97, 116.47),
    "Shunyi": (40.14, 116.72),
    "Tiantan": (39.87, 116.43),
    "Wanliu": (39.99, 116.32),
    "Wanshouxigong": (39.87, 116.37)
}

station_pm25["lat"] = station_pm25["station"].map(lambda x: station_coords[x][0])
station_pm25["lon"] = station_pm25["station"].map(lambda x: station_coords[x][1])

m = folium.Map(location=[39.9, 116.4], zoom_start=9)

# Colormap: Putih ke Merah ke Hitam
colormap = LinearColormap(
    colors=["#ffffff", "#ff0000", "#000000"],
    vmin=station_pm25["PM2.5"].min(),
    vmax=station_pm25["PM2.5"].max()
)
colormap.caption = "Indikator Rata-rata PM2.5"

for _, row in station_pm25.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=10,
        popup=f"Stasiun: {row['station']}<br>Rata-rata PM2.5: {row['PM2.5']:.2f} µg/m³",
        color=colormap(row["PM2.5"]),
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

colormap.add_to(m)
st_folium(m, width=1100, height=500)

# Menambahkan Insight Geospasial sesuai permintaan
with st.expander("Lihat Insight Peta Persebaran Rata-rata PM2.5 per Stasiun"):
    st.write("""
    **Insight Geospasial:**
    Pada peta di atas, gradien warna menunjukkan tingkat konsentrasi PM2.5; semakin gelap/hitam warna titik marker, 
    maka semakin tinggi tingkat pencemaran PM2.5 di stasiun tersebut. 
    
    Berdasarkan visualisasi tersebut, terlihat bahwa **Wanshouxigong** menjadi stasiun pemantauan dengan tingkat 
    pencemaran udara tertinggi. Sebaliknya, **Dingling** menjadi stasiun pemantauan dengan tingkat pencemaran udara 
    terendah. Hal ini menegaskan bahwa wilayah pusat aktivitas perkotaan memiliki risiko polusi yang jauh lebih besar 
    dibandingkan wilayah pinggiran.
    """)

st.caption("Copyright © 2026 - Rizky Putra Reinanda | Data Analysis Project")