import base64
import os
import streamlit as st


def get_logo_base64(file_path="logo.jpg"):
    """Konversi file logo ke format base64."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None


def render_header():
    """Menampilkan Header Bar (Logo & Title Z-QUANT) serta Garis Pembatas."""

    # Cek apakah ada query param reset dari klik logo/home
    if st.query_params.get("reset") == "true":
        st.session_state["selected_screener"] = None
        st.query_params.clear()
        st.rerun()

    logo_b64 = get_logo_base64("logo.jpg")

    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo-img" />'
    else:
        logo_html = '<span style="font-size: 32px;">⚡</span>'

    # Render Logo & Title Z-QUANT
    st.markdown(
        f"""
        <div class="brand-container" style="position: relative; z-index: 999999; pointer-events: auto; margin-bottom: 12px;">
            <a href="/?reset=true" target="_self" class="brand-link" style="display: inline-flex; align-items: center; gap: 12px; text-decoration: none; cursor: pointer;">
                {logo_html}
                <span class="brand-title-text" style="cursor: pointer;">Z-QUANT</span>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header_divider():
    """Menampilkan garis pembatas hijau neon di bawah top navigation."""
    st.markdown(
        "<hr style='margin-top: 15px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #00FF66, transparent);'>",
        unsafe_allow_html=True,
    )


def render_welcome():
    """Menampilkan tampilan Welcome Banner saat belum ada screener terpilih."""
    st.markdown(
        """
        <div style="background-color: #242424; border: 1px solid #00FF66; box-shadow: 0 0 20px rgba(0, 255, 102, 0.2); padding: 70px 20px; text-align: center; margin-top: 10px; font-family: 'Share Tech Mono', monospace;">
            <h2 style="color: #00FF66; font-size: 24px; margin-bottom: 8px; text-shadow: 0 0 10px #00FF66; font-weight: 900; letter-spacing: 2px;">
                WELCOME TO Z-QUANT TERMINAL
            </h2>
            <p style="color: #8A8B98; font-size: 13px; max-width: 580px; margin: 0 auto 16px auto; letter-spacing: 1px;">
                Pilih strategi screening saham IHSG di menu <strong style="color:#00FF66;">CHOOSE_SCREENER</strong> di bawah logo untuk memulai analisis.
            </p>
            <div style="display: inline-block; background: rgba(0, 255, 102, 0.05); border: 1px solid #00FF66; color: #8A8B98; padding: 6px 16px; font-size: 11px;">
                STATUS: <span style="color: #00FF66; font-weight: bold; text-shadow: 0 0 5px #00FF66;">[ONLINE]</span> | ENGINE: <span style="color: #00F3FF; font-weight: bold;">[QUANT]</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
