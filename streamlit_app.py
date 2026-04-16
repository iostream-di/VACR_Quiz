import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
import random
import time
from PIL import Image
from groq import Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Marty's VACR QUIZ", layout="wide", page_icon="✈️")

# Remove mobile browser auto-focus highlight
st.markdown("""
    <style>
    button:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# OPENAI SETUP
# ---------------------------------------------------------
def ai_difference_summary(correct, chosen):
    if chosen is None:
        return f"You did not select an answer. The correct aircraft was **{correct}**."

    prompt = f"""
You are a military aircraft recognition instructor.
Explain the silhouette differences between these two aircraft:

Correct aircraft: {correct}
Chosen aircraft: {chosen}

Focus ONLY on:
- Nose shape
- Tail configuration
- Wing geometry
- Engine placement
- Canopy style
- Intake shape
- Overall proportions

Keep it short, clear, and training-focused.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
        )
        return response.choices[0].message["content"]

    except Exception as e:
        return f"AI summary unavailable. Error: {e}"

# ---------------------------------------------------------
# VACR IMAGE SCALING
# ---------------------------------------------------------
def scale_vacr_pil(img, max_w, max_h):
    w, h = img.size

    if h > w:
        scale = max_h / h
    else:
        scale = max_w / w

    new_w = int(w * scale)
    new_h = int(h * scale)

    if new_w > max_w:
        scale = max_w / new_w
        new_w = int(new_w * scale)
        new_h = int(new_h * scale)

    if new_h > max_h:
        scale = max_h / new_h
        new_h = int(new_h * scale)
        new_w = int(new_w * scale)

    return img.resize((new_w, new_h), Image.LANCZOS)

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
    max_aircraft = len(categories)

    num_q = st.slider("Number of aircraft", 1, max_aircraft, min(20, max_aircraft))
    difficulty = st.selectbox("Difficulty", ["Easy", "Standard", "Warfighter", "AI"])
    num_choices = st.slider("Choices per question", 4, 6, 4)

    if st.button("Start Quiz"):
        st.session_state.screen = "quiz"
        st.session_state.quiz_settings = (chosen, num_q, difficulty, num_choices)
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
        chosen, num_q, difficulty, num_choices = st.session_state.quiz_settings
        categories, img_dir = load_hotlist(chosen)
        models = list(categories.keys())
        images = load_images(img_dir, models)
        st.session_state.quiz = Quiz(models, categories, images, num_q, difficulty, num_choices)
        st.session_state.phase_start = None
        st.session_state.last_state = None
        st.session_state.selected_choice = None

    quiz = st.session_state.quiz

    if quiz.state != st.session_state.get("last_state"):
        st.session_state.phase_start = None
        st.session_state.last_state = quiz.state

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

    if quiz.state == "finished":
        st.session_state.screen = "results"
        st.rerun()

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

            with st.expander(f"❌ {shown} → {correct}"):
                with st.spinner("Analyzing differences…"):
                    summary = ai_difference_summary(correct, chosen)
                st.markdown(summary)

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
