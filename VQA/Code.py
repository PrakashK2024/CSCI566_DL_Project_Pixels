import io, os, asyncio
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
import httpx

# --------------------- Config ---------------------
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
MAX_IMAGE_DIM = 1024

st.set_page_config(page_title="PixelSense (Backend)", page_icon="📸", layout="wide")
# --------------------- UI / Title ---------------------
full_header_text = [
    "📸 PixelSense: Multimodal Transformer Framework",
    "For Interactive Image Understanding"
]

# Generate animated spans for each line
animated_header_html = "<br>".join(
    ["".join(f"<span style='--i:{i}'>{ch}</span>" for i, ch in enumerate(line)) for line in full_header_text]
)

st.markdown(f"""
<style>
/* Body and general text */
body {{
    background-color: #ffffff !important;
    color: #000000 !important;         
}}

/* Title container */
.title-container {{
    text-align:center;
    font-size:2.2rem;
    font-weight:700;
    margin-bottom:1rem;
    color:#000;
}}

/* Animated letters */
.pixels span {{
    display:inline-block;
    animation: rainbow 2s infinite;
}}
@keyframes rainbow {{
    0% {{color:#ff4b4b;}}
    25% {{color:#ffa64b;}}
    50% {{color:#4bff4b;}}
    75% {{color:#4b9bff;}}
    100% {{color:#ff4b4b;}}
}}

/* Header animation (bounce/wave) */
.puzzle-header {{
    text-align:center;
    color:#000;
    font-weight:600;
    font-size:1.8rem;
    line-height:1.4;
    display:inline-block;
}}
.puzzle-header span {{
    display:inline-block;
    opacity:0;
    transform: translateY(-20px);
    animation: bounceIn 0.6s forwards;
}}
.puzzle-header span:nth-child(n) {{
    animation-delay: calc(var(--i) * 0.03s);
}}

@keyframes bounceIn {{
    0% {{opacity:0; transform: translateY(-30px);}}
    50% {{opacity:1; transform: translateY(10px);}}
    100% {{opacity:1; transform: translateY(0);}}
}}

/* Result and info boxes */
.result-box {{
    background:#f7f7f7; 
    border-radius:8px; 
    padding:12px; 
    white-space:pre-wrap; 
    color:#000;
}}
.info-box {{
    font-size:0.9rem; 
    color:#000; 
    background:#f0f0f0; 
    padding:6px 10px; 
    border-radius:6px; 
    margin-bottom:8px;
}}

</style>

<div class="title-container">👥 Team Name:
  <span class="pixels"><span>P</span><span>i</span><span>x</span><span>e</span><span>l</span><span>s</span></span>
</div>
<div class="header-container">
  <h2 class='puzzle-header'>{animated_header_html}</h2>

""", unsafe_allow_html=True)


# --------------------- Session State ---------------------
for key in ["image_bytes", "camera_preview", "answer", "saved_image_path", "input_option"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --------------------- Helpers ---------------------
def prepare_image(image_bytes: bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), img.size

async def save_image_to_backend(image_bytes: bytes, filename: str):
    async with httpx.AsyncClient(timeout=30) as client:
        files = {"file": (filename, image_bytes, "image/png")}
        resp = await client.post(f"{BACKEND_URL}/upload-image", files=files)
        if resp.status_code == 200:
            return resp.json()["url"]
        return None

async def get_caption(file_url: str):
    async with httpx.AsyncClient(timeout=60) as client:
        data = {"file_url": file_url}
        resp = await client.post(f"{BACKEND_URL}/image-caption", data=data)
        if resp.status_code == 200:
            return resp.json()["answer"]
        return f"❌ Error: {resp.text}"

async def get_vqa(file_url: str, question: str):
    async with httpx.AsyncClient(timeout=60) as client:
        data = {"file_url": file_url, "question": question}
        resp = await client.post(f"{BACKEND_URL}/image-vqa", data=data)
        if resp.status_code == 200:
            return resp.json()["answer"]
        return f"❌ Error: {resp.text}"

# --------------------- Input Selection ---------------------
st.markdown("### 🖼️ Choose Input Method")
st.session_state.input_option = st.radio(
    "Select input method:", ["Upload Image", "Capture via Camera"], horizontal=True
)

col1, col2 = st.columns(2, gap="large")
if st.session_state.input_option == "Upload Image":
    with col1:
        uploaded = st.file_uploader("Upload an image (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.session_state.image_bytes = uploaded.getvalue()
    with col2:
        st.info("You selected Upload mode. Switch to Camera to capture a live image.")
else:
    with col1:
        if st.session_state.camera_preview:
            st.image(st.session_state.camera_preview, caption="Camera Preview", width=300)
    with col2:
        captured = st.camera_input("Take a picture")
        if captured:
            st.session_state.image_bytes = captured.getvalue()
            st.session_state.camera_preview = Image.open(io.BytesIO(st.session_state.image_bytes))

# --------------------- Display & Save ---------------------
if st.session_state.image_bytes:
    prepared_img_bytes, img_size = prepare_image(st.session_state.image_bytes)
    st.image(prepared_img_bytes, caption="Preview", width=520)
    st.markdown(f"<div class='info-box'>Image size: {img_size[0]}x{img_size[1]} px | File size: {len(prepared_img_bytes)//1024} KB</div>", unsafe_allow_html=True)

    if st.button("💾 Save to Backend"):
        file_url = asyncio.run(save_image_to_backend(prepared_img_bytes, "uploaded_image.png"))
        if file_url:
            st.session_state.saved_image_path = file_url
            st.success(f"Image saved: {file_url}")
            st.image(f"{BACKEND_URL}{file_url}", caption="Saved Preview", width=520)

    # --------------------- Query Options ---------------------
    st.markdown("### 🤖 Query Options")
    query_type = st.radio("Select:", ["Image Captioning", "Visual Question Answering (VQA)"], horizontal=True)
    prompt_text = ""
    if query_type == "Visual Question Answering (VQA)":
        prompt_text = st.text_input("Ask a question:", placeholder="What is happening in the image?")

    if st.button("🔍 Get Answer"):
        if st.session_state.saved_image_path:
            if query_type == "Image Captioning":
                st.session_state.answer = asyncio.run(get_caption(st.session_state.saved_image_path))
            else:
                st.session_state.answer = asyncio.run(get_vqa(st.session_state.saved_image_path, prompt_text))
        else:
            st.warning("💡 Please save the image to backend first.")

    if st.session_state.answer:
        st.markdown("### 🧠 Model Output")
        st.markdown(f"<div class='result-box'>{st.session_state.answer}</div>", unsafe_allow_html=True)

# --------------------- Reset ---------------------
# Reset variables
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False

col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("🔄 Start Over"):
        for key in ["image_bytes", "camera_preview", "answer", "saved_image_path", "input_option"]:
            st.session_state[key] = None
        st.session_state.reset_trigger = True

# Conditionally hide preview
if st.session_state.get("reset_trigger"):
    st.session_state.reset_trigger = False
