import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai

app = FastAPI()

# Render से सुरक्षित तरीके से Google API Key उठाना
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_FALLBACK_KEY")
genai.configure(api_key=API_KEY)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.head("/")
async def head_item():
    return HTMLResponse(content="", status_code=200)

@app.post("/ask")
async def ask_ai(data: dict):
    user_message = data.get("message", "")
    try:
        # गूगल का सबसे नया और बिना एरर चलने वाला 2.5-flash मॉडल
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(user_message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
