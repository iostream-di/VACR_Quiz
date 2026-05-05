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
import base64
from io import BytesIO

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Marty's VACR QUIZ", layout="wide", page_icon="✈️")

# ---------------------------------------------------------
# GLOBAL CSS — layout fixes + title padding + no scroll
# ---------------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

header, .stApp {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

h1, h2, h3 {
    padding-top: 2.0rem !important;
}

html, body, .stApp {
    height: 100%;
    overflow: hidden;
}

.vacr-img {
    max-height: 80vh !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Invisible auto-rerun trigger */
#invisirun {
    height: 0px !important;
    width: 0px !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INVISIBLE AUTO-RERUN ENGINE (0.5s)
# ---------------------------------------------------------
st.markdown("""
<script>
setTimeout(function() {
    const btn = document.getElementById("invisirun");
    if (btn) { btn.click(); }
}, 500);
</script>
""", unsafe_allow_html=True)

# Hidden button that triggers rerun
st.button(" ", key="invisirun", help="", type="secondary")

# ---------------------------------------------------------
# FULLY CACHED HTML IMAGE RENDERER
# ---------------------------------------------------------
@st.cache_resource
def get_cached_image_html(path_str, max_w=1600, max_h=900):
    img = Image.open(path_str)

    w, h = img.size
    scale = min(max_w / w, max_h / h)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return f"""
    <div style="text-align:center;">
        <img class="vacr-img"
             src="data:image/png;base64,{b64}" />
    </div>
    """

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
        images[model] = sorted(folder.glob("*.*")) if folder.exists() else []
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
        self.phase_start = time.time()

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

    filtered_models = [m for m, c in categories.items() if cat_states.get(c, False)]
    max_aircraft = len(filtered_models)

    if max_aircraft == 0:
        st.error("No aircraft available with the selected categories.")
        return

    num_q = st.slider("Number of aircraft", 1, max_aircraft, min(20, max_aircraft))
    difficulty = st.selectbox("Difficulty", ["Easy", "Standard", "Warfighter", "AI"], index=1)
    num_choices = st.slider("Choices per question", 4, 6, 4)

    if st.button("Start Quiz"):
        st.session_state.screen = "quiz"
        st.session_state.quiz_settings = (chosen, num_q, difficulty, num_choices, cat_states)
        st.session_state.quiz = None
        st.session_state.selected_choice = None
        st.rerun()

# ---------------------------------------------------------
# SCREEN 2 — QUIZ (auto-advancing silent timer)
# ---------------------------------------------------------
def screen_quiz():
    if "quiz" not in st.session_state or st.session_state.quiz is None:
        chosen, num_q, difficulty, num_choices, cat_states = st.session_state.quiz_settings
        categories, img_dir = load_hotlist(chosen)

        models = [m for m, c in categories.items() if cat_states.get(c, False)]
        images = load_images(img_dir, models)

        st.session_state.quiz = Quiz(models, categories, images, num_q, difficulty, num_choices)
        st.session_state.selected_choice = None

    quiz = st.session_state.quiz

    now = time.time()
    elapsed = now - quiz.phase_start

    # IMAGE PHASE
    if quiz.state == "image":
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Look closely…")

        if quiz.current_image:
            html = get_cached_image_html(str(quiz.current_image))
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.warning("No image found")

        # Auto-advance silently
        if elapsed >= quiz.image_time:
            quiz.state = "choices"
            quiz.phase_start = time.time()
            st.session_state.selected_choice = None
            st.rerun()
        return

    # CHOICES PHASE
    if quiz.state == "choices":
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Which one was it?")

        selected = st.session_state.get("selected_choice")

        cols = st.columns(2)
        for i, choice in enumerate(quiz.choices):
            col = cols[i % 2]
            label = f"▶ {choice}" if choice == selected else choice
            if col.button(label, key=f"choice_{i}"):
                st.session_state.selected_choice = choice
                st.rerun()

        # Auto-submit silently
        if elapsed >= quiz.choice_time:
            final_answer = st.session_state.get("selected_choice")
            quiz.process_answer(final_answer)
            st.session_state.selected_choice = None

            if quiz.state == "finished":
                st.session_state.screen = "results"

            st.rerun()
        return

    if quiz.state == "finished":
        st.session_state.screen = "results"
        st.rerun()
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