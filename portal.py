import streamlit as st

st.set_page_config(page_title="VACR Instructor Portal", layout="wide")

st.title("VACR Instructor Portal")
st.write("Welcome to the central access point for all VACR training tools.")

st.markdown("---")

# ---------------------------------------------------------
# LINKS TO APPS
# ---------------------------------------------------------

IMAGE_MANAGER_URL = "https://vacrquiz-blwkadwcl9xxgtbmzaz7nx.streamlit.app"
HOTLIST_MANAGER_URL = "https://vacrquiz-wwz4rhy3weunubu7scahad.streamlit.app"
QUIZ_URL = "https://vacrquiz-pfnbpvqtgumek3nrbfkhql.streamlit.app"

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📸 Image Manager")
    st.write("Add, remove, and manage aircraft images in the archive.")
    st.link_button("Open Image Manager", IMAGE_MANAGER_URL)

with col2:
    st.subheader("📝 Hotlist Manager")
    st.write("Create, edit, and manage VACR hotlists.")
    st.link_button("Open Hotlist Manager", HOTLIST_MANAGER_URL)

with col3:
    st.subheader("🎯 VACR Quiz")
    st.write("Run the aircraft recognition quiz.")
    st.link_button("Open Quiz App", QUIZ_URL)

st.markdown("---")

st.info("This portal provides unified access to all VACR instructor tools.")
