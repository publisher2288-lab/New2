import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI  # Grok के लिए OpenAI लाइब्रेरी का उपयोग

app = FastAPI()

# Render से Grok API Key उठाना
XAI_API_KEY = os.getenv("XAI_API_KEY", "YOUR_FALLBACK_KEY")

# Grok API को कनेक्ट करने के लिए स्पेशल क्लाइंट सेटअप
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://x.ai"  # Grok का आधिकारिक सर्वर रूट
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
        # यहाँ Grok का सबसे लेटेस्ट और तेज़ मॉडल इस्तेमाल किया गया है
        response = client.chat.completions.create(
            model="grok-2-1212",
            messages=[
                {"role": "system", "content": "आप एक बहुत ही बुद्धिमान और मजाकिया AI सहायक हैं जिसका नाम Grok है।"},
                {"role": "user", "content": user_message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
