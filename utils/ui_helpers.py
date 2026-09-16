import streamlit as st


def apply_custom_css():
    """Menginjeksikan styling CSS Futuristik Modern & Memperbaiki Warna Button."""
    css_code = """
    <style>
    /* 1. KUSTOMISASI TOMBOL PRIMARY (PENGGANTI WARNA MERAH JADI HIJAU/TEAL FUTURISTIK) */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-baseweb="button"][aria-label*="Selected"],
    div.stButton > button:contains("Selected") {
        background: linear-gradient(135deg, #00C853 0%, #009688 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 200, 83, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #00E676 0%, #00BFA5 100%) !important;
        box-shadow: 0 6px 16px rgba(0, 230, 118, 0.5) !important;
        transform: translateY(-1px);
    }

    /* Tombol Run Screening Khusus */
    div.stButton > button:contains("Run Screening") {
        background: linear-gradient(135deg, #2979FF 0%, #1565C0 100%) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(41, 121, 255, 0.3) !important;
    }

    /* 2. CARD SELECTION CONTAINER */
    .stock-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        transition: border-color 0.2s ease;
    }
    
    .stock-card.selected {
        border: 2px solid #00E676 !important;
        background-color: rgba(0, 230, 118, 0.05);
    }

    /* Metric Badge Styling */
    .badge-score {
        background-color: #21262D;
        border: 1px solid #30363D;
        color: #FFD600;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    </style>
    """
    st.markdown(css_code, unsafe_allow_html=True)


def set_selected_symbol(symbol: str):
    """Callback function untuk memastikan state terpilih di-update secara instan."""
    st.session_state["selected_symbol"] = symbol
    if "active_ticker" in st.session_state:
        st.session_state["active_ticker"] = symbol


def render_stock_card(
    ticker: str,
    score: int,
    signal_type: str,
    date_range: str,
    price: int,
    change_pct: float,
    is_selected: bool = False,
):
    """Fungsi helper untuk merender kartu saham di panel kiri dengan tombol interaktif yang sinkron."""
    clean_ticker = ticker.replace(".JK", "")
    card_border = "#00E676" if is_selected else "#30363D"
    bg_color = "rgba(0, 230, 118, 0.05)" if is_selected else "#161B22"

    # HTML Card Container
    card_html = f"""
    <div style="
        background-color: {bg_color};
        border: 1px solid {card_border};
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 16px; font-weight: 800; color: #FFFFFF;">{clean_ticker}</span>
                <span style="background-color: #21262D; color: #FFD600; font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">
                    ⭐ {score}
                </span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 14px; font-weight: 700; color: #FFFFFF;">{price:,}</div>
                <div style="font-size: 11px; font-weight: 600; color: {'#FF5252' if change_pct < 0 else '#00E676'};">
                    {change_pct:+.2f}%
                </div>
            </div>
        </div>
        <div style="margin-top: 6px; font-size: 11px; color: #8B949E;">
            📌 {signal_type}<br>
            📅 {date_range}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Render Button yang tersinkronisasi langsung dengan State
    btn_label = (
        f"✓ Selected ({clean_ticker})"
        if is_selected
        else f"Select {clean_ticker}"
    )
    btn_type = "primary" if is_selected else "secondary"

    st.button(
        btn_label,
        key=f"btn_select_{clean_ticker}",
        type=btn_type,
        use_container_width=True,
        on_click=set_selected_symbol,
        args=(ticker,),
    )
