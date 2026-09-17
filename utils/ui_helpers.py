import streamlit as st


def load_css():
    """Injects global CSS styles including uniform cyan neon buttons across all tabs."""
    st.markdown(
        """
        <style>
        /* ==========================================
           GLOBAL BUTTON STYLING (CYAN NEON GLOW)
           ========================================== */
        div.stButton > button {
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 8px rgba(0, 243, 255, 0.3) !important;
            border-radius: 6px !important;
            transition: all 0.25s ease-in-out !important;
        }

        div.stButton > button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, #00b4d8 0%, #00f3ff 100%) !important;
            color: #020617 !important;
            font-weight: 700 !important;
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.6) !important;
        }

        div.stButton > button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(135deg, #00f3ff 0%, #10b981 100%) !important;
            color: #000000 !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.9), 0 0 10px rgba(16, 185, 129, 0.8) !important;
        }

        div.stButton > button:hover {
            border-color: #00F3FF !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.8) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
