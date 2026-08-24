import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI

app = FastAPI()

# OpenRouter API Key उठाना
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_FALLBACK_KEY")

# OpenRouter के ज़रिये Grok को कनेक्ट करना (यह ब्लॉक नहीं होगा)
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai"
)

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
        response = client.chat.completions.create(
            # OpenRouter पर Grok मॉडल का नाम
            model="x-ai/grok-2-1212", 
            messages=[
                {"role": "system", "content": "आप Grok AI हैं।"},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices.message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
