import streamlit as st
from pathlib import Path
import random
import time
from PIL import Image

# ---------------------------------------------------------
# SAFE RERUN HANDLER (must be at top)
# ---------------------------------------------------------
if st.session_state.get("_force_rerun", False):
    st.session_state._force_rerun = False
    st.rerun()

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="VACR QUIZ",
    layout="wide",
    page_icon="✈️"
)

# ---------------------------------------------------------
# LOAD HOTLIST FOLDERS
# ---------------------------------------------------------
def load_hotlist_folders():
    base = Path("hotlists")
    base.mkdir(exist_ok=True)
    folders = [f.name for f in base.iterdir() if f.is_dir() and (f / "hotlist.txt").exists()]
    folders.sort()
    return folders

# ---------------------------------------------------------
# LOAD HOTLIST DATA
# ---------------------------------------------------------
def load_hotlist(folder):
    base = Path("hotlists") / folder
    hotlist_path = base / "hotlist.txt"
    img_dir = base / "imgs"

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
        files = sorted(list(img_dir.glob(f"{safe}__*.*")))
        images[model] = files
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

        # Difficulty timing
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

        # Build question list
        self.questions = random.sample(models, min(num_q, len(models)))
        while len(self.questions) < num_q:
            self.questions += random.sample(models, min(len(models), num_q - len(self.questions)))

        self.index = 0
        self.score = 0
        self.wrong = []
        self.state = "image"
        self.start_time = time.time()

        self.current_model = None
        self.current_image = None
        self.choices = []

        self.next_question()

    # -----------------------------------------------------
    def next_question(self):
        if self.index >= self.num_q:
            self.state = "finished"
            return

        self.current_model = self.questions[self.index]

        # Pick image
        img_list = self.images.get(self.current_model, [])
        if img_list:
            self.current_image = random.choice(img_list)
        else:
            self.current_image = None

        # Build choices
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
        self.start_time = time.time()

    # -----------------------------------------------------
    def update(self):
        now = time.time()

        if self.state == "image" and now - self.start_time >= self.image_time:
            self.state = "choices"
            self.start_time = now

        elif self.state == "choices" and now - self.start_time >= self.choice_time:
            self.process_answer(None)

    # -----------------------------------------------------
    def process_answer(self, answer):
        if answer == self.current_model:
            self.score += 1
        else:
            self.wrong.append((self.current_model, answer))

        self.index += 1
        self.next_question()

# ---------------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------------
def run_quiz():
    st.title("✈️ Marty’s VACR Quiz")

    # Sidebar settings
    st.sidebar.header("Settings")

    hotlists = load_hotlist_folders()
    chosen = st.sidebar.selectbox("Hotlist", hotlists)

    num_q = st.sidebar.slider("Number of aircraft", 1, 50, 20)
    difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Standard", "Warfighter", "AI"])
    num_choices = st.sidebar.slider("Choices per question", 4, 6, 4)

    if st.sidebar.button("Start Quiz"):
        st.session_state.quiz_started = True
        st.session_state.quiz = None

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if not st.session_state.quiz_started:
        st.info("Configure settings and press **Start Quiz**")
        return

    # Load quiz if not already loaded
    if "quiz" not in st.session_state or st.session_state.quiz is None:
        categories, img_dir = load_hotlist(chosen)
        models = list(categories.keys())
        images = load_images(img_dir, models)
        st.session_state.quiz = Quiz(models, categories, images, num_q, difficulty, num_choices)

    quiz = st.session_state.quiz
    quiz.update()

    # -----------------------------------------------------
    # IMAGE PHASE
    # -----------------------------------------------------
    if quiz.state == "image":
        st.subheader("Look closely…")
        if quiz.current_image:
            img = Image.open(quiz.current_image)
            st.image(img, use_column_width=True)
        else:
            st.warning("No image found")

        remaining = quiz.image_time - (time.time() - quiz.start_time)
        st.progress(max(0, remaining) / quiz.image_time)

        st.session_state._force_rerun = True
        return

    # -----------------------------------------------------
    # CHOICE PHASE
    # -----------------------------------------------------
    elif quiz.state == "choices":
        st.subheader("Which one was it?")
        cols = st.columns(2)

        for i, choice in enumerate(quiz.choices):
            if cols[i % 2].button(choice):
                quiz.process_answer(choice)
                st.rerun()

        remaining = quiz.choice_time - (time.time() - quiz.start_time)
        st.progress(max(0, remaining) / quiz.choice_time)

        st.session_state._force_rerun = True
        return

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------
    else:
        st.header("Results")
        percent = (quiz.score / quiz.num_q) * 100
        st.subheader(f"Score: **{quiz.score}/{quiz.num_q}** ({percent:.1f}%)")

        if quiz.wrong:
            st.subheader("Incorrect Answers")
            for correct, chosen in quiz.wrong:
                st.write(f"❌ **{chosen}** → **{correct}**")
        else:
            st.success("Perfect score!")

        if st.button("Return to Menu"):
            st.session_state.quiz_started = False
            st.session_state.quiz = None
            st.rerun()

# ---------------------------------------------------------
# RUN APP
# ---------------------------------------------------------
run_quiz()
