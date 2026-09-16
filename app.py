import base64
import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z - QUANT",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS
inject_custom_css()

# Inisialisasi session state
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None


# Helper untuk load gambar lokal ke base64 agar bisa ditampilkan di CSS/HTML
def get_image_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# Ganti path ini sesuai lokasi file gambar kamu di project
logo_b64 = get_image_base64("Gemini_Generated_Image_64qobr64qobr64qo (1).jpg")

# 3. Custom CSS Cyberpunk & Logo Besar
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    .stApp {{
        background-color: #030407 !important;
        color: #C0C5D0 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }}

    /* Sembunyikan Header bawaan */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }}

    /* Custom Header Brand (Logo Besar + Nama Z - QUANT) */
    .brand-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        background: transparent;
        border: none;
        padding: 0;
        cursor: pointer;
    }}

    .brand-logo {{
        width: 70px;
        height: 70px;
        border-radius: 8px;
        object-fit: cover;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
        border: 1px solid #00F3FF;
    }}

    .brand-title {{
        color: #00F3FF;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
        font-family: 'Share Tech Mono', monospace;
    }}

    /* Tombol Klik Logo/Home */
    div.btn-home-container div.stButton > button {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
        height: auto !important;
    }}

    /* Popover Menu Styling */
    div[data-testid="stPopover"] > button {{
        background-color: #090C15 !important;
        border: 1.5px solid #00F3FF !important;
        color: #00F3FF !important;
        border-radius: 0px !important;
        padding: 6px 16px !important;
        font-weight: 700 !important;
        font-family: 'Share Tech Mono', monospace !important;
        height: 50px !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }}
    div[data-testid="stPopover"] > button:hover {{
        background-color: #00F3FF !important;
        color: #000000 !important;
        box-shadow: 0 0 18px #00F3FF !important;
    }}

    div[data-testid="stPopoverContent"] {{
        background-color: #080A10 !important;
        border: 1px solid #00F3FF !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.3) !important;
    }}

    div[data-testid="stPopoverContent"] [data-testid="stVerticalBlock"] {{
        gap: 4px !important;
    }}

    div[data-testid="stPopoverContent"] div.stButton > button {{
        width: 100% !important;
        text-align: left !important;
        padding: 6px 12px !important;
        height: 38px !important;
        border-radius: 0px !important;
        background-color: #0D101D !important;
        border: 1px solid #1E2338 !important;
        color: #C0C5D0 !important;
        font-size: 13px !important;
        font-family: 'Share Tech Mono', monospace !important;
    }}

    div[data-testid="stPopoverContent"] div.stButton > button:hover {{
        border-color: #00F3FF !important;
        color: #00F3FF !important;
        background-color: rgba(0, 243, 255, 0.1) !important;
    }}

    div.btn-active div.stButton > button {{
        background-color: rgba(0, 243, 255, 0.15) !important;
        border: 1.5px solid #00F3FF !important;
        color: #00F3FF !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# 4. Header Bar (Logo Besar Kiri Atas + Popover Kanan)
col_brand, col_popover = st.columns([3, 1], vertical_alignment="center")

with col_brand:
    st.markdown('<div class="btn-home-container">', unsafe_allow_html=True)
    # Tombol klik brand/logo untuk balik ke Home
    if st.button(
        f"Z - QUANT",
        key="btn_go_home",
    ):
        st.session_state["selected_screener"] = None
        st.rerun()

    # Menampilkan visual Logo + Nama
    st.markdown(
        f"""
        <div class="brand-header" style="margin-top: -45px; pointer-events: none;">
            <img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo" />
            <span class="brand-title">Z - QUANT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_popover:
    with st.popover("🎛️ CHOOSE_SCREENER", use_container_width=True):
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 0 2px; font-family: 'Share Tech Mono', monospace;">
                <span style="color: #00F3FF; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">PRESET_SCREENER</span>
                <span style="color: #00E676; font-size: 10px; font-weight: 700;">3 AVAILABLE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        curr = st.session_state["selected_screener"]

        # Button 1: RSI - Divergence
        cls_rsi = "btn-active" if curr == "rsi" else ""
        badge_rsi = " [ACTIVE] ✔" if curr == "rsi" else ""
        st.markdown(f'<div class="{cls_rsi}">', unsafe_allow_html=True)
        if st.button(
            f"1. RSI - Divergence{badge_rsi}",
            key="btn_rsi",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "rsi"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Button 2: Stoch - Psar
        cls_stoch = "btn-active" if curr == "stoch_psar" else ""
        badge_stoch = " [ACTIVE] ✔" if curr == "stoch_psar" else ""
        st.markdown(f'<div class="{cls_stoch}">', unsafe_allow_html=True)
        if st.button(
            f"2. Stoch - Psar{badge_stoch}",
            key="btn_stoch",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "stoch_psar"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Button 3: Trade Plan - Batch Filter
        cls_tp = "btn-active" if curr == "trade_plan" else ""
        badge_tp = " [ACTIVE] ✔" if curr == "trade_plan" else ""
        st.markdown(f'<div class="{cls_tp}">', unsafe_allow_html=True)
        if st.button(
            f"3. Trade Plan - Batch Filter{badge_tp}",
            key="btn_tp",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "trade_plan"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<hr style='margin-top: 15px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #00F3FF, transparent);'>",
    unsafe_allow_html=True,
)

# 5. Home View / Render Tab
if st.session_state["selected_screener"] is None:
    st.markdown(
        """
        <div style="background-color: #080A12; border: 1px solid #00F3FF; box-shadow: 0 0 20px rgba(0, 243, 255, 0.15); padding: 70px 20px; text-align: center; margin-top: 10px; font-family: 'Share Tech Mono', monospace;">
            <h2 style="color: #00F3FF; font-size: 24px; margin-bottom: 8px; text-shadow: 0 0 8px #00F3FF; font-weight: 900; letter-spacing: 2px;">
                WELCOME TO Z - QUANT TERMINAL
            </h2>
            <p style="color: #8A8B98; font-size: 13px; max-width: 580px; margin: 0 auto 16px auto; letter-spacing: 1px;">
                Pilih strategi screening saham IHSG pada menu <strong>🎛️ CHOOSE_SCREENER</strong> di pojok kanan atas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif st.session_state["selected_screener"] == "rsi":
    render_tab_rsi()
elif st.session_state["selected_screener"] == "stoch_psar":
    render_tab_stoch_psar()
elif st.session_state["selected_screener"] == "trade_plan":
    render_tab_trade_planner()
