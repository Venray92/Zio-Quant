import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Zio - Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS
inject_custom_css()

# Inisialisasi session state (Default None agar clean di awal)
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

# Custom CSS untuk menyembunyikan button bawaan & membuat Card menjadi Button Utuh
st.markdown(
    """
    <style>
    /* Trigger Popover Button */
    div[data-testid="stPopover"] > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #00E676 !important;
        color: #00E676 !important;
    }
    
    /* Styling tombol custom yang menyamar jadi Card */
    div.screener-btn-wrapper > button {
        width: 100% !important;
        text-align: left !important;
        padding: 12px 14px !important;
        border-radius: 8px !important;
        background-color: #161B22 !important;
        border: 1px solid #21262D !important;
        color: #FFFFFF !important;
        margin-bottom: 8px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.screener-btn-wrapper > button:hover {
        border-color: #00E676 !important;
        background-color: #1F242C !important;
    }
    
    /* Card Active Style */
    div.screener-btn-active > button {
        width: 100% !important;
        text-align: left !important;
        padding: 12px 14px !important;
        border-radius: 8px !important;
        background-color: #0D2B1D !important;
        border: 1.5px solid #00E676 !important;
        color: #FFFFFF !important;
        margin-bottom: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Header Bar & Popover Menu di Kanan Atas
col_brand, col_popover = st.columns([2.5, 1], vertical_alignment="center")

with col_brand:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px;">📈</span>
            <span style="color: #FFFFFF; font-size: 20px; font-weight: 700;">Zio - Screener</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_popover:
    with st.popover("⚙️ Choose Screener", use_container_width=True):
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: #8B949E; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">PRESET SCREENER</span>
                <span style="color: #00E676; font-size: 11px; font-weight: 700;">3 AVAILABLE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        curr = st.session_state["selected_screener"]

        # Option 1: Stoch - Psar
        is_active = curr == "stoch_psar"
        wrapper_class = "screener-btn-active" if is_active else "screener-btn-wrapper"
        active_badge = " [Active] ✔️" if is_active else ""

        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        if st.button(
            f"📈 1. Stoch – Psar{active_badge}\nStoch (10,5,5) GC (0–2 Hari) & Psar Dead Cross (0 Hari)",
            key="btn_card_stoch",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "stoch_psar"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Option 2: RSI + Pattern
        is_active = curr == "rsi"
        wrapper_class = "screener-btn-active" if is_active else "screener-btn-wrapper"
        active_badge = " [Active] ✔️" if is_active else ""

        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        if st.button(
            f"📈 2. RSI + Pattern{active_badge}\nRSI Divergence & Chart Pattern Breakout / Reversal",
            key="btn_card_rsi",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "rsi"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Option 3: Trade Plan Filter
        is_active = curr == "trade_plan"
        wrapper_class = "screener-btn-active" if is_active else "screener-btn-wrapper"
        active_badge = " [Active] ✔️" if is_active else ""

        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        if st.button(
            f"🎯 3. Trade Plan Filter{active_badge}\nBatch Screening & Dynamic Support / Resistance Scoring",
            key="btn_card_tp",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "trade_plan"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #21262D;'>",
    unsafe_allow_html=True,
)

# 4. State Default Clean / Render Screener Terpilih
if st.session_state["selected_screener"] is None:
    st.markdown(
        """
        <div style="background-color: #161B22; border: 1px dashed #30363D; border-radius: 8px; padding: 80px 20px; text-align: center; margin-top: 20px;">
            <h2 style="color: #FFFFFF; font-size: 22px; margin-bottom: 8px;">Selamat Datang di Zio - Screener Dashboard</h2>
            <p style="color: #8B949E; font-size: 14px; max-width: 500px; margin: 0 auto;">
                Pilih strategi screening saham IHSG di menu tombol <strong>⚙️ Choose Screener</strong> di pojok kanan atas untuk memulai analisis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif st.session_state["selected_screener"] == "stoch_psar":
    render_tab_stoch_psar()
elif st.session_state["selected_screener"] == "rsi":
    render_tab_rsi()
elif st.session_state["selected_screener"] == "trade_plan":
    render_tab_trade_planner()
