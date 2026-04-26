# ======================================================================
#  VACR (Visual Aircraft Recognition TEST) app
#  Author: David "Marty" Martinez (dmartinez61789@gmail.com / david.a.martinez291.mil@army.mil)
#  Purpose: Streamlit-based test app for instructors to use as an official VACR test.
#
#  Description:
#     This application provides a clean interface for:
#       • Students to test their profeciency identifying aircrafts
#       • Instructors to host their VACR hotlist exam.
#
#  Notes:
#     • Slow bandwidth users might observe the timer elapsing before the image fully loads.
#
#  Version: 1.0
#  Last Updated: April 2026
# ======================================================================

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
import random
import time
from PIL import Image
import base64
import requests

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="VACR TEST", layout="wide", page_icon="📝")

st.markdown("""
    <style>
    button:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# IMAGE SCALING
# ---------------------------------------------------------
def scale_vacr_pil(img, max_w, max_h):
    w, h = img.size
    scale = min(max_w / w, max_h / h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

# ---------------------------------------------------------
# LOAD HOTLIST
# ---------------------------------------------------------
def load_hotlist(name):
    hotlist_path = Path("hotlists") / f"{name}.txt"
    img_dir = Path("imgs")

    categories = {}
    with open(hotlist_path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            model, cat = line.strip().split("|", 1)
            categories[model.strip()] = cat.strip().capitalize()

    return categories, img_dir

# ---------------------------------------------------------
# LOAD IMAGES
# ---------------------------------------------------------
def load_images(img_dir, models):
    images = {}
    for model in models:
        safe = model.replace(" ", "_").replace("/", "_").lower()
        folder = img_dir / safe
        images[model] = sorted(folder.glob("*.*")) if folder.exists() else []
    return images

# ---------------------------------------------------------
# QUIZ ENGINE
# ---------------------------------------------------------
class Quiz:
    def __init__(self, models, categories, images):
        self.models = models
        self.categories = categories
        self.images = images
        self.num_q = len(models)
        self.num_choices = 4

        # Standard difficulty
        self.image_time = 5
        self.choice_time = 5

        self.questions = random.sample(models, len(models))
        self.index = 0
        self.score = 0
        self.state = "image"

        self.current_model = None
        self.current_image = None
        self.choices = []

        self.next_question()

    def next_question(self):
        if self.index >= self.num_q:
            self.state = "finished"
            return

        self.current_model = self.questions[self.index]
        img_list = self.images.get(self.current_model, [])
        self.current_image = random.choice(img_list) if img_list else None

        cat = self.categories[self.current_model]
        others = [m for m in self.models if m != self.current_model]
        same_cat = [m for m in others if self.categories[m] == cat]

        wrong = []
        need = self.num_choices - 1

        take_same = min(len(same_cat), need)
        wrong.extend(random.sample(same_cat, take_same))

        remaining = need - take_same
        if remaining > 0:
            pool = [m for m in others if m not in wrong]
            wrong.extend(random.sample(pool, remaining))

        self.choices = wrong + [self.current_model]
        random.shuffle(self.choices)

        self.state = "image"

    def process_answer(self, answer):
        if answer == self.current_model:
            self.score += 1
        self.index += 1
        self.next_question()

# ---------------------------------------------------------
# GITHUB CSV APPEND
# ---------------------------------------------------------
def append_to_github_csv(class_num, rank, name, score):
    repo = st.secrets["GITHUB_REPO"]
    token = st.secrets["GITHUB_TOKEN"]
    path = f"test/{class_num}.csv"

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        sha = data["sha"]
        content = base64.b64decode(data["content"]).decode("utf-8")
    else:
        sha = None
        content = "class,rank,name,score\n"

    new_row = f"{class_num},{rank},{name},{score}\n"
    updated = content + new_row
    encoded = base64.b64encode(updated.encode()).decode()

    payload = {
        "message": f"Add test result for {name}",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=headers, json=payload)

# ---------------------------------------------------------
# SCREEN: ADMIN
# ---------------------------------------------------------
def screen_admin():
    st.title("VACR TEST")

    results_dir = Path("test")
    results_dir.mkdir(exist_ok=True)

    csv_files = sorted([f.name for f in results_dir.glob("*.csv")])
    class_numbers = [f.replace(".csv", "") for f in csv_files]

    if not class_numbers:
        st.error("No class CSV files found in /test.")
        return

    class_num = st.selectbox("Class Number", class_numbers)
    rank = st.text_input("Rank")
    name = st.text_input("Name")

    if st.button("Begin Test"):
        if not rank or not name:
            st.error("Please enter rank and name.")
            return

        st.session_state.test_info = {
            "class": class_num,
            "rank": rank.strip(),
            "name": name.strip()
        }

        # Load default hotlist (first one)
        hotlists = sorted([f.stem for f in Path("hotlists").glob("*.txt")])
        chosen = hotlists[0]

        categories, img_dir = load_hotlist(chosen)
        models = list(categories.keys())
        images = load_images(img_dir, models)

        st.session_state.quiz = Quiz(models, categories, images)
        st.session_state.screen = "quiz"
        st.session_state.phase_start = None
        st.session_state.last_state = None
        st.session_state.selected_choice = None
        st.rerun()

# ---------------------------------------------------------
# SCREEN: QUIZ
# ---------------------------------------------------------
def screen_quiz():
    st_autorefresh(interval=1000, key="tick_test")

    quiz = st.session_state.quiz

    if quiz.state != st.session_state.get("last_state"):
        st.session_state.phase_start = None
        st.session_state.last_state = quiz.state

    # IMAGE PHASE
    if quiz.state == "image":
        st.subheader("Look closely…")

        if quiz.current_image:
            img = Image.open(quiz.current_image)
            img = scale_vacr_pil(img, 1600, 900)
            st.image(img)
        else:
            st.warning("No image found")

        if st.session_state.phase_start is None:
            st.session_state.phase_start = time.time()

        elapsed = time.time() - st.session_state.phase_start
        remaining = quiz.image_time - elapsed
        st.progress(max(0.0, remaining) / quiz.image_time)

        if remaining <= 0:
            quiz.state = "choices"
            st.session_state.phase_start = None
            st.session_state.selected_choice = None
            st.rerun()
        return

    # CHOICES PHASE
    if quiz.state == "choices":
        st.subheader("Which one was it?")

        if st.session_state.phase_start is None:
            st.session_state.phase_start = time.time()

        selected = st.session_state.get("selected_choice")

        cols = st.columns(2)
        for i, choice in enumerate(quiz.choices):
            col = cols[i % 2]
            label = f"▶ {choice}" if choice == selected else choice

            if col.button(label, key=f"choice_{i}"):
                st.session_state.selected_choice = choice
                st.rerun()

        elapsed = time.time() - st.session_state.phase_start
        remaining = quiz.choice_time - elapsed
        st.progress(max(0.0, remaining) / quiz.choice_time)

        if remaining <= 0:
            final_answer = st.session_state.get("selected_choice")
            quiz.process_answer(final_answer)
            st.session_state.selected_choice = None
            st.session_state.phase_start = None

            if quiz.state == "finished":
                st.session_state.screen = "results"
                st.rerun()
            else:
                st.rerun()
        return

# ---------------------------------------------------------
# SCREEN: RESULTS
# ---------------------------------------------------------
def screen_results():
    quiz = st.session_state.quiz
    info = st.session_state.test_info

    st.header("Test Complete")

    percent = (quiz.score / quiz.num_q) * 100
    st.subheader(f"Score: {quiz.score}/{quiz.num_q} ({percent:.1f}%)")

    append_to_github_csv(
        info["class"],
        info["rank"],
        info["name"],
        quiz.score
    )

    st.success("Your score has been recorded.")

    col1, col2 = st.columns(2)
    if col1.button("Return to Menu"):
        st.session_state.screen = "admin"
        st.session_state.quiz = None
        st.rerun()

    if col2.button("Quit"):
        st.stop()

# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------
if "screen" not in st.session_state:
    st.session_state.screen = "admin"

if st.session_state.screen == "admin":
    screen_admin()
elif st.session_state.screen == "quiz":
    screen_quiz()
elif st.session_state.screen == "results":
    screen_results()
