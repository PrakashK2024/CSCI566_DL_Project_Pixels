from fastapi import FastAPI, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from PIL import Image
import io, os, tempfile, base64, uuid
from dotenv import load_dotenv
import openai
import aiofiles
import httpx

# ------------------------- Setup -------------------------
app = FastAPI()
TEMP_DIR = tempfile.mkdtemp()
app.mount("/files", StaticFiles(directory=TEMP_DIR), name="files")

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
MODEL_ID = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_IMAGE_DIM = 1024

openai.api_key = OPENAI_API_KEY

# ------------------------- Helpers -------------------------
async def prepare_image_bytes(file_bytes: bytes):
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

async def upload_to_imgbb(image_bytes: bytes):
    """Upload image to imgbb and return public URL"""
    if not IMGBB_API_KEY:
        return None
    payload = {
        "key": IMGBB_API_KEY,
        "image": base64.b64encode(image_bytes).decode("utf-8")
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post("https://api.imgbb.com/1/upload", data=payload)
            resp.raise_for_status()
            return resp.json()["data"]["url"]
    except Exception:
        return None

async def openai_predict(image_url: str, prompt: str):
    try:
        response = openai.chat.completions.create(
            model=MODEL_ID,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }],
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"

async def fetch_image(file_url: str):
    """Fetch image from URL or local /files path"""
    try:
        if file_url.startswith("/files/"):
            # Local temp file
            file_path = os.path.join(TEMP_DIR, os.path.basename(file_url))
            if not os.path.exists(file_path):
                return None
            async with aiofiles.open(file_path, "rb") as f:
                return await prepare_image_bytes(await f.read())
        else:
            # External URL
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = await client.get(file_url, headers=headers)
                resp.raise_for_status()
                return await prepare_image_bytes(resp.content)
    except Exception:
        return None

# ------------------------- Endpoints -------------------------
@app.post("/upload-image")
async def upload_image(file: UploadFile):
    content = await prepare_image_bytes(await file.read())
    filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(TEMP_DIR, filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    return {"message": "✅ Image uploaded successfully", "url": f"/files/{filename}"}

@app.post("/image-caption")
async def image_caption(file: UploadFile = None, file_url: str = Form(None)):
    if file:
        content = await prepare_image_bytes(await file.read())
    elif file_url:
        content = await fetch_image(file_url)
        if not content:
            return JSONResponse({"answer": "❌ Could not fetch image from URL or local file"})
    else:
        return JSONResponse({"answer": "❌ No image provided"})

    # Upload to imgbb if possible
    image_url = await upload_to_imgbb(content)
    if not image_url:
        # fallback to local temp file
        filename = f"temp_{uuid.uuid4().hex}.png"
        file_path = os.path.join(TEMP_DIR, filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        image_url = f"/files/{filename}"

    answer = await openai_predict(image_url, "Provide a short descriptive caption for this image.")
    return {"answer": answer, "type": "caption"}

@app.post("/image-vqa")
async def image_vqa(question: str = Form(...), file: UploadFile = None, file_url: str = Form(None)):
    if file:
        content = await prepare_image_bytes(await file.read())
    elif file_url:
        content = await fetch_image(file_url)
        if not content:
            return JSONResponse({"answer": "❌ Could not fetch image from URL or local file", "question": question})
    else:
        return JSONResponse({"answer": "❌ No image provided", "question": question})

    # Upload to imgbb if possible
    image_url = await upload_to_imgbb(content)
    if not image_url:
        # fallback to local temp file
        filename = f"temp_{uuid.uuid4().hex}.png"
        file_path = os.path.join(TEMP_DIR, filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        image_url = f"/files/{filename}"

    answer = await openai_predict(image_url, question)
    return {"answer": answer, "question": question, "type": "vqa"}
