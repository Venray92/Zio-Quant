import streamlit as st


def render_tab_trade_planner():
    # 🎨 CSS OVERHAUL: MENIRU PERSIS ELEMEN, WARNA, BENTUK, DAN BUTTON GAMBAR REFERENSI
    st.markdown(
        """
        <style>
        /* 1. Root & Background Control */
        .stApp {
            background-color: #07090E !important;
        }

        /* 2. Style Card / Container Utama (Meniru Card Zio) */
        .zio-card-container {
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }

        /* 3. Header Section Style */
        .zio-header-wrapper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 24px;
        }
        .zio-header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .zio-icon-square {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.3);
        }
        .zio-title-text {
            color: #FFFFFF;
            font-size: 1.35rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .zio-badge-pill {
            background-color: rgba(168, 85, 247, 0.15);
            color: #C084FC;
            border: 1px solid rgba(168, 85, 247, 0.3);
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .zio-subtitle-text {
            color: #64748B;
            font-size: 0.85rem;
            margin-top: 2px;
        }

        /* 4. Mini Status Cards (Meniru Card 'Response Time' / 'Status Sistem') */
        .zio-status-card {
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 18px 20px;
            height: 100%;
        }
        .zio-status-title {
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .zio-status-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 4px;
        }
        .zio-status-desc {
            font-size: 0.78rem;
            color: #64748B;
            line-height: 1.3;
        }

        /* 5. Custom Form Labels & Section Header */
        .zio-form-header {
            color: #FFFFFF;
            font-size: 1.05rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }
        .zio-label {
            color: #94A3B8;
            font-size: 0.82rem;
            font-weight: 600;
            margin-bottom: 6px;
            display: block;
        }

        /* 6. Input & Select Styling (Meniru Input Box Dark di Gambar) */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            background-color: #07090E !important;
            border: 1px solid #1E2638 !important;
            border-radius: 8px !important;
            color: #F8FAFC !important;
        }
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 0 1px #8B5CF6 !important;
        }
        textarea {
            background-color: #07090E !important;
            border: 1px solid #1E2638 !important;
            border-radius: 8px !important;
            color: #F8FAFC !important;
        }

        /* 7. Button Customization (Sesuai Gaya Dark/Futuristik) */
        div.stButton > button {
            background-color: #111625 !important;
            color: #A855F7 !important;
            border: 1px solid rgba(168, 85, 247, 0.4) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div.stButton > button:hover {
            background-color: #8B5CF6 !important;
            color: #FFFFFF !important;
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.4) !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5) !important;
        }

        /* Radio Button Container Style */
        div[role="radiogroup"] {
            background-color: #07090E;
            border: 1px solid #1E2638;
            border-radius: 8px;
            padding: 8px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- HEADER UTAMA (Meniru "Pusat Bantuan & Support Zio") ---
    st.markdown(
        """
        <div class="zio-header-wrapper">
            <div class="zio-header-left">
                <div class="zio-icon-square">🎧</div>
                <div>
                    <div class="zio-title-text">
                        Pusat Bantuan & Support Zio
                        <span class="zio-badge-pill">Helpdesk 24/7</span>
                    </div>
                    <div class="zio-subtitle-text">Panduan screener, troubleshooting aplikasi, dan layanan konsultasi tim support.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 3 CARD ATAS (Meniru Response Time, Status Sistem, Dokumentasi) ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="zio-status-card">
                <div class="zio-status-title" style="color: #00E676;">
                    <span>🕒</span> Response Time
                </div>
                <div class="zio-status-value">&lt; 15 Menit</div>
                <div class="zio-status-desc">Layanan fast response saat jam bursa aktif.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="zio-status-card">
                <div class="zio-status-title" style="color: #00E676;">
                    <span>🛡️</span> Status Sistem
                </div>
                <div class="zio-status-value" style="color: #00E676;">All Systems Operational</div>
                <div class="zio-status-desc">Feed IDX & Algoritma Screener normal.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="zio-status-card">
                <div class="zio-status-title" style="color: #F59E0B;">
                    <span>📖</span> Dokumentasi
                </div>
                <div class="zio-status-value" style="color: #F59E0B;">Versi v2.4 Pro</div>
                <div class="zio-status-desc">Modul Trade Plan & Algoritma V3.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # --- FORM UTAMA (Meniru Box "Kirim Pertanyaan / Request Fitur Baru") ---
    st.markdown('<div class="zio-card-container">', unsafe_allow_html=True)

    st.markdown(
        '<div class="zio-form-header"><span style="color:#A855F7;">❓</span> Kirim Pertanyaan / Request Fitur Baru</div>',
        unsafe_allow_html=True,
    )

    f_col1, f_col2 = st.columns(2)

    with f_col1:
        st.markdown(
            '<span class="zio-label">Kategori Masalah:</span>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Kategori Masalah",
            [
                "Indikator & Algoritma Screener",
                "Data Feed / Price Delay",
                "Request Fitur Baru",
            ],
            label_visibility="collapsed",
        )

    with f_col2:
        st.markdown(
            '<span class="zio-label">Judul Singkat:</span>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "Judul Singkat",
            placeholder="Contoh: Pertanyaan indikator BBCA",
            label_visibility="collapsed",
        )

    st.write("")
    st.markdown(
        '<span class="zio-label">Detail Pertanyaan:</span>',
        unsafe_allow_html=True,
    )
    st.text_area(
        "Detail Pertanyaan",
        placeholder="Tulis kendala atau pertanyaan yang ingin Anda tanyakan...",
        height=120,
        label_visibility="collapsed",
    )

    st.write("")
    b_col1, b_col2 = st.columns([4, 1])
    with b_col2:
        st.button(
            "Kirim Pesan 🚀", type="primary", use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # --- FOOTER (Meniru Footer di Gambar) ---
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 4px; color: #475569; font-size: 0.8rem;">
            <div>Official Support Desk • Melayani trader saham seluruh Indonesia</div>
            <div style="color: #A855F7; font-weight: 600; cursor: pointer;">Tutup Jendela</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
