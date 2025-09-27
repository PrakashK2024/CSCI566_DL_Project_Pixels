import streamlit as st
from PIL import Image
import time
import os
import tempfile
import speech_recognition as sr

st.title("👥 Team Name: Pixels")
st.header("📸 Project Title: Interactive Web App for Image & Audio Insights with Transformers")

# Create a temp directory for session images
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

if "saved_image" not in st.session_state:
    st.session_state.saved_image = None
if "saved_image_path" not in st.session_state:
    st.session_state.saved_image_path = None
if "option" not in st.session_state:
    st.session_state.option = None
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""


def process_and_save_image(img):
    progress = st.progress(0)
    status_text = st.empty()
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i + 1)
        status_text.text(f"Processing image... {i + 1}%")

    img_path = os.path.join(st.session_state.temp_dir, "session_image.png")
    img.save(img_path)
    st.session_state.saved_image = img
    st.session_state.saved_image_path = img_path

    status_text.text("✅ Image securely saved for this session!")
    progress.empty()


def reset_input():
    if st.session_state.saved_image_path and os.path.exists(st.session_state.saved_image_path):
        os.remove(st.session_state.saved_image_path)
    st.session_state.saved_image = None
    st.session_state.saved_image_path = None
    st.session_state.option = None
    st.session_state.transcribed_text = ""
    st.rerun()


input_options = ["-- Select Input Method --", "Upload Image", "Capture via Camera"]

if st.session_state.option is None and st.session_state.saved_image is None:
    selected = st.selectbox("Choose input method:", options=input_options, index=0)
    if selected != input_options[0]:
        st.session_state.option = selected
    else:
        st.stop()

if st.session_state.option == "Upload Image" and st.session_state.saved_image is None:
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", width="stretch")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Save this Image"):
                process_and_save_image(img)
        with col2:
            if st.button("🔄 Retake / Reupload"):
                reset_input()

if st.session_state.option == "Capture via Camera" and st.session_state.saved_image is None:
    captured_file = st.camera_input("Take a picture")
    if captured_file:
        img = Image.open(captured_file)
        st.image(img, caption="Captured Image", width="stretch")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Save this Image"):
                process_and_save_image(img)
        with col2:
            if st.button("🔄 Retake"):
                reset_input()

if st.session_state.saved_image is not None:
    st.subheader("✅ Final Saved Image")
    st.image(st.session_state.saved_image, width="stretch")

    # Multimodal input
    st.subheader("🎙️ Text + Audio Input")

    col1, col2 = st.columns([2, 1])

    with col1:
        user_text = st.text_input(
            "💬 Enter your query here:",
            value=st.session_state.transcribed_text,
            key="text_input"
        )

        # New button to clear just the text field
        if st.button("🧹 Clear Text"):
            st.session_state.transcribed_text = ""
            st.rerun()

    with col2:
        st.write("🎤 Click below to speak:")
        if st.button("🎙️ Speak now"):
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("Listening...")
                audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                # Append new speech to existing text
                existing = st.session_state.transcribed_text
                if existing:
                    st.session_state.transcribed_text = existing + " " + text
                else:
                    st.session_state.transcribed_text = text
                st.success(f"You said: {text}")
                st.rerun()
            except sr.UnknownValueError:
                st.error("Could not understand audio")
            except sr.RequestError as e:
                st.error(f"Could not request results; {e}")

    if user_text:
        st.write(f"📝 You typed (or spoke): {user_text}")

    if st.button("🔁 Start Over"):
        reset_input()
