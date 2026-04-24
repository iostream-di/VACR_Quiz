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
import base64
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Image Manager", layout="wide")

# ---------------------------------------------------------
# GitHub Configuration
# ---------------------------------------------------------
TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]
BRANCH = st.secrets["GITHUB_BRANCH"]
IMG_PATH = st.secrets["GITHUB_IMG_PATH"]   # "imgs"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ---------------------------------------------------------
# GitHub API Helpers
# ---------------------------------------------------------
def safe_name(name):
    return name.replace(" ", "_").replace("/", "_").lower()

def github_folder_path(aircraft):
    return f"{IMG_PATH}/{safe_name(aircraft)}"

def github_list_aircraft():
    """List aircraft folders from GitHub."""
    url = f"https://api.github.com/repos/{REPO}/contents/{IMG_PATH}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    folders = []
    for item in r.json():
        if item["type"] == "dir":
            folders.append(item["name"].replace("_", " ").title())

    return sorted(folders)

def github_list_images(aircraft):
    """List images inside an aircraft folder."""
    url = f"https://api.github.com/repos/{REPO}/contents/{github_folder_path(aircraft)}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    return r.json()

def github_create_folder_if_missing(aircraft):
    """GitHub auto‑creates folders when uploading files, so no action needed."""
    pass

def github_upload_image(aircraft, filename, file_bytes):
    """Upload image to GitHub."""
    encoded = base64.b64encode(file_bytes).decode()
    path = f"{github_folder_path(aircraft)}/{filename}"

    url = f"https://api.github.com/repos/{REPO}/contents/{path}"

    payload = {
        "message": f"Add {filename}",
        "content": encoded,
        "branch": BRANCH
    }

    return requests.put(url, json=payload, headers=HEADERS)

def github_delete_image(path, sha):
    """Delete an image from GitHub."""
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"

    payload = {
        "message": f"Delete {path}",
        "sha": sha,
        "branch": BRANCH
    }

    return requests.delete(url, json=payload, headers=HEADERS)

def github_delete_aircraft(aircraft):
    """Delete entire aircraft folder by deleting each file."""
    images = github_list_images(aircraft)
    for img in images:
        github_delete_image(img["path"], img["sha"])

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
st.title("VACR: Aircraft Image Manager (GitHub‑Backed)")

aircraft_list = github_list_aircraft()

col1, col2 = st.columns([3,1])

with col1:
    selected = st.selectbox("Select Aircraft", aircraft_list)

with col2:
    new_name = st.text_input("➕ New Aircraft Name")
    if st.button("Create Aircraft"):
        if new_name:
            # Upload a dummy .gitkeep to create folder
            github_upload_image(new_name, ".gitkeep", b"")
            st.success(f"Created aircraft folder: {new_name}")
            st.rerun()

if not selected:
    st.stop()

# ---------------------------------------------------------
# SELECTED AIRCRAFT VIEW
# ---------------------------------------------------------
st.header(f"Images for: {selected}")

# Delete aircraft
if st.button(f"🗑️ Delete Aircraft '{selected}'"):
    github_delete_aircraft(selected)
    st.success(f"Deleted aircraft: {selected}")
    st.rerun()

# ---------------------------------------------------------
# IMAGE GRID
# ---------------------------------------------------------
st.subheader("Existing Images")

images = github_list_images(selected)

if images:
    cols = st.columns(4)

    for i, img in enumerate(images):
        name = img["name"]
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
            continue

        with cols[i % 4]:
            st.image(img["download_url"], width=150, caption=name)

            if st.button("Delete", key=f"del_{i}"):
                github_delete_image(img["path"], img["sha"])
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
    for file in uploaded:
        file_bytes = file.read()
        result = github_upload_image(selected, file.name, file_bytes)

        if result.status_code in [200, 201]:
            st.success(f"Uploaded {file.name}")
        else:
            st.error(f"Failed to upload {file.name}: {result.text}")

    st.rerun()
