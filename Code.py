import streamlit as st
from PIL import Image
import time

st.title("👥 Team Name: Pixels")
st.header("📸 Project Title: Image Insights Detection using Multimodal Transformers")

if "saved_image" not in st.session_state:
    st.session_state.saved_image = None
if "option" not in st.session_state:
    st.session_state.option = None


def process_and_save_image(img):
    progress = st.progress(0)
    status_text = st.empty()
    for i in range(100):
        time.sleep(0.02)
        progress.progress(i + 1)
        status_text.text(f"Processing image... {i + 1}%")
    st.session_state.saved_image = img
    status_text.text("✅ Image saved for this session!")
    progress.empty()


def reset_input():
    st.session_state.saved_image = None
    st.session_state.option = None
    st.rerun()


input_options = ["-- Select Input Method --", "Upload Image", "Capture via Camera"]

if st.session_state.option is None and st.session_state.saved_image is None:
    selected = st.selectbox(
        "Choose input method:",
        options=input_options,
        index=0
    )
    if selected != input_options[0]:
        st.session_state.option = selected
    else:
        st.stop()


if st.session_state.option == "Upload Image" and st.session_state.saved_image is None:
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_container_width=True)

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
        st.image(img, caption="Captured Image", use_container_width=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Save this Image"):
                process_and_save_image(img)
        with col2:
            if st.button("🔄 Retake"):
                reset_input()


if st.session_state.saved_image is not None:
    st.subheader("✅ Final Saved Image")
    progress = st.progress(0)
    status_text = st.empty()
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i + 1)
        status_text.text(f"Displaying image... {i + 1}%")
    st.image(st.session_state.saved_image, use_container_width=True)
    progress.empty()
    status_text.empty()


    if st.button("🔁 Start Over"):
        reset_input()