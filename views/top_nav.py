import streamlit as st

from utils.icons import icon_kwargs
from utils.pages import BASE_PAGES, SCREENER_KEYS, get_pages, keyed_container, link_width_kwargs
from utils.screeners import SCREENERS, get_screener


def _active(flag):
    return "__active" if flag else ""


def render_top_nav(current=None):
    """Menu atas: Home, Screeners (dropdown), Watchlist, Money, How To. Halaman aktif menyala."""
    current = current or st.session_state.get("current_page", "home")
    pages = get_pages()
    width = link_width_kwargs()
    labels = {key: (label, icon) for key, _, label, icon in BASE_PAGES}

    cols = st.columns([1, 1.35, 1, 1, 1, 1.6], vertical_alignment="center")

    def nav_link(col, key):
        label, icon = labels[key]
        with col:
            with keyed_container(f"znav_{key}{_active(current == key)}"):
                st.page_link(pages[key], label=label, icon=f":material/{icon}:", **width)

    nav_link(cols[0], "home")

    # ---- Screeners dropdown ----
    active_scr = current if current in SCREENER_KEYS else None
    pop_label = get_screener(active_scr)["name"] if active_scr else "Screeners"
    pop_kwargs = {"use_container_width": True}
    try:
        import inspect

        if "width" in inspect.signature(st.popover).parameters:
            pop_kwargs = {"width": "stretch"}
    except Exception:
        pass
    with cols[1]:
        with keyed_container(f"znav_screeners{_active(active_scr is not None)}"):
            with st.popover(pop_label, **pop_kwargs, **icon_kwargs("radar", "popover")):
                st.markdown(
                    f"""<div style="display:flex; justify-content:space-between; font-family:'Share Tech Mono', monospace; font-size:11px; font-weight:800; letter-spacing:1px; color:#00F3FF; margin-bottom:6px;">
<span>SCREENERS</span><span>{len(SCREENERS)} AVAILABLE</span></div>""",
                    unsafe_allow_html=True,
                )
                for s in SCREENERS:
                    is_on = s["key"] == active_scr
                    with keyed_container(f"zscr_{s['key']}{_active(is_on)}"):
                        st.page_link(
                            pages[s["key"]],
                            label=s["name"] + ("  ·  Active" if is_on else ""),
                            icon=f":material/{s['material']}:",
                            **width,
                        )
                        st.caption(f"{s['category']} · {s['desc']}")

    nav_link(cols[2], "watchlist")
    nav_link(cols[3], "money_management")
    nav_link(cols[4], "how_to")
