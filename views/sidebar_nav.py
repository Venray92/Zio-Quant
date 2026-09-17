import streamlit as st

# Set konfigurasi halaman di paling atas
st.set_page_config(
    page_title="IDX Screener", layout="wide", initial_sidebar_state="expanded"
)


def render_sidebar_nav():
    """Sidebar Navigasi Ringkas dengan Ikon + Teks Vertikal."""

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    nav_items = [
        ("screener", "Screener", "⚙️"),
        ("markets", "Markets", "📈"),
        ("stream", "Stream", "📡"),
        ("support", "Support", "🎧"),
    ]

    # Style CSS sederhana & aman
    sidebar_css = """
    <style>
    /* Styling tombol di sidebar */
    [data-testid="stSidebar"] button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        height: 60px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }

    [data-testid="stSidebar"] button p {
        font-size: 12px !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        white-space: pre-line !important;
        text-align: center !important;
    }

    [data-testid="stSidebar"] button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)

    # Render di Sidebar
    with st.sidebar:
        st.write("### NAVIGASI")
        for key, label, icon in nav_items:
            is_active = active_nav == key
            button_text = f"► {icon}\n{label}" if is_active else f"{icon}\n{label}"

            if st.button(button_text, key=f"nav_{key}", use_container_width=True):
                st.session_state["active_nav"] = key
                st.rerun()


# --- WAJIB DIPANGGIL DI FILE UTAMA ---
render_sidebar_nav()

# Tampilan Konten Utama
st.title(f"Halaman: {st.session_state['active_nav'].upper()}")
st.write("Jika teks ini muncul dan sidebar di kiri ada, berarti fungsi berhasil.")
