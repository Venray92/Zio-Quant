import pandas as pd
import streamlit as st


def inject_custom_css():
    """Inject CSS global untuk styling aplikasi."""
    st.markdown(
        """
        <style>
        /* Modern Dark Theme Base */
        .stApp {
            background-color: #0D1117;
            color: #C9D1D9;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0D1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #21262D;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #30363D;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_inline_trade_planner(ticker_symbol, key_suffix=""):
    """Render Inline Trade Planner dengan Card Futuristik Modern (Tanpa Logo & Tanpa Tabel)."""

    # Inject CSS khusus Card Trade Plan
    st.markdown(
        """
        <style>
        .tp-card-container {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .tp-card-container:hover {
            border-color: #58A6FF;
        }
        .tp-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #21262D;
            padding-bottom: 10px;
            margin-bottom: 12px;
        }
        .tp-badge-type {
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #FFFFFF;
            background: linear-gradient(135deg, #1F6FEB, #238636);
            padding: 4px 10px;
            border-radius: 6px;
        }
        .tp-badge-grade {
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            background-color: #21262D;
            border: 1px solid #30363D;
        }
        .tp-price-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
            gap: 10px;
        }
        .tp-metric-box {
            background-color: #0D1117;
            border: 1px solid #21262D;
            border-radius: 8px;
            padding: 8px 10px;
            text-align: center;
        }
        .tp-metric-box.buy-zone {
            border-color: #0366D6;
            background-color: rgba(3, 102, 214, 0.1);
        }
        .tp-metric-box.stop-loss {
            border-color: #DA3633;
            background-color: rgba(218, 54, 51, 0.1);
        }
        .tp-metric-box.target-profit {
            border-color: #238636;
            background-color: rgba(35, 134, 54, 0.1);
        }
        .tp-metric-title {
            font-size: 10px;
            color: #8B949E;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .tp-metric-value {
            font-size: 14px;
            font-weight: 700;
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. Judul Tanpa Logo/Emoji
    st.markdown(
        f"<h2 style='color:#FFFFFF; margin-top:0; margin-bottom:10px; font-weight:700;'>Live Trade Plan: {ticker_symbol}</h2>",
        unsafe_allow_html=True,
    )

    # Filter Periode Data Analysis
    period = st.selectbox(
        "Periode Data Analysis",
        options=["1mo", "3mo", "6mo", "1y"],
        index=1,
        key=f"period_select_{ticker_symbol}_{key_suffix}",
    )

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # 2. Section Subheader Tanpa Logo/Emoji
    st.markdown(
        "<h3 style='color:#FFFFFF; font-weight:600; margin-bottom:14px;'>Trade Plan Recommendation</h3>",
        unsafe_allow_html=True,
    )

    # DATA SIMULASI TRADE PLAN (Sesuaikan dengan data asli kalkulasi kamu jika ada)
    trade_plan_data = [
        {
            "Type": "BOW",
            "Score": 55,
            "Grade": "🟡 Grade B (Moderate)",
            "Posisi Harga": "Running / Away",
            "Area Buy": "655 - 675",
            "Stop Loss": 640,
            "TP 1": 745,
            "TP 2": 785,
        },
        {
            "Type": "BOB",
            "Score": 83,
            "Grade": "🟢 Grade A (Ideal)",
            "Posisi Harga": "In Buy Zone",
            "Area Buy": "745 - 760",
            "Stop Loss": 730,
            "TP 1": 785,
            "TP 2": 830,
        },
    ]

    # RENDER BENTUK CARD FUTURISTIK (BEBAS TABEL)
    if trade_plan_data:
        for idx, item in enumerate(trade_plan_data):
            tp_type = item.get("Type", "-")
            score = item.get("Score", 0)
            grade = item.get("Grade", "-")
            posisi = item.get("Posisi Harga", "-")
            area_buy = item.get("Area Buy", "-")
            stop_loss = item.get("Stop Loss", "-")
            tp1 = item.get("TP 1", "-")
            tp2 = item.get("TP 2", "-")

            posisi_color = "#00E676" if "Buy Zone" in str(posisi) else "#FFD600"

            card_html = f"""
            <div class="tp-card-container">
                <div class="tp-card-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="tp-badge-type">{tp_type}</span>
                        <span style="color: #8B949E; font-size: 13px; font-weight: 600;">Score: <strong style="color:#FFFFFF;">{score}</strong></span>
                        <span class="tp-badge-grade">{grade}</span>
                    </div>
                    <div>
                        <span style="font-size: 11px; color: #8B949E;">Posisi: </span>
                        <span style="font-size: 12px; font-weight: 700; color: {posisi_color};">{posisi}</span>
                    </div>
                </div>

                <div class="tp-price-grid">
                    <div class="tp-metric-box buy-zone">
                        <div class="tp-metric-title">Area Buy</div>
                        <div class="tp-metric-value" style="color: #58A6FF;">{area_buy}</div>
                    </div>
                    <div class="tp-metric-box stop-loss">
                        <div class="tp-metric-title">Stop Loss</div>
                        <div class="tp-metric-value" style="color: #FF5252;">{stop_loss}</div>
                    </div>
                    <div class="tp-metric-box target-profit">
                        <div class="tp-metric-title">Target Profit 1</div>
                        <div class="tp-metric-value" style="color: #00E676;">{tp1}</div>
                    </div>
                    <div class="tp-metric-box target-profit">
                        <div class="tp-metric-title">Target Profit 2</div>
                        <div class="tp-metric-value" style="color: #00E676;">{tp2}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("Tidak ada rekomendasi Trade Plan untuk saham ini.")

    # Status Candlestick Warning Box
    st.markdown(
        """
        <div style="background-color: #2D2700; border: 1px solid #FFD600; border-radius: 8px; padding: 12px 16px; color: #FFE57F; font-size: 13px; margin-top: 10px;">
            <strong>Pola Candle Terdeteksi:</strong> — — ⚠️ Jauh dari Support (+13.7%)
        </div>
        """,
        unsafe_allow_html=True,
    )
