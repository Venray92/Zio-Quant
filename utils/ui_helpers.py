import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from engines.trade_planner import TradePlanner


# ==============================================================================
# FUNGSI 1: INJECT CSS KUSTOM
# Menyuntikkan file assets/style.css ke Streamlit untuk custom styling
# ==============================================================================
def inject_custom_css():
    """Mengimpor style CSS eksternal dari assets/style.css"""
    # Membentuk path relatif menuju file assets/style.css
    css_path = os.path.join("assets", "style.css")
    
    # Cek apakah file CSS tersebut benar-benar ada di direktori
    if os.path.exists(css_path):
        # Buka dan baca isi file CSS dengan encoding UTF-8
        with open(css_path, "r", encoding="utf-8") as f:
            # Inject isi CSS ke Streamlit menggunakan st.markdown dengan unsafe_allow_html
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ==============================================================================
# FUNGSI 2: HELPER FORMAT ANGKA UNTUK TAMPILAN
# Mengonversi nilai numerik menjadi string berformat desimal / ribuan yang rapi
# ==============================================================================
def _format_val(val):
    # Jika data kosong (NaN/None/string kosong/tanda strip), kembalikan tanda strip "-"
    if pd.isna(val) or val is None or val == "" or val == "-":
        return "-"
    try:
        # Konversi nilai ke float
        num = float(val)
        # Jika angka bulat (misal 1000.0), tampilkan tanpa desimal dengan pemisah ribuan (1,000)
        # Jika angka desimal, tampilkan 2 angka di belakang koma (1,000.50)
        return f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
    except (ValueError, TypeError):
        # Jika gagal di-float-kan (misal berupa teks), kembalikan bentuk string aslinya
        return str(val)


# ==============================================================================
# FUNGSI 3: HELPER PEMBERSIH ANGKA UNTUK KALKULASI
# Membersihkan string angka bercampur koma menjadi float murni
# ==============================================================================
def _clean_num(val):
    # Jika data kosong (NaN/None/string kosong/tanda strip), kembalikan None
    if pd.isna(val) or val is None or val == "" or val == "-":
        return None
    try:
        # Jika berupa string, hapus karakter koma separator ribuan dan spasi
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        # Konversi ke float murni agar siap dihitung secara matematis
        return float(val)
    except Exception:
        # Jika terjadi error saat konversi, kembalikan None secara aman
        return None


# ==============================================================================
# FUNGSI 4: KALKULASI RISK TO REWARD RATIO (R:R)
# Menghitung rasio Risk to Reward untuk Target 1 dan Target 2
# ==============================================================================
def calculate_rr_ratios(row):
    # Ambil nilai Buy dari kolom yang tersedia (prioritas: Range Buy Max, Buy Max, Buy Min)
    buy_val = _clean_num(
        row.get("Range Buy Max", row.get("Buy Max", row.get("Buy Min", None)))
    )
    # Ambil nilai Stop Loss dari kolom (Stop Loss atau SL)
    sl_val = _clean_num(row.get("Stop Loss", row.get("SL", None)))
    # Ambil nilai Target Price 1
    tp1_val = _clean_num(row.get("TP 1", row.get("TP1", row.get("Target 1", None))))
    # Ambil nilai Target Price 2
    tp2_val = _clean_num(row.get("TP 2", row.get("TP2", row.get("Target 2", None))))

    # Default tampilan rasio jika tidak bisa dihitung
    rr_tp1_str = "-"
    rr_tp2_str = "-"

    # Syarat perhitungan R:R: Buy Price dan Stop Loss harus valid, dan Buy Price > Stop Loss
    if buy_val and sl_val and (buy_val > sl_val):
        # Jarak resiko (Risk) = Harga Beli - Stop Loss
        risk = buy_val - sl_val
        
        # Hitung R:R Target 1 jika Target 1 lebih tinggi dari Harga Beli
        if tp1_val and tp1_val > buy_val:
            rr_tp1_str = f"1 : {((tp1_val - buy_val) / risk):.1f}"
            
        # Hitung R:R Target 2 jika Target 2 lebih tinggi dari Harga Beli
        if tp2_val and tp2_val > buy_val:
            rr_tp2_str = f"1 : {((tp2_val - buy_val) / risk):.1f}"

    # Kembalikan pasangan string rasio R:R TP1 dan TP2
    return rr_tp1_str, rr_tp2_str


