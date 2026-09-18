import os
import streamlit as st


def inject_cyberpunk_theme():
    """Membaca file CSS eksternal dari folder assets dan memasangnya ke Streamlit."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_file_path = os.path.join(base_dir, "assets", "style-money-management.css")

    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(
            f"⚠️ File style `{css_file_path}` tidak ditemukan. Menggunakan tampilan default."
        )


def render_page_money_management():
    """Fungsi utama untuk menampilkan halaman Money Management."""
    # Injeksi style CSS
    inject_cyberpunk_theme()

    st.title("⚡ CYBERPUNK FINANCIAL SYSTEM")
    st.markdown("---")

    # Layout Kolom Kartu Statistik
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="cyber-card">
                <div class="cyber-label">TOTAL CAPITAL</div>
                <div class="cyber-value">$125,450.00</div>
                <span class="cyber-badge badge-cyan">STATUS: ACTIVE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="cyber-card">
                <div class="cyber-label">MONTHLY PROFIT</div>
                <div class="cyber-value">+$14,210.50</div>
                <span class="cyber-badge badge-yellow">+11.3% GROWTH</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="cyber-card-pink">
                <div class="cyber-label">MAX DRAWDOWN</div>
                <div class="cyber-value" style="color: #FF0055;">-4.25%</div>
                <span class="cyber-badge badge-pink">RISK LEVEL: LOW</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Layout Input Form & Selectbox
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🛠️ Transaction Input")
        asset_type = st.selectbox(
            "Pilih Aset Kripto / Saham:",
            ["BTC/USDT", "ETH/USDT", "SOL/USDT", "NVDA", "AAPL", "TSLA"],
        )
        order_type = st.selectbox(
            "Tipe Order:",
            ["LIMIT BUY", "MARKET BUY", "STOP LOSS", "TAKE PROFIT"],
        )
        amount = st.number_input(
            "Jumlah Alokasi ($):", min_value=10, value=1000, step=50
        )

        if st.button("EXECUTE TRANSACTION"):
            st.success(
                f"Order {order_type} untuk {asset_type} sebesar ${amount} berhasil!"
            )

    with col_right:
        st.subheader("📊 System Log")
        with st.expander("Lihat Rincian Riwayat Transaksi", expanded=True):
            st.write("• [2026-09-18] BOUGHT BTC/USDT @ $64,200")
            st.write("• [2026-09-17] SOLD ETH/USDT @ $3,450 (+5.2%)")
            st.write("• [2026-09-15] BOUGHT NVDA @ $125.00")
