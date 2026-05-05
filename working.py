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
#  Last Updated: may 2026
# ======================================================================

import streamlit as st
from pathlib import Path
import random
import time
from PIL import Image
from io import BytesIO
import base64

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="VACR QUIZ", layout="wide", page_icon="✈️")

# ---------------------------------------------------------
# GLOBAL CSS
# ---------------------------------------------------------
st.markdown("""
<style>
.timer-box {
    position: absolute;
    top: 10px;
    right: 20px;
    font-size: 32px;
    font-weight: 600;
}
.vacr-img {
    max-height: 80vh;
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TICK ENGINE (E1)
# ---------------------------------------------------------
if "tick" not in st.session_state:
    st.session_state.tick = 0

# This widget forces rerun because its value changes every run
st.session_state.tick += 1
st.number_input(" ", value=st.session_state.tick, key="tickbox")

# ---------------------------------------------------------
# IMAGE CACHE
# ---------------------------------------------------------
@st.cache_resource
def get_cached_image_html(path_str):
    img = Image.open(path_str)
    w, h = img.size
    scale = min(1600 / w, 900 / h)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return f"<img class='vacr-img' src='data:image/png;base64,{b64}' />"

# ---------------------------------------------------------
# LOAD HOTLISTS
# ---------------------------------------------------------
def load_hotlist_folders():
    base = Path("hotlists")
    base.mkdir(exist_ok=True)
    return sorted([f.stem for f in base.glob("*.txt")])

def load_hotlist(name):
    categories = {}
    with open(Path("hotlists") / f"{name}.txt", "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                model, cat = line.strip().split("|", 1)
                categories[model] = cat.capitalize()
    return categories, Path("imgs")

def load_images(img_dir, models):
    images = {}
    for m in models:
        safe = m.replace(" ", "_").replace("/", "_").lower()
        folder = img_dir / safe
        images[m] = sorted(folder.glob("*.*")) if folder.exists() else []
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
        self.phase_start = time.time()

        self.next_question()

    def next_question(self):
        if self.index >= self.num_q:
            self.state = "finished"
            return

        self.current_model = self.questions[self.index]
        imgs = self.images.get(self.current_model, [])
        self.current_image = random.choice(imgs) if imgs else None

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
        self.phase_start = time.time()

    def process_answer(self, answer):
        if answer == self.current_model:
            self.score += 1
        else:
            self.wrong.append((self.current_model, answer))
        self.index += 1
        self.next_question()

# ---------------------------------------------------------
# MENU
# ---------------------------------------------------------
def screen_menu():
    st.title("VACR QUIZ")

    hotlists = load_hotlist_folders()
    chosen = st.selectbox("Hotlist", hotlists)

    categories, _ = load_hotlist(chosen)
    unique_cats = sorted(set(categories.values()))

    st.subheader("Select Categories")
    cat_states = {c: st.toggle(c, value=True) for c in unique_cats}

    models = [m for m, c in categories.items() if cat_states[c]]
    if not models:
        st.error("No aircraft available.")
        return

    num_q = st.slider("Number of aircraft", 1, len(models), min(20, len(models)))
    difficulty = st.selectbox("Difficulty", ["Easy", "Standard", "Warfighter", "AI"], index=1)
    num_choices = st.slider("Choices per question", 4, 6, 4)

    if st.button("Start Quiz"):
        st.session_state.screen = "quiz"
        st.session_state.quiz_settings = (chosen, num_q, difficulty, num_choices, cat_states)
        st.session_state.quiz = None
        st.session_state.selected_choice = None
        st.rerun()

# ---------------------------------------------------------
# QUIZ
# ---------------------------------------------------------
def screen_quiz():
    if "quiz" not in st.session_state or st.session_state.quiz is None:
        chosen, num_q, difficulty, num_choices, cat_states = st.session_state.quiz_settings
        categories, img_dir = load_hotlist(chosen)
        models = [m for m, c in categories.items() if cat_states[c]]
        images = load_images(img_dir, models)
        st.session_state.quiz = Quiz(models, categories, images, num_q, difficulty, num_choices)
        st.session_state.selected_choice = None

    quiz = st.session_state.quiz
    now = time.time()
    elapsed = now - quiz.phase_start

    # IMAGE PHASE
    if quiz.state == "image":
        remaining = quiz.image_time - int(elapsed)
        if remaining < 0:
            remaining = 0

        st.markdown(f"<div class='timer-box'>{remaining}s</div>", unsafe_allow_html=True)
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Look closely…")

        if quiz.current_image:
            st.markdown(get_cached_image_html(str(quiz.current_image)), unsafe_allow_html=True)
        else:
            st.warning("No image found")

        if remaining <= 0:
            quiz.state = "choices"
            quiz.phase_start = time.time()
            st.session_state.selected_choice = None
            st.rerun()

        return

    # CHOICE PHASE
    if quiz.state == "choices":
        remaining = quiz.choice_time - int(elapsed)
        if remaining < 0:
            remaining = 0

        st.markdown(f"<div class='timer-box'>{remaining}s</div>", unsafe_allow_html=True)
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Which one was it?")

        selected = st.session_state.get("selected_choice")

        cols = st.columns(2)
        for i, choice in enumerate(quiz.choices):
            col = cols[i % 2]
            label = f"▶ {choice}" if choice == selected else choice
            if col.button(label, key=f"choice_{quiz.index}_{i}"):
                st.session_state.selected_choice = choice
                st.rerun()

        if remaining <= 0:
            quiz.process_answer(st.session_state.get("selected_choice"))
            st.session_state.selected_choice = None

            if quiz.state == "finished":
                st.session_state.screen = "results"

            st.rerun()

        return

# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------
def screen_results():
    quiz = st.session_state.quiz
    st.header("Results")

    pct = (quiz.score / quiz.num_q) * 100
    st.subheader(f"Score: {quiz.score}/{quiz.num_q} ({pct:.1f}%)")

    if quiz.wrong:
        st.subheader("Incorrect Answers")
        for correct, chosen in quiz.wrong:
            chosen = chosen if chosen else "No answer"
            st.write(f"❌ {chosen} → {correct}")
    else:
        st.success("Perfect score!")

    if st.button("Return to Menu"):
        st.session_state.screen = "menu"
        st.session_state.quiz = None
        st.session_state.selected_choice = None
        st.rerun()

# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------
if "screen" not in st.session_state:
    st.session_state.screen = "menu"

if st.session_state.screen == "menu":
    screen_menu()
elif st.session_state.screen == "quiz":
    screen_quiz()
elif st.session_state.screen == "results":
    screen_results()