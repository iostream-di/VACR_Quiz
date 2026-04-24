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
#  Version: 1.2
#  Last Updated: April 2026
#
#  Changelog:
#  1.2 - UI shows count of aircraft total, and by type.
#  1.1 - Locked in categories to prevent typos in a freetext field.
# ======================================================================

import streamlit as st
import base64
import requests

st.set_page_config(page_title="Hotlist Manager", layout="wide")

ALLOWED_CATEGORIES = [
    "Fighter",
    "Bomber",
    "Transport",
    "Helicopter",
    "Recon",
    "UAV",
]

# ---------------------------------------------------------
# GitHub Configuration
# ---------------------------------------------------------
TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]
BRANCH = st.secrets["GITHUB_BRANCH"]

HOTLIST_PATH = "hotlists"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ---------------------------------------------------------
# GitHub Helpers
# ---------------------------------------------------------
def github_file_url(name):
    return f"https://api.github.com/repos/{REPO}/contents/{HOTLIST_PATH}/{name}.txt"

def github_list_hotlists():
    """Return list of hotlist names from GitHub."""
    url = f"https://api.github.com/repos/{REPO}/contents/{HOTLIST_PATH}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    return sorted([item["name"].replace(".txt", "") for item in r.json() if item["name"].endswith(".txt")])

def github_load_hotlist(name):
    """Load hotlist text from GitHub."""
    url = github_file_url(name)
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return {}

    content = base64.b64decode(r.json()["content"]).decode("utf-8")

    categories = {}
    for line in content.splitlines():
        if "|" not in line:
            continue
        aircraft, cat = line.strip().split("|", 1)
        categories[aircraft.strip()] = cat.strip().capitalize()

    return categories

def github_save_hotlist(name, categories):
    """Create or update a hotlist in GitHub."""
    url = github_file_url(name)

    # Convert dict to text
    text = "\n".join(f"{ac}|{cat}" for ac, cat in categories.items())
    encoded = base64.b64encode(text.encode()).decode()

    # Check if file exists
    check = requests.get(url, headers=HEADERS)

    if check.status_code == 200:
        sha = check.json()["sha"]
        payload = {
            "message": f"Update hotlist {name}",
            "content": encoded,
            "branch": BRANCH,
            "sha": sha
        }
    else:
        payload = {
            "message": f"Add hotlist {name}",
            "content": encoded,
            "branch": BRANCH
        }

    return requests.put(url, json=payload, headers=HEADERS)

def github_delete_hotlist(name):
    """Delete a hotlist from GitHub."""
    url = github_file_url(name)
    check = requests.get(url, headers=HEADERS)

    if check.status_code != 200:
        return

    sha = check.json()["sha"]

    payload = {
        "message": f"Delete hotlist {name}",
        "sha": sha,
        "branch": BRANCH
    }

    requests.delete(url, json=payload, headers=HEADERS)

# ---------------------------------------------------------
# MAIN UI
# ---------------------------------------------------------
st.title("VACR: Hotlist Manager (GitHub‑Backed)")

# ---------------------------------------------------------
# HOTLIST SELECTION
# ---------------------------------------------------------
hotlists = github_list_hotlists()

col1, col2 = st.columns([3,1])

with col1:
    selected = st.selectbox("Select Hotlist", hotlists)

with col2:
    new_name = st.text_input("➕ New Hotlist Name")
    if st.button("Create Hotlist"):
        if new_name:
            github_save_hotlist(new_name, {})
            st.success(f"Created hotlist: {new_name}")
            st.rerun()

if not selected:
    st.stop()

categories = github_load_hotlist(selected)

# ---------------------------------------------------------
# CATEGORY SUMMARY
# ---------------------------------------------------------
st.subheader("Category Summary")

cat_counts = {}
for ac, cat in categories.items():
    cat_counts[cat] = cat_counts.get(cat, 0) + 1

total_count = sum(cat_counts.values())

cols = st.columns(3)
i = 0
for cat, count in sorted(cat_counts.items()):
    with cols[i % 3]:
        st.metric(label=cat, value=count)
    i += 1

st.metric(label="Total Aircraft", value=total_count)

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

    github_save_hotlist(selected, new_cats)
    st.success("Hotlist imported successfully.")
    st.rerun()

# ---------------------------------------------------------
# MODIFY HOTLIST
# ---------------------------------------------------------
st.header(f"Editing: {selected}")

# Add new aircraft
with st.expander("➕ Add Aircraft"):
    new_aircraft = st.text_input("Aircraft Name")

    new_category = st.selectbox(
        "Category",
        ALLOWED_CATEGORIES,
        key="add_cat"
    )

    if st.button("Add Aircraft"):
        if new_aircraft:
            categories[new_aircraft] = new_category
            github_save_hotlist(selected, categories)
            st.success("Aircraft added.")
            st.rerun()

# Edit existing aircraft
for aircraft in list(categories.keys()):
    with st.expander(aircraft):
        colA, colB = st.columns([3,1])

        with colA:
            new_cat = st.selectbox(
                f"Category for {aircraft}",
                ALLOWED_CATEGORIES,
                index=ALLOWED_CATEGORIES.index(categories[aircraft])
                    if categories[aircraft] in ALLOWED_CATEGORIES else 0,
                key=f"cat_{aircraft}"
            )

            if st.button(f"Save {aircraft}", key=f"save_{aircraft}"):
                categories[aircraft] = new_cat
                github_save_hotlist(selected, categories)
                st.success("Updated.")
                st.rerun()

        with colB:
            if st.button(f"❌ Delete {aircraft}", key=f"del_{aircraft}"):
                del categories[aircraft]
                github_save_hotlist(selected, categories)
                st.success("Deleted.")
                st.rerun()

# ---------------------------------------------------------
# EXPORT HOTLIST
# ---------------------------------------------------------
st.subheader("Export Hotlist")

export_text = "\n".join(f"{ac}|{cat}" for ac, cat in categories.items())

st.download_button(
    label="💾 Download hotlist",
    data=export_text,
    file_name=f"{selected}.txt",
    mime="text/plain"
)
