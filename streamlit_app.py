import streamlit as st
from pathlib import Path
import random

# Load images
IMAGE_DIR = Path("images")
image_files = list(IMAGE_DIR.glob("*.png"))

# Initialize session state
if "score" not in st.session_state:
    st.session_state.score = 0
if "current_image" not in st.session_state:
    st.session_state.current_image = random.choice(image_files)

st.title("VACR Identification Quiz")

# Show the image
st.image(st.session_state.current_image, width=400)

# User input
answer = st.text_input("Enter your identification")

if st.button("Submit"):
    correct = st.session_state.current_image.stem.lower()

    if answer.lower().strip() == correct:
        st.success("Correct!")
        st.session_state.score += 1
    else:
        st.error(f"Incorrect. Correct answer: {correct}")

    # Load next image
    st.session_state.current_image = random.choice(image_files)

st.write(f"Score: {st.session_state.score}")
