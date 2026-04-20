# ======================================================================
#  IMAGE MANAGER APPLICATION
#  Author: David "Marty" Martinez (dmartinez61789@gmail.com / david.a.martinez291.mil@army.mil)
#  Purpose: Streamlit-based tool for adding and removing images for
#           each aircraft in the image archive.
#
#  Description:
#     This application provides a clean interface for instructors to:
#       • Create new aircraft in the image archive
#       • Add images to that aircraft
#       • Remove Images from that aircraft
#
#     Image Format:
#         The following are supported image file types for the archive:
#         ".jpg", 
#
#  Notes:
#     • This tool manages ONLY images in the aircraft image archive.
#     • Hotlist management is handled separately in the Hotlist Manager app.
#     • All images are stored in the /imgs directory, inside the aircraft's name folder.
#
#  Version: 1.0
#  Last Updated: April 2026
# ======================================================================


import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Hotlist Manager", layout="wide")

HOTLIST_DIR = Path("hotlists")
HOTLIST_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# LOAD HOTLIST
# ---------------------------------------------------------
def load_hotlist(name):
    path = HOTLIST_DIR / f"{name}.txt"
    categories = {}

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            aircraft, cat = line.strip().split("|", 1)
            categories[aircraft.strip()] = cat.strip().capitalize()

    return categories

# ---------------------------------------------------------
# SAVE HOTLIST
# ---------------------------------------------------------
def save_hotlist(name, categories):
    path = HOTLIST_DIR / f"{name}.txt"
    with open(path, "w", encoding="utf-8") as f:
        for aircraft, cat in categories.items():
            f.write(f"{aircraft}|{cat}\n")

# ---------------------------------------------------------
# MAIN UI
# ---------------------------------------------------------
st.title("✈️ Hotlist Manager (Import / Modify / Export)")

# ---------------------------------------------------------
# HOTLIST SELECTION
# ---------------------------------------------------------
hotlists = sorted([f.stem for f in HOTLIST_DIR.glob("*.txt")])

col1, col2 = st.columns([3,1])

with col1:
    selected = st.selectbox("Select Hotlist", hotlists)

with col2:
    if st.button("➕ New Hotlist"):
        new_name = st.text_input("Enter new hotlist name:", key="new_hotlist_name")
        if new_name:
            save_hotlist(new_name, {})
            st.success(f"Created hotlist: {new_name}")
            st.rerun()

if not selected:
    st.stop()

categories = load_hotlist(selected)

# ---------------------------------------------------------
# IMPORT HOTLIST
# ---------------------------------------------------------
st.subheader("Import Hotlist")

uploaded = st.file_uploader("Upload a .txt hotlist file", type=["txt"])

if uploaded:
    text = uploaded.read().decode("utf-8")
    new_cats = {}

    for line in text.splitlines():
        if "|" not in line:
            continue
        aircraft, cat = line.strip().split("|", 1)
        new_cats[aircraft.strip()] = cat.strip().capitalize()

    categories = new_cats
    save_hotlist(selected, categories)
    st.success("Hotlist imported successfully.")
    st.rerun()

# ---------------------------------------------------------
# MODIFY HOTLIST
# ---------------------------------------------------------
st.header(f"Editing: {selected}")

# Add new aircraft
with st.expander("➕ Add Aircraft"):
    new_aircraft = st.text_input("Aircraft Name")
    new_category = st.text_input("Category")

    if st.button("Add Aircraft"):
        if new_aircraft and new_category:
            categories[new_aircraft] = new_category.capitalize()
            save_hotlist(selected, categories)
            st.success("Aircraft added.")
            st.rerun()

# Edit existing aircraft
for aircraft in list(categories.keys()):
    with st.expander(aircraft):
        colA, colB = st.columns([3,1])

        with colA:
            new_cat = st.text_input(
                f"Category for {aircraft}",
                value=categories[aircraft],
                key=f"cat_{aircraft}"
            )

            if st.button(f"Save {aircraft}", key=f"save_{aircraft}"):
                categories[aircraft] = new_cat.capitalize()
                save_hotlist(selected, categories)
                st.success("Updated.")
                st.rerun()

        with colB:
            if st.button(f"❌ Delete {aircraft}", key=f"del_{aircraft}"):
                del categories[aircraft]
                save_hotlist(selected, categories)
                st.success("Deleted.")
                st.rerun()

# ---------------------------------------------------------
# EXPORT HOTLIST
# ---------------------------------------------------------
st.subheader("Export Hotlist")

st.download_button(
    label="💾 Download hotlist.txt",
    data=open(HOTLIST_DIR / f"{selected}.txt", "rb").read(),
    file_name=f"{selected}.txt",
    mime="text/plain"
)
