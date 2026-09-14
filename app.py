import streamlit as st
from trade_planner import TradePlanner

st.set_page_config(page_title="Zio Quant Trade Plan", layout="wide")
st.title("📊 Zio Quant Trade Planner")

# Memanggil Class TradePlanner
ticker = st.text_input("Kode Saham (IDX):", value="INCO.JK")

if st.button("Hitung Trade Plan"):
  with st.spinner("Mengunduh data & mengolah trade plan..."):
    # Inisialisasi Class secara Terisolasi
    planner = TradePlanner(ticker=ticker)
    planner.fetch_and_prepare_data()

    # Ambil Output DataFrame
    direction_df = planner.get_direction()
    trade_plan_df = planner.generate_trade_plan()
    strong_res = planner.get_strong_resistance()
    strong_sup = planner.get_strong_support()
    swing_points = planner.get_swing_points()

    # Tampilkan di Streamlit UI
    st.subheader("🎯 Direction Market")
    st.dataframe(direction_df, use_container_width=True)

    st.subheader("📝 Trade Plan")
    st.dataframe(trade_plan_df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
      st.subheader("🔴 Strong Resistance")
      st.dataframe(strong_res, use_container_width=True)
    with col2:
      st.subheader("🟢 Strong Support")
      st.dataframe(strong_sup, use_container_width=True)

    st.subheader("📌 Swing Points Summary (30 Titik)")
    st.dataframe(swing_points, use_container_width=True)
