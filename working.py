# ======================================================================
#  VACR QUIZ v7.5 — CSS-based scaling + original image loader + TM1
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

# ---------------------------------------------------------
# GLOBAL CSS (padding + image fit)
# ---------------------------------------------------------
st.markdown("""
<style>
/* Reduce default Streamlit padding to give images more vertical room */
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

/* Slight top padding for headings so they don't stick to the top edge */
h1, h2, h3 {
    padding-top: 1.5rem !important;
}

/* Prevent double scrollbars and keep content tight */
html, body, .stApp {
    height: 100%;
    overflow: hidden;
}

/* VACR image: fit inside viewport without scrolling */
.vacr-img {
    max-height: 80vh !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Remove mobile browser auto-focus highlight on buttons */
button:focus {
    outline: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# IMAGE SCALING (original logic, now paired with CSS)
# ---------------------------------------------------------
def scale_vacr_pil(img, max_w=1600, max_h=900):
    w, h = img.size
    scale = min(max_w / w, max_h / h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

# ---------------------------------------------------------
# LOAD HOTLIST FOLDERS
# ---------------------------------------------------------
def load_hotlist_folders():
    base = Path("hotlists")
    base.mkdir(exist_ok=True)
    return sorted([f.stem for f in base.glob("*.txt")])

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
            model, cat = line.strip().split("|", 1)
            categories[model.strip()] = cat.strip().capitalize()

    return categories, img_dir

# ---------------------------------------------------------
# LOAD IMAGES (original working logic)
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
# MENU
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

    models = [m for m, c in categories.items() if cat_states.get(c, False)]
    if not models:
        st.error("No aircraft available with the selected categories.")
        return

    num_q = st.slider("Number of aircraft", 1, len(models), min(20, len(models)))
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
# QUIZ
# ---------------------------------------------------------
def screen_quiz():
    # 1s autorefresh drives TM1 timing + auto-advance
    st_autorefresh(interval=1000, key="quiz_tick")

    if "quiz" not in st.session_state or st.session_state.quiz is None:
        chosen, num_q, difficulty, num_choices, cat_states = st.session_state.quiz_settings
        categories, img_dir = load_hotlist(chosen)
        models = [m for m, c in categories.items() if cat_states.get(c, False)]
        images = load_images(img_dir, models)

        st.session_state.quiz = Quiz(models, categories, images, num_q, difficulty, num_choices)
        st.session_state.phase_start = None
        st.session_state.last_state = None
        st.session_state.selected_choice = None

    quiz = st.session_state.quiz

    # Reset timer when state changes
    if quiz.state != st.session_state.get("last_state"):
        st.session_state.phase_start = None
        st.session_state.last_state = quiz.state

    # IMAGE PHASE
    if quiz.state == "image":
        st.subheader(f"{quiz.index + 1}/{quiz.num_q}: Look closely…")

        if quiz.current_image:
            img = Image.open(quiz.current_image)
            img = scale_vacr_pil(img)  # scaled, plus CSS max-height 80vh
            st.image(img, use_column_width=False)
        else:
            st.warning("No image found")

        if st.session_state.phase_start is None:
            st.session_state.phase_start = time.time()

        elapsed = time.time() - st.session_state.phase_start
        remaining = quiz.image_time - elapsed

        if remaining <= 0:
            quiz.state = "choices"
            st.session_state.phase_start = None
            st.session_state.selected_choice = None
            st.rerun()
        return

    # CHOICE PHASE
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
                st.rerun()

        elapsed = time.time() - st.session_state.phase_start
        remaining = quiz.choice_time - elapsed

        if remaining <= 0:
            quiz.process_answer(st.session_state.get("selected_choice"))
            st.session_state.selected_choice = None
            st.session_state.phase_start = None

            if quiz.state == "finished":
                st.session_state.screen = "results"
            st.rerun()
        return

    # FINISHED
    if quiz.state == "finished":
        st.session_state.screen = "results"
        st.rerun()

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
        st.session_state.phase_start = None
        st.session_state.last_state = None
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
