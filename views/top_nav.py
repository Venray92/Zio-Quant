import base64
import streamlit as st

# 1. MENGUBAH SVG MENTAH KE BASE64 DATA URI
SVG_HOME_RAW = """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22 22L2 22" stroke="#00F3FF" stroke-width="1.5" stroke-linecap="round"/><path d="M2 11L6.06296 7.74968M22 11L13.8741 4.49931C12.7784 3.62279 11.2216 3.62279 10.1259 4.49931L9.34398 5.12486" stroke="#00F3FF" stroke-width="1.5" stroke-linecap="round"/><path d="M15.5 5.5V3.5C15.5 3.22386 15.7239 3 16 3H18.5C18.7761 3 19 3.22386 19 3.5V8.5" stroke="#00F3FF" stroke-width="1.5" stroke-linecap="round"/><path d="M4 22V9.5" stroke="#00F3FF" stroke-width="1.5" stroke-linecap="round"/><path d="M20 9.5V13.5M20 22V17.5" stroke="#00F3FF" stroke-width="1.5" stroke-linecap="round"/><path d="M15 22V17C15 15.5858 15 14.8787 14.5607 14.4393C14.1213 14 13.4142 14 12 14C10.5858 14 9.87868 14 9.43934 14.4393M9 22V17" stroke="#00F3FF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 9.5C14 10.6046 13.1046 11.5 12 11.5C10.8954 11.5 10 10.6046 10 9.5C10 8.39543 10.8954 7.5 12 7.5C13.1046 7.5 14 8.39543 14 9.5Z" stroke="#00F3FF" stroke-width="1.5"/></svg>"""

SVG_WATCHLIST_RAW = """<svg viewBox="0 0 32.219 32.219" xmlns="http://www.w3.org/2000/svg"><path style="fill:#00F3FF;" d="M32.144,12.402c-0.493-1.545-3.213-1.898-6.09-2.277c-1.578-0.209-3.373-0.445-3.914-0.844c-0.543-0.398-1.304-2.035-1.978-3.482C18.94,3.17,17.786,0.686,16.166,0.68l-0.03-0.003c-1.604,0.027-2.773,2.479-4.016,5.082c-0.684,1.439-1.463,3.07-2.005,3.463c-0.551,0.394-2.342,0.613-3.927,0.803c-2.877,0.352-5.598,0.68-6.108,2.217c-0.507,1.539,1.48,3.424,3.587,5.424c1.156,1.094,2.465,2.34,2.67,2.98c0.205,0.639-0.143,2.414-0.448,3.977c-0.557,2.844-1.084,5.535,0.219,6.5c0.312,0.225,0.704,0.338,1.167,0.328c1.331-0.023,3.247-1.059,5.096-2.062c1.387-0.758,2.961-1.611,3.661-1.621c0.675,0.002,2.255,0.881,3.647,1.654c1.891,1.051,3.852,2.139,5.185,2.119c0.414-0.01,0.771-0.117,1.06-0.322c1.312-0.947,0.814-3.639,0.285-6.494c-0.289-1.564-0.615-3.344-0.409-3.982c0.213-0.639,1.537-1.867,2.702-2.955C30.628,15.808,32.634,13.945,32.144,12.402z M21.473,19.355h-3.722v3.797h-3.237v-3.797h-3.768v-3.238h3.768v-3.691h3.237v3.691h3.722V19.355z"/></svg>"""

SVG_MM_RAW = """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M14,7H11.5A1.5,1.5,0,0,0,10,8.5h0A1.5,1.5,0,0,0,11.5,10h1A1.5,1.5,0,0,1,14,11.5h0A1.5,1.5,0,0,1,12.5,13H10" style="fill: none; stroke: #00F3FF; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></path><path d="M12,6V7m0,6v1" style="fill: none; stroke: #00F3FF; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></path><line x1="6" y1="21" x2="18" y2="21" style="fill: none; stroke: #00F3FF; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></line><rect x="3" y="3" width="18" height="14" rx="1" style="fill: none; stroke: #00F3FF; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></rect></svg>"""