# ==============================================================================
# FUNGSI 5: RENDER INLINE TRADE PLANNER (KOMPONEN UI UTAMA)
# Menampilkan detail Trade Plan, TradingView Chart, dan Fitur Watchlist
# ==============================================================================
def render_inline_trade_planner(ticker_symbol, key_suffix, screener_name="Screener"):
    # Buat garis pemisah vertikal sebelum komponen dimulai
    st.markdown("---")

    # Pastikan session state untuk "watchlist" sudah diinisialisasi sebagai list kosong
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []

    # 1. RENDER HEADER FUTURISTIK MENGGUNAKAN HTML/CSS
    st.markdown(
        f"""
        <div class="live-plan-header">
            <div class="live-plan-title">
                📊 LIVE TRADE PLAN: <span class="live-plan-ticker">{ticker_symbol}</span>
            </div>
            <div style="font-size: 12px; color: #8B949E; font-weight: 600;">
                SYSTEM STATUS: <span style="color: #00E676;">ONLINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. DROPDOWN PERIODE & BUTTON ADD TO WATCHLIST
    # Menggunakan 3 kolom layout dengan posisi tombol sejajar di bagian bawah (vertical_alignment="bottom")
    col_select, _, col_btn = st.columns([1, 2, 1], vertical_alignment="bottom")

    # Kolom Pertama: Dropdown Pemilihan Periode Data
    with col_select:
        period_selected = st.selectbox(
            "⏱️ Periode Data Analysis",
            options=["3mo", "6mo", "1y", "2y"],
            index=0,
            key=f"period_{key_suffix}",
        )

    # Kolom Ketiga: Tombol Manajemen Watchlist
    with col_btn:
        # Bersihkan format kode ticker (huruf besar & hapus spasi)
        clean_ticker_code = ticker_symbol.upper().strip()

        # Ambil daftar ticker yang sudah tersimpan di watchlist session state
        existing_list = [
            x.get("Ticker", x) if isinstance(x, dict) else str(x)
            for x in st.session_state["watchlist"]
        ]
        # Cek apakah saham ini sudah ada di dalam watchlist
        is_in_watchlist = clean_ticker_code in existing_list

        # Jika sudah ada di watchlist, tampilkan tombol ter-disabled "✅ In Watchlist"
        if is_in_watchlist:
            st.button(
                "✅ In Watchlist",
                key=f"btn_add_wl_{key_suffix}",
                disabled=True,
                use_container_width=True,
            )
        # Jika belum ada di watchlist, tampilkan tombol aktif "➕ Add to Watchlist"
        else:
            if st.button(
                "➕ Add to Watchlist",
                key=f"btn_add_wl_{key_suffix}",
                use_container_width=True,
            ):
                # Tentukan nama asal screener pencetus sinyal
                active_source = screener_name
                if active_source == "Screener" and "active_screener_name" in st.session_state:
                    active_source = st.session_state.get("active_screener_name", "Screener")

                # Masukkan data saham beserta asal screener-nya ke session state watchlist
                st.session_state["watchlist"].append(
                    {"Ticker": clean_ticker_code, "Notes": active_source}
                )

                # Tampilkan notifikasi pop-up (toast) sukses
                st.toast(
                    f"🚀 **{clean_ticker_code}** ({active_source}) berhasil ditambahkan ke Watchlist!",
                    icon="📌",
                )
                # Refresh halaman Streamlit agar state tombol langsung berubah
                st.rerun()

    # 3. EMBED WIDGET CHART TRADINGVIEW INTERAKTIF
    # Hapus prefix/suffix IDX atau .JK untuk format TradingView symbol
    clean_ticker = (
        ticker_symbol.replace(".JK", "").replace("IDX:", "").strip().upper()
    )
    # Ganti karakter titik menjadi underscore untuk ID unik container HTML Javascript
    safe_container_id = clean_ticker.replace(".", "_")
    # Format symbol standard TradingView (contoh: "IDX:BBCA")
    tv_symbol = f"IDX:{clean_ticker}"

    # Script HTML + Javascript TradingView Widget
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:550px; width:100%; border-radius:10px; overflow:hidden; border: 1px solid #30363D; margin-top: 10px; margin-bottom: 8px;">
      <div id="tv_chart_container_{safe_container_id}" style="height:100%; width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      if (typeof TradingView !== 'undefined') {{
          new TradingView.widget({{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "D",
            "timezone": "Asia/Jakarta",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#1A1A1A",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "save_image": true,
            "container_id": "tv_chart_container_{safe_container_id}"
          }});
      }}
      </script>
    </div>
    """
    # Render iframe HTML widget TradingView di Streamlit
    components.html(tv_html, height=560)

    # Catatan kecil petunjuk bagi pengguna di bawah chart
    st.markdown(
        "<div style='font-size: 11px; color: #8B949E; margin-bottom: 20px; font-weight: 500;'>"
        "💡 *Harap lakukan screenshot chart jika Anda membuat tarikan garis/analisa visual.*"
        "</div>",
        unsafe_allow_html=True,
    )

    # 4. KARTU REKOMENDASI TRADE PLAN (MEMANGGIL ENGINE TRADE PLANNER)
    with st.spinner(f"⚡ Menganalisis Trade Plan {ticker_symbol}..."):
        try:
            # Inisialisasi class TradePlanner dari engines/trade_planner.py
            planner = TradePlanner(
                ticker=ticker_symbol.upper(), period=period_selected
            )
            # Jalankan pengambilan & pra-pemrosesan data historis harga jika method-nya ada
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

            # Generate dataframe Trade Plan rekomendasi strategi
            df_plan = (
                planner.generate_trade_plan()
                if hasattr(planner, "generate_trade_plan")
                else None
            )

            # Jika hasil analisisTrade Plan tidak kosong
            if df_plan is not None and not df_plan.empty:
                # Tampilkan Sub-Judul Section
                st.markdown(
                    '<div class="section-title">🎯 Trade Plan Recommendation</div>',
                    unsafe_allow_html=True,
                )

                # Looping setiap baris strategi rekomendasi yang dihasilkan oleh engine
                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    # Tentukan Nama Strategi / Tipe Plan
                    plan_type = row.get(
                        "Type", row.get("Strategy", f"Plan #{plan_no}")
                    )
                    # Skor kekuatan sinyal & grade rekomendasi
                    score = row.get("Score", 0)
                    grade = row.get("Grade", "N/A")
                    posisi = row.get("Posisi Harga", row.get("Status", "-"))

                    # Format angka Area Buy (Min - Max)
                    range_min = _format_val(
                        row.get("Range Buy Min", row.get("Buy Min", "-"))
                    )
                    range_max = _format_val(
                        row.get("Range Buy Max", row.get("Buy Max", "-"))
                    )
                    area_buy = (
                        f"{range_min} - {range_max}"
                        if range_min != "-" and range_max != "-"
                        else range_min
                    )

                    # Format angka Stop Loss, TP1, dan TP2
                    stop_loss = _format_val(
                        row.get("Stop Loss", row.get("SL", "-"))
                    )
                    tp1 = _format_val(row.get("TP 1", row.get("TP1", "-")))
                    tp2 = _format_val(row.get("TP 2", row.get("TP2", "-")))

                    # Tentukan warna status posisi harga (Hijau jika dalam Buy Zone, Kuning jika di luar)
                    posisi_color = (
                        "#10B981" if "Buy Zone" in str(posisi) else "#F59E0B"
                    )

                    # Template HTML Card Futuristik untuk menampilkan detail Trade Plan
                    card_html = f"""
                    <div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 5px solid #00E676; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 12px; margin-bottom: 14px;">
                            <div>
                                <span style="background: linear-gradient(90deg, #00E676 0%, #38BDF8 100%); color: #0E1117; font-weight: 900; font-size: 13px; padding: 4px 12px; border-radius: 6px;">#{plan_no} {plan_type}</span>
                                <span style="font-size: 13px; font-weight: 700; color: #E6EDF3; margin-left: 8px;">{grade}</span>
                            </div>
                            <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #A855F7; color: #F3E8FF; font-weight: 800; padding: 4px 14px; border-radius: 20px; font-size: 12px;">
                                SCORE: {score}
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; text-align: center;">
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.2);">
                                <div style="font-size: 10px; color: #38BDF8; font-weight: 800;">Area Buy</div>
                                <div style="font-size: 15px; font-weight: 800; color: #38BDF8; margin-top: 4px;">{area_buy}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 82, 82, 0.2);">
                                <div style="font-size: 10px; color: #FF5252; font-weight: 800;">Stop Loss</div>
                                <div style="font-size: 15px; font-weight: 800; color: #FF5252; margin-top: 4px;">{stop_loss}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 10px; color: #00E676; font-weight: 800;">Target 1</div>
                                <div style="font-size: 15px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp1}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 10px; color: #00E676; font-weight: 800;">Target 2</div>
                                <div style="font-size: 15px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp2}</div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px; background-color: #0E1117; padding: 10px 14px; border-radius: 8px; border: 1px solid #21262D;">
                            <span style="color: #8B949E; font-weight: 600;">Posisi Harga Saat Ini:</span>
                            <span style="font-weight: 800; color: {posisi_color};">{posisi}</span>
                        </div>
                    </div>
                    """
                    # Render kartu ke antarmuka Streamlit
                    st.markdown(card_html, unsafe_allow_html=True)

                    # KALKULASI & PENAMPILAN RASIO RISK TO REWARD (R:R)
                    rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)

                    # Tampilkan komponen Expander untuk detail Rasio R:R
                    with st.expander(
                        f"⚙️ Parameter Lengkap & Rasio R:R #{plan_no} ({plan_type})",
                        expanded=True,
                    ):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(
                                label="R:R ( Target 1 )", value=rr_tp1_val
                            )
                        with c2:
                            st.metric(
                                label="R:R ( Target 2 )", value=rr_tp2_val
                            )
            # Jika tidak ada rekomendasi Trade Plan yang memenuhi syarat teknikal
            else:
                st.info(f"Tidak ada Trade Plan yang tersedia untuk **{ticker_symbol}** pada periode ini.")

        # Penanganan error jika eksekusi TradePlanner gagal (misal gagal ambil data yfinance)
        except Exception as e:
            st.error(f"Gagal memuat Trade Plan: {e}")
