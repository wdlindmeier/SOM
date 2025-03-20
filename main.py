from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import openai
import base64
from io import BytesIO
from PIL import Image
import logging
import sys
from typing import Optional

from utils import *

app = FastAPI()

# Serve static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger('uvicorn.error')

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/image/")
async def upload_image(file: UploadFile = File(...), prompt: Optional[str] = Form(None)):
    logger.info("In /image")
    try:
        # Read file into a buffer to avoid multiple reads
        file_bytes = await file.read()
        image = Image.open(BytesIO(file_bytes)).convert("RGB")

        # Convert to base64
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        response = general_image_upload_base64_encoded_image(img_str, structured_wines, prompt)
        return {"response": response }

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {"error": str(e)}

@app.post("/prompt/")
async def ask_question(prompt: str = Form(None)):
    logger.info("In /prompt")
    try:
        response = recommend_wine_for_occasion(prompt, structured_wines)
        return {"response": response }

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("openai.html", {"request": request})

@app.get("/somcast", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("podcasts.html", {"request": request})    

@app.get("/profile", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})        