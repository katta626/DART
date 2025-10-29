from streamlit.components.v1 import html
import streamlit as st

st.sidebar.image("https://picsum.photos/200")

import streamlit as st
from streamlit.components.v1 import html
import streamlit as st

st.markdown(
    """
    <style>
    /* Custom header decoration styles */
    header[data-testid="stHeader"] div[data-testid="stDecoration"] {
        color: rgb(255, 255, 255) !important;
        background-color: rgb(32, 32, 32) !important;
        font-weight: bold !important;
        font-size: 18px !important;
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        height: 3rem !important;
        padding: 0 1rem !important;
        left: 0 !important;
        right: 200px !important;
        position: absolute !important;
        overflow: hidden !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
    }
    </style>
    <script>
    const observer = new MutationObserver(() => {
        const header = window.parent.document.querySelector('header[data-testid="stHeader"]');
        if (!header) return;

        const decoration = header.querySelector('div[data-testid="stDecoration"]');
        if (!decoration) return;

        decoration.innerText = "Welcome, Streamlit App!";

        observer.disconnect();
    });

    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
    """,
    unsafe_allow_html=True,
)


