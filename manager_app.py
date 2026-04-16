import streamlit as st
import os
import shutil
import zipfile
import string
from pathlib import Path
from PIL import Image

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="VACR Hotlist Manager", layout="wide")

BASE_DIR = Path("hotlists")
BASE_DIR.mkdir(exist_ok=True)

CATEGORIES = [
    "Fighter", "Bomber", "Attack", "Transport", "Tanker",
    "Helicopter", "UAV", "Trainer", "Reconnaissance",
    "Civilian", "Other"
]

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def safe_name(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_").lower()

def load_hotlist(path: Path):
    data = {}
    file = path / "hotlist.txt"
    if not file.exists():
        return data
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            name, cat = line.strip().split("|", 1)
            data[name.strip()] = cat.strip()
    return data

def save_hotlist(path: Path, data: dict):
    with open(path / "hotlist.txt", "w", encoding="utf-8") as f:
        for name, cat in data.items():
            f.write(f"{name} | {cat}\n")

def export_hotlist(path: Path):
    zip_path = f"{path.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(path / "hotlist.txt", arcname=f"{path.name}/hotlist.txt")
        img_dir = path / "imgs"
        for file in img_dir.iterdir():
            z.write(file, arcname=f"{path.name}/imgs/{file.name}")
    return zip_path

def import_hotlist(zip_file):
    with zipfile.ZipFile(zip_file, "r") as z:
        root_folder = z.namelist()[0].split("/")[0]
        target = BASE_DIR / root_folder
        if target.exists():
            shutil.rmtree(target)
        z.extractall(BASE_DIR)
    return root_folder

# ---------------------------------------------------------
# UI: HOTLIST SELECTION
# ---------------------------------------------------------
st.title("✈️ VACR Hotlist Manager")

hotlists = sorted([p.name for p in BASE_DIR.iterdir() if p.is_dir()])

col1, col2, col3 = st.columns([2,1,1])

with col1:
    selected_hotlist = st.selectbox("Select Hotlist", hotlists)

with col2:
    if st.button("Create New Hotlist"):
        new_name = st.text_input("Enter new hotlist name:", key="new_hotlist_name")
        if new_name:
            path = BASE_DIR / new_name
            path.mkdir(exist_ok=True)
            (path / "imgs").mkdir(exist_ok=True)
            save_hotlist(path, {})
            st.success(f"Created hotlist: {new_name}")
            st.rerun()

with col3:
    uploaded_zip = st.file_uploader("Import Hotlist (.zip)", type=["zip"])
    if uploaded_zip:
        name = import_hotlist(uploaded_zip)
        st.success(f"Imported hotlist: {name}")
        st.rerun()

if not selected_hotlist:
    st.stop()

hotlist_path = BASE_DIR / selected_hotlist
imgs_path = hotlist_path / "imgs"
imgs_path.mkdir(exist_ok=True)

hotlist = load_hotlist(hotlist_path)

# ---------------------------------------------------------
# UI: HOTLIST MANAGER
# ---------------------------------------------------------
st.header(f"Managing Hotlist: {selected_hotlist}")

left, right = st.columns([1,2])

# ---------------- LEFT PANE ----------------
with left:
    st.subheader("Aircraft List")

    aircraft_list = sorted(hotlist.keys())
    selected_aircraft = st.selectbox("Select Aircraft", ["(None)"] + aircraft_list)

    st.markdown("---")

    # Add aircraft
    new_ac_name = st.text_input("Add Aircraft")
    new_ac_cat = st.selectbox("Category", CATEGORIES, key="new_ac_cat")
    if st.button("Add"):
        if new_ac_name:
            hotlist[new_ac_name] = new_ac_cat
            save_hotlist(hotlist_path, hotlist)
            st.rerun()

    # Delete aircraft
    if selected_aircraft != "(None)" and st.button("Delete Aircraft"):
        del hotlist[selected_aircraft]
        save_hotlist(hotlist_path, hotlist)
        # Remove images
        prefix = safe_name(selected_aircraft)
        for f in imgs_path.iterdir():
            if f.name.startswith(prefix + "__"):
                f.unlink()
        st.rerun()

    st.markdown("---")

    # Export hotlist
    if st.button("Export Hotlist (.zip)"):
        zip_path = export_hotlist(hotlist_path)
        with open(zip_path, "rb") as f:
            st.download_button("Download Export", f, file_name=zip_path)
        os.remove(zip_path)

# ---------------- RIGHT PANE ----------------
with right:
    st.subheader("Aircraft Details")

    if selected_aircraft == "(None)":
        st.info("Select an aircraft to edit.")
        st.stop()

    # Editable fields
    new_name = st.text_input("Name", selected_aircraft)
    new_cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(hotlist[selected_aircraft]))

    if st.button("Save Changes"):
        if new_name != selected_aircraft:
            # rename images
            old_safe = safe_name(selected_aircraft)
            new_safe = safe_name(new_name)
            for f in imgs_path.iterdir():
                if f.name.startswith(old_safe + "__"):
                    new_file = f.name.replace(old_safe, new_safe, 1)
                    f.rename(imgs_path / new_file)
            # update hotlist
            del hotlist[selected_aircraft]
            hotlist[new_name] = new_cat
        else:
            hotlist[selected_aircraft] = new_cat

        save_hotlist(hotlist_path, hotlist)
        st.success("Saved.")
        st.rerun()

    st.markdown("---")

    # ---------------- IMAGES ----------------
    st.subheader("Images")

    # Upload images
    uploaded_imgs = st.file_uploader("Add Images", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)
    if uploaded_imgs:
        sname = safe_name(new_name)
        existing = [f.name for f in imgs_path.iterdir() if f.name.startswith(sname + "__")]
        used = {f.split("__")[1].split(".")[0] for f in existing}
        alphabet = list(string.ascii_lowercase)
        available = [c for c in alphabet if c not in used]

        for i, file in enumerate(uploaded_imgs):
            if i >= len(available):
                st.error("Ran out of suffix letters.")
                break
            letter = available[i]
            ext = os.path.splitext(file.name)[1]
            out = imgs_path / f"{sname}__{letter}{ext}"
            with open(out, "wb") as f:
                f.write(file.read())

        st.success("Images added.")
        st.rerun()

    # List images
    image_files = sorted([f for f in imgs_path.iterdir() if f.name.startswith(safe_name(new_name) + "__")])

    if image_files:
        selected_img = st.selectbox("Select Image", [f.name for f in image_files])
        img_path = imgs_path / selected_img

        # Preview
        img = Image.open(img_path)
        st.image(img, caption=selected_img, use_column_width=True)

        # Delete image
        if st.button("Delete Image"):
            img_path.unlink()
            st.rerun()
    else:
        st.info("No images for this aircraft.")