SVG_HOWTO_RAW = """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M13 3L13.7071 2.29289C13.5196 2.10536 13.2652 2 13 2V3ZM14 22C14.5523 22 15 21.5523 15 21C15 20.4477 14.5523 20 14 20V22ZM19 9H20C20 8.73478 19.8946 8.48043 19.7071 8.29289L19 9ZM18 10C18 10.5523 18.4477 11 19 11C19.5523 11 20 10.5523 20 10H18ZM5.21799 19.908L4.32698 20.362H4.32698L5.21799 19.908ZM6.09202 20.782L6.54601 19.891L6.54601 19.891L6.09202 20.782ZM6.09202 3.21799L5.63803 2.32698L5.63803 2.32698L6.09202 3.21799ZM5.21799 4.09202L4.32698 3.63803L4.32698 3.63803L5.21799 4.09202ZM13.109 8.45399L14 8V8L13.109 8.45399ZM13.546 8.89101L14 8L13.546 8.89101ZM9 16C8.44772 16 8 16.4477 8 17C8 17.5523 8.44772 18 9 18V16ZM12 18C12.5523 18 13 17.5523 13 17C13 16.4477 12.5523 16 12 16V18ZM9 12C8.44772 12 8 12.4477 8 13C8 13.5523 8.44772 14 9 14V12ZM13 14C13.5523 14 14 13.5523 14 13C14 12.4477 13.5523 12 13 12V14ZM9 8C8.44772 8 8 8.44772 8 9C8 9.55228 8.44772 10 9 10V8ZM10 10C10.5523 10 11 9.55228 11 9C11 8.44772 10.5523 8 10 8V10ZM17.2299 17.7929C16.8394 18.1834 16.8394 18.8166 17.2299 19.2071C17.6204 19.5976 18.2536 19.5976 18.6441 19.2071L17.2299 17.7929ZM15.0316 15.2507C14.8939 15.7856 15.2159 16.3308 15.7507 16.4684C16.2856 16.6061 16.8308 16.2841 16.9684 15.7493L15.0316 15.2507ZM17.9375 20C17.3852 20 16.9375 20.4477 16.9375 21C16.9375 21.5523 17.3852 22 17.9375 22V20ZM17.9475 22C18.4998 22 18.9475 21.5523 18.9475 21C18.9475 20.4477 18.4998 20 17.9475 20V22Z" fill="#00F3FF"/></svg>"""


def get_b64_icon(svg_str):
    """Helper untuk merubah string SVG ke format Data URI."""
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_str.encode()).decode()}"


def render_top_nav():
    icon_home = get_b64_icon(SVG_HOME_RAW)
    icon_watchlist = get_b64_icon(SVG_WATCHLIST_RAW)
    icon_mm = get_b64_icon(SVG_MM_RAW)
    icon_howto = get_b64_icon(SVG_HOWTO_RAW)

    # Inject CSS untuk penataan posisi tombol & memasang ikon di sebelah kiri teks
    st.markdown(
        f"""
        <style>
        /* Mendorong seluruh baris tombol ke bawah mendekati garis divider */
        div[data-testid="stHorizontalBlock"]:has(button[key*="nav_"]) {{
            align-items: flex-end !important;
            transform: translateY(22px) !important;
            margin-bottom: 0px !important;
        }}

        /* Styling dasar tombol navigasi */
        button[key*="nav_"] {{
            margin-bottom: 0px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            font-weight: 600 !important;
        }}

        /* Penetas ikon SVG presisi kecil (16px) sejajar teks */
        button[key*="nav_"]::before {{
            content: "";
            display: inline-block;
            width: 16px;
            height: 16px;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            flex-shrink: 0;
        }}

        /* Memasangkan background ikon masing-masing tombol */
        button[key="nav_home"]::before {{ background-image: url("{icon_home}"); }}
        button[key="nav_watchlist"]::before {{ background-image: url("{icon_watchlist}"); }}
        button[key="nav_mm"]::before {{ background-image: url("{icon_mm}"); }}
        button[key="nav_howto"]::before {{ background-image: url("{icon_howto}"); }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 1, 1.2, 1, 2.5])

    # 1. HOME
    with cols[0]:
        if st.button("Home", key="nav_home", use_container_width=True):
            st.session_state["selected_page"] = "home"
            st.session_state["selected_screener"] = None
            st.rerun()

    # 2. WATCHLIST
    with cols[1]:
        if st.button("Watchlist", key="nav_watchlist", use_container_width=True):
            st.session_state["selected_page"] = "watchlist"
            st.rerun()

    # 3. MONEY MANAGEMENT
    with cols[2]:
        if st.button(
            "Money Management", key="nav_mm", use_container_width=True
        ):
            st.session_state["selected_page"] = "money_management"
            st.rerun()

    # 4. HOW TO
    with cols[3]:
        if st.button("How To", key="nav_howto", use_container_width=True):
            st.session_state["selected_page"] = "how_to"
            st.rerun()
