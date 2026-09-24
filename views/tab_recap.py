"""Halaman Rekap Screener: rekap harian & mingguan tiap screener (dulu di Home, dipindah 24 Sep
supaya Home nggak kepanjangan -- sekarang satu dropdown dgn Leaderboard di navbar)."""
import streamlit as st

from utils.card_html import compact_html
from utils.icons import svg_icon


def render_page_recap():
    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("calendar-event", 24, "#00F3FF", 2, margin_right=8)}REKAP SCREENER</h1>
<p>Rekap harian & mingguan tiap screener dari update data terakhir -- bukan hasil live, bukan pengaturanmu sendiri.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )

    from views.home import render_recaps

    render_recaps()
