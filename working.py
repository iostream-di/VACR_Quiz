# ======================================================================
#  VACR (Visual Aircraft Recognition QUIZ) app
#  Author: David "Marty" Martinez (dmartinez61789@gmail.com / david.a.martinez291.mil@army.mil)
#  Purpose: Streamlit-based quiz app for students seeking to improve their VACR techniques.
#
#  Description:
#     This application provides a clean interface for students to:
#       • Test their profeciency identifying aircrafts
#       • Improve their quick recognition skills with varied difficulty settings
#       • Focus on specific category of aircrafts
#       • (Future) AI-assisted comparison summary of wrong answers at the end of the quiz
#
#  Notes:
#     • AI-assisted comparison summary only works with valid AI tokens.
#     • Slow bandwidth users might observe the timer elapsing before the image fully loads.
#
#  Version: 2.3 (cached images + safe reruns + desktop fit)
#  Last Updated: April 2026
# ======================================================================

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
import random
import time
from PIL import Image

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Marty's VACR QUIZ", layout="wide", page_icon="✈️")

# Global CSS
st.markdown("""
    <style>
    button:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    /* Make quiz images fit on desktop without scrolling */
    .stImage img {
        max-height: 80vh !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# VACR IMAGE SCALING + CACHED LOADER
# ---------------------------------------------------------
def scale_vacr_pil(img, max_w, max_h):
    w, h = img.size
    scale = min(max_w / w, max_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


@st.cache_resource
def load_and_scale_image(path_str, max_w=1600, max_h=900):
    """
    Cached image loader + scaler.
    - Avoids re-decoding and resizing on every autorefresh tick.
    - max_h tuned so desktop users don't have to scroll (plus CSS cap).
    """
    img = Image.open(path_str)
    return scale_vacr_pil(img, max_w, max_h)

# ---------------------------------------------------------
# LOAD HOTLIST FOLDERS
# ---------------------------------------------------------
def load_hotlist_folders():
    base = Path("hotlists")
    base.mkdir(exist_ok=True)

    files = [f.stem for f in base.glob("*.txt")]
    files.sort()
    return files

# ---------------------------------------------------------
# LOAD HOTLIST DATA
# ---------------------------------------------------------
def load_hotlist(name):
    hotlist_path = Path("hotlists") / f"{name}.txt"
    img_dir = Path("imgs")

    categories = {}
    with open(hotlist_path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            name, cat = line.strip().split("|", 1)
            categories[name.strip()] = cat.strip().capitalize()

    return categories, img_dir

# ---------------------------------------------------------
# LOAD IMAGES
# ---------------------------------------------------------
def load_images(img_dir, models):
    images = {}
    for model in models:
        safe = model.replace(" ", "_").replace("/", "_").lower()
        folder = img_dir / safe

        if folder.exists() and folder.is_dir():
            images[model] = sorted(folder.glob("*.*"))
        else:
            images[model] = []

    return images

# ---------------------------------------------------------
# QUIZ ENGINE
# ---------------------------------------------------------
class Quiz:
    def __init__(self, models, categories, images, num_q, difficulty, num_choices):
        self.models = models
        self.categories = categories
        self.images = images
        self.num_q = num_q
        self.num_choices = num_choices

        if difficulty == "Easy":
            self.image_time = 10
            self.choice_time = 15
        elif difficulty == "Warfighter":
            self.image_time = 3
            self.choice_time = 4
        elif difficulty == "AI":
            self.image_time = 1
            self.choice_time = 3
        else:
            self.image_time = 5
            self.choice_time = 5

        self.questions = random.sample(models, min(num_q, len(models)))
        while len(self.questions) < num_q:
            self.questions += random.sample(models, min(len(models), num_q - len(self.questions)))

        self.index = 0
        self.score = 0
        self.wrong = []
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
            wrong.extend(random.sample(pool, min(len(pool), remaining)))

        self.choices = wrong + [self.current_model]
        random.shuffle(self.choices)

        self.state = "image"

    def process_answer(self, answer):
        if answer == self.current_model:
            self.score += 1
        else:
            self.wrong.append((self.current_model, answer))

        self.index += 1
        self.next_question()

# ---------------------------------------------------------
# SCREEN 1 — MENU
# ---------------------------------------------------------
def screen_menu():
    st.title("Marty's VACR Quiz")

    hotlists = load_hotlist_folders()
    chosen = st.selectbox("Hotlist", hotlists)

    categories, _ = load_hotlist(chosen)

    unique_cats = sorted(set(categories.values()))

    st.subheader("Select Categories")
    cat_states = {}
    cols = st.columns(3)
    for i, cat in enumerate(unique_cats):
        with cols[i % 3]:
            cat_states[cat] = st.toggle(cat, value=True)

    filtered_models = [
        m for m, c in categories.items()
        if cat_states.get(c, False)
    ]

    max_aircraft = len(filtered_models)

    if max_aircraft == 0:
        st.error("No aircraft available with the selected categories.")
        return

    num_q = st.slider("Number of aircraft", 1, max_aircraft, min(20, max_aircraft))
    difficulty = st.selectbox("Difficulty", ["Easy", "Standard", "Warfighter", "AI"])
    num_choices = st.slider("Choices per question", 4, 6, 4)

    if st.button("Start Quiz"):
        st.session_state.screen = "quiz"
        st.session_state.quiz_settings = (chosen, num_q, difficulty, num_choices, cat_states)
        st.session_state.quiz = None
        st.session_state.phase_start = None
        st.session_state.last_state = None
        st.session_state.selected_choice = None
        st.rerun()

# ---------------------------------------------------------
# SCREEN 2 — QUIZ
# ---------------------------------------------------------
def screen_quiz():
    st_autorefresh(interval=1000, key="quiz_tick")

    if "quiz" not in st.session_state or st.session_state.quiz is None:
        chosen, num_q, difficulty, num_choices, cat_states = st.session_state.quiz_settings
        categories, img_dir = load_hotlist(chosen)

        models = [
            m for m, c in categories.items()
            if cat_states.get(c, False)
        ]

        images = load_images(img_dir, models)

        st.session_state.quiz = Quiz(models, categories, images, num_q, difficulty, num_choices)
        st.session_state.phase_start = None
        st.session_state.last_state = None
        st.session_state.selected_choice = None

    quiz = st.session_state.quiz

    if quiz.state != st.session_state.get("last_state"):
        st.session_state.phase_start = None
        st.session_state.last_state = quiz.state

    # IMAGE PHASE
    if quiz.state == "image":
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Look closely…")

        if quiz.current_image:
            img = load_and_scale_image(str(quiz.current_image), max_w=1600, max_h=900)
            # Let Streamlit handle width; CSS caps height
            st.image(img, use_column_width=True)
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
        return

    # CHOICES PHASE
    if quiz.state == "choices":
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Which one was it?")

        if st.session_state.phase_start is None:
            st.session_state.phase_start = time.time()

        selected = st.session_state.get("selected_choice")

        cols = st.columns(2)
        for i, choice in enumerate(quiz.choices):
            col = cols[i % 2]
            label = f"▶ {choice}" if choice == selected else choice

            if col.button(label, key=f"choice_{i}"):
                st.session_state.selected_choice = choice

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
        return

    if quiz.state == "finished":
        st.session_state.screen = "results"
        return

# ---------------------------------------------------------
# SCREEN 3 — RESULTS
# ---------------------------------------------------------
def screen_results():
    quiz = st.session_state.quiz

    st.header("Results")
    percent = (quiz.score / quiz.num_q) * 100
    st.subheader(f"Score: {quiz.score}/{quiz.num_q} ({percent:.1f}%)")

    if quiz.wrong:
        st.subheader("Incorrect Answers")
        for correct, chosen in quiz.wrong:
            shown = chosen if chosen is not None else "No answer"
            st.markdown(f"❌ **{shown} → {correct}**")
    else:
        st.success("Perfect score!")

    if st.button("Return to Menu"):
        st.session_state.screen = "menu"
        st.session_state.quiz = None
        st.session_state.phase_start = None
        st.session_state.last_state = None
        st.session_state.selected_choice = None
        st.rerun()

# ---------------------------------------------------------
# MAIN ROUTER
# ---------------------------------------------------------
if "screen" not in st.session_state:
    st.session_state.screen = "menu"

if st.session_state.screen == "menu":
    screen_menu()
elif st.session_state.screen == "quiz":
    screen_quiz()
elif st.session_state.screen == "results":
    screen_results()