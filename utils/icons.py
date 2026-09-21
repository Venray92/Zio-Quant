"""Ikon outline untuk UI (inline SVG). Sumber: Tabler Icons (MIT License, https://tabler.io/icons).

Dipakai di HTML kartu/judul lewat svg_icon(). Untuk widget bawaan Streamlit (tombol, expander)
pakai icon_kwargs()/expander_kwargs(): ikon Material dipasang hanya kalau versi Streamlit mendukung,
kalau tidak, widget tampil sebagai teks biasa (tanpa error).
"""
import inspect

import streamlit as st

ICON_PATHS = {
    "bolt": '<path d="M13 3l0 7l6 0l-8 11l0 -7l-6 0l8 -11" />',
    "player-play": '<path d="M7 4v16l13 -8l-13 -8" />',
    "player-stop": '<path d="M5 7a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2l0 -10" />',
    "download": '<path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2" /> <path d="M7 11l5 5l5 -5" /> <path d="M12 4l0 12" />',
    "star": '<path d="M12 17.75l-6.172 3.245l1.179 -6.873l-5 -4.867l6.9 -1l3.086 -6.253l3.086 6.253l6.9 1l-5 4.867l1.179 6.873l-6.158 -3.245" />',
    "chart-candle": '<path d="M4 7a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v3a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -3" /> <path d="M6 4l0 2" /> <path d="M6 11l0 9" /> <path d="M10 15a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v3a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -3" /> <path d="M12 4l0 10" /> <path d="M12 19l0 1" /> <path d="M16 6a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1l0 -4" /> <path d="M18 4l0 1" /> <path d="M18 11l0 9" />',
    "calendar": '<path d="M4 7a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12" /> <path d="M16 3v4" /> <path d="M8 3v4" /> <path d="M4 11h16" /> <path d="M11 15h1" /> <path d="M12 15v3" />',
    "trending-up": '<path d="M3 17l6 -6l4 4l8 -8" /> <path d="M14 7l7 0l0 7" />',
    "trending-down": '<path d="M3 7l6 6l4 -4l8 8" /> <path d="M21 10l0 7l-7 0" />',
    "target": '<path d="M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /> <path d="M7 12a5 5 0 1 0 10 0a5 5 0 1 0 -10 0" /> <path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />',
    "chart-bar": '<path d="M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -6" /> <path d="M15 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -10" /> <path d="M9 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -14" /> <path d="M4 20h14" />',
    "clock": '<path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /> <path d="M12 7v5l3 3" />',
    "bookmark-plus": '<path d="M12 17l-6 4v-14a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v5" /> <path d="M16 19h6" /> <path d="M19 16v6" />',
    "circle-check": '<path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /> <path d="M9 12l2 2l4 -4" />',
    "check": '<path d="M5 12l5 5l10 -10" />',
    "copy": '<path d="M7 9.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667l0 -8.666" /> <path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" />',
    "alert-triangle": '<path d="M12 9v4" /> <path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0" /> <path d="M12 16h.01" />',
    "info-circle": '<path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /> <path d="M12 9h.01" /> <path d="M11 12h1v4h1" />',
    "adjustments-horizontal": '<path d="M12 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M4 6l8 0" /> <path d="M16 6l4 0" /> <path d="M6 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M4 12l2 0" /> <path d="M10 12l10 0" /> <path d="M15 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M4 18l11 0" /> <path d="M19 18l1 0" />',
    "bulb": '<path d="M3 12h1m8 -9v1m8 8h1m-15.4 -6.4l.7 .7m12.1 -.7l-.7 .7" /> <path d="M9 16a5 5 0 1 1 6 0a3.5 3.5 0 0 0 -1 3a2 2 0 0 1 -4 0a3.5 3.5 0 0 0 -1 -3" /> <path d="M9.7 17l4.6 0" />',
    "chart-line": '<path d="M4 19l16 0" /> <path d="M4 15l4 -6l4 2l4 -5l4 4" />',
    "database": '<path d="M4 6a8 3 0 1 0 16 0a8 3 0 1 0 -16 0" /> <path d="M4 6v6a8 3 0 0 0 16 0v-6" /> <path d="M4 12v6a8 3 0 0 0 16 0v-6" />',
    "refresh": '<path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4" /> <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" />',
    "trash": '<path d="M4 7l16 0" /> <path d="M10 11l0 6" /> <path d="M14 11l0 6" /> <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /> <path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" />',
    "eraser": '<path d="M19 20h-10.5l-4.21 -4.3a1 1 0 0 1 0 -1.41l10 -10a1 1 0 0 1 1.41 0l5 5a1 1 0 0 1 0 1.41l-9.2 9.3" /> <path d="M18 13.3l-6.3 -6.3" />',
    "hourglass": '<path d="M6.5 7h11" /> <path d="M6.5 17h11" /> <path d="M6 20v-2a6 6 0 1 1 12 0v2a1 1 0 0 1 -1 1h-10a1 1 0 0 1 -1 -1" /> <path d="M6 4v2a6 6 0 1 0 12 0v-2a1 1 0 0 0 -1 -1h-10a1 1 0 0 0 -1 1" />',
    "palette": '<path d="M12 21a9 9 0 0 1 0 -18c4.97 0 9 3.582 9 8c0 1.06 -.474 2.078 -1.318 2.828c-.844 .75 -1.989 1.172 -3.182 1.172h-2.5a2 2 0 0 0 -1 3.75a1.3 1.3 0 0 1 -1 2.25" /> <path d="M7.5 10.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /> <path d="M11.5 7.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /> <path d="M15.5 10.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />',
    "circle-x": '<path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /> <path d="M10 10l4 4m0 -4l-4 4" />',
    "tool": '<path d="M7 10h3v-3l-3.5 -3.5a6 6 0 0 1 8 8l6 6a2 2 0 0 1 -3 3l-6 -6a6 6 0 0 1 -8 -8l3.5 3.5" />',
    "trophy": '<path d="M8 21l8 0" /> <path d="M12 17l0 4" /> <path d="M7 4l10 0" /> <path d="M17 4v8a5 5 0 0 1 -10 0v-8" /> <path d="M3 9a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M17 9a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />',
    "map-pin": '<path d="M9 11a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" /> <path d="M17.657 16.657l-4.243 4.243a2 2 0 0 1 -2.827 0l-4.244 -4.243a8 8 0 1 1 11.314 0" />',
    "scale": '<path d="M7 20l10 0" /> <path d="M6 6l6 -1l6 1" /> <path d="M12 3l0 17" /> <path d="M9 12l-3 -6l-3 6a3 3 0 0 0 6 0" /> <path d="M21 12l-3 -6l-3 6a3 3 0 0 0 6 0" />',
    "filter": '<path d="M4 4h16v2.172a2 2 0 0 1 -.586 1.414l-4.414 4.414v7l-6 2v-8.5l-4.48 -4.928a2 2 0 0 1 -.52 -1.345v-2.227" />',
    "x": '<path d="M18 6l-12 12" /> <path d="M6 6l12 12" />',
    "search": '<path d="M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0" /> <path d="M21 21l-6 -6" />',
    "pin": '<path d="M15 4.5l-4 4l-4 1.5l-1.5 1.5l7 7l1.5 -1.5l1.5 -4l4 -4" /> <path d="M9 15l-4.5 4.5" /> <path d="M14.5 4l5.5 5.5" />',
    "history": '<path d="M12 8l0 4l2 2" /> <path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5" />',
}


def svg_icon(name, size=16, color="currentColor", stroke=1.8, margin_right=0):
    """Ikon outline sebagai teks <svg> (untuk st.markdown(..., unsafe_allow_html=True))."""
    inner = ICON_PATHS.get(name, "")
    mr = f"margin-right:{margin_right}px;" if margin_right else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-3px;flex-shrink:0;{mr}" aria-hidden="true">{inner}</svg>'
    )


def _accepts_icon(func):
    try:
        return "icon" in inspect.signature(func).parameters
    except Exception:
        return False


_SUPPORT = {
    "button": _accepts_icon(st.button),
    "download_button": _accepts_icon(st.download_button),
    "expander": _accepts_icon(st.expander),
}


def icon_kwargs(material_name, widget="button"):
    """Untuk st.button / st.download_button / st.expander: {"icon": ":material/nama:"}
    kalau versi Streamlit mendukung, kalau tidak {} (tampil sebagai teks biasa)."""
    return {"icon": f":material/{material_name}:"} if _SUPPORT.get(widget) else {}


def expander_kwargs(material_name):
    return icon_kwargs(material_name, "expander")
