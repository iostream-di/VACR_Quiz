# ======================================================================
#  HOTLIST MANAGER APPLICATION
#  Author: David "Marty" Martinez (dmartinez61789@gmail.com / david.a.martinez291.mil@army.mil)
#  Purpose: Streamlit-based tool for importing, editing, and exporting
#           VACR hotlists used in aircraft recognition training.
#
#  Description:
#     This application provides a clean interface for instructors to:
#       • Load existing hotlists from /hotlists/*.txt
#       • Import new hotlists from text files
#       • Add, edit, and remove aircraft/category entries
#       • Export updated hotlists back to .txt format
#
#     Hotlist Format:
#         Each line follows the structure:
#             <Aircraft Name>|<Category>
#
#     Example:
#         F-16C | Fighter
#         C-17A | Cargo
#         MQ-9 Reaper | UAV
#
#  Notes:
#     • This tool manages ONLY text-based hotlists.
#     • Image management is handled separately in the Image Manager app.
#     • All hotlists are stored in the /hotlists directory.
#
#  Version: 1.0
#  Last Updated: April 2026
# ======================================================================


import streamlit as st
from pathlib import Path
from PIL import Image
import shutil

st.set_page_config(page_title="Image Manager", layout="wide")

IMG_DIR = Path("imgs")
IMG_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def list_aircraft():
    aircraft = []
    for folder in IMG_DIR.iterdir():
        if folder.is_dir():
            name = folder.name.replace("_", " ").title()
            aircraft.append(name)
    return sorted(aircraft)

def safe_name(name):
    return name.replace(" ", "_").replace("/", "_").lower()

def get_aircraft_folder(name):
    return IMG_DIR / safe_name(name)

def load_images(name):
    folder = get_aircraft_folder(name)
    if not folder.exists():
        return [], folder
    return sorted(folder.glob("*.*")), folder

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
st.title("VACR: Aircraft Image Manager")

aircraft_list = list_aircraft()

col1, col2 = st.columns([3,1])

with col1:
    selected = st.selectbox("Select Aircraft", aircraft_list)

with col2:
    if st.button("➕ New Aircraft"):
        new_name = st.text_input("Enter new aircraft name:", key="new_aircraft_name")
        if new_name:
            folder = get_aircraft_folder(new_name)
            folder.mkdir(exist_ok=True)
            st.success(f"Created aircraft folder: {new_name}")
            st.rerun()

if not selected:
    st.stop()

# ---------------------------------------------------------
# SELECTED AIRCRAFT VIEW
# ---------------------------------------------------------
st.header(f"Images for: {selected}")

imgs, folder = load_images(selected)

# Delete aircraft
if st.button(f"🗑️ Delete Aircraft '{selected}'"):
    shutil.rmtree(folder)
    st.success(f"Deleted aircraft: {selected}")
    st.rerun()

# ---------------------------------------------------------
# IMAGE GRID
# ---------------------------------------------------------
if imgs:
    st.subheader("Existing Images")
    cols = st.columns(4)

    for i, img_path in enumerate(imgs):
        with cols[i % 4]:
            try:
                st.image(Image.open(img_path), width=150)
            except:
                st.warning("Invalid image file")

            if st.button("Delete", key=f"del_{i}"):
                img_path.unlink()
                st.rerun()
else:
    st.info("No images found for this aircraft.")

# ---------------------------------------------------------
# UPLOAD NEW IMAGES
# ---------------------------------------------------------
st.subheader("Add Images")

uploaded = st.file_uploader(
    "Upload one or more images",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png", "gif", "bmp", "webp"]
)

if uploaded:
    folder.mkdir(exist_ok=True)
    for file in uploaded:
        out = folder / file.name
        with open(out, "wb") as f:
            f.write(file.read())
    st.success("Images uploaded.")
    st.rerun()
