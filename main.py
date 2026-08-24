import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai

app = FastAPI()

# API Key सेटअप (इसे हम होस्टिंग पैनल में सुरक्षित रखेंगे)
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_FALLBACK_KEY")
genai.configure(api_key=API_KEY)

# HTML फाइल दिखाने के लिए सेटअप
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/ask")
async def ask_ai(data: dict):
    user_message = data.get("message", "")
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
