"""Kompatibilitas antar versi Streamlit (satu tempat, dipakai semua halaman)."""
import inspect

import streamlit as st


def _supports_width():
    try:
        return "width" in inspect.signature(st.button).parameters
    except (TypeError, ValueError):
        return False


# Lebar penuh untuk button / download_button / form_submit_button / popover / dataframe / plotly_chart.
# Streamlit baru memakai width="stretch"; use_container_width sudah ditandai akan dihapus.
STRETCH = {"width": "stretch"} if _supports_width() else {"use_container_width": True}
