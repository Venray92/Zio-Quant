import pandas as pd
import streamlit as st


def inject_custom_css():
    """Inject CSS global untuk aplikasi."""
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0D1117;
            color: #C9D1D9;
        }
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
    """Render Inline Trade Planner versi bawaan (dengan tabel dan logo)."""

    st.markdown(
        f"<h2 style='color:#FFFFFF;'>📊 Live Trade Plan: {ticker_symbol}</h2>",
        unsafe_allow_html=True,
    )

    period = st.selectbox(
        "Periode Data Analysis",
        options=["1mo", "3mo", "6mo", "1y"],
        index=1,
        key=f"period_select_{ticker_symbol}_{key_suffix}",
    )

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    st.markdown(
        "<h3 style='color:#FFFFFF;'>🎯 Trade Plan Recommendation</h3>",
        unsafe_allow_html=True,
    )

    # Data simulasi tabel bawaan
    df_data = pd.DataFrame([
        {
            "No": 1,
            "Type": "BOW",
            "Score": 55,
            "Grade": "🟡 Grade B (Moderate)",
            "Posisi Harga": "Running / Away",
            "Range Buy Min": 655,
            "Range Buy Max": 675,
            "Area Buy": "655 - 675",
            "Stop Loss": 640,
            "TP 1": 745,
            "TP 2": 785,
        },
        {
            "No": 2,
            "Type": "BOB",
            "Score": 83,
            "Grade": "🟢 Grade A (Ideal)",
            "Posisi Harga": "In Buy Zone",
            "Range Buy Min": 745,
            "Range Buy Max": 760,
            "Area Buy": "745 - 760",
            "Stop Loss": 730,
            "TP 1": 785,
            "TP 2": 830,
        },
    ])

    st.dataframe(df_data, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div style="background-color: #2D2700; border: 1px solid #FFD600; border-radius: 8px; padding: 12px 16px; color: #FFE57F; font-size: 13px; margin-top: 10px;">
            <strong>Pola Candle Terdeteksi:</strong> — — ⚠️ Jauh dari Support (+13.7%)
        </div>
        """,
        unsafe_allow_html=True,
    )
