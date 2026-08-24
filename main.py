import os

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from google import genai
from google.genai import types


app = FastAPI()

# =========================================================
# GEMINI CLIENT
# =========================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable नहीं मिली।")

client = genai.Client(
    api_key=API_KEY
)

# =========================================================
# TEMPLATES
# =========================================================

templates = Jinja2Templates(
    directory="templates"
)


# =========================================================
# HOME
# =========================================================

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):

    return templates.TemplateResponse(
        request,
        "index.html"
    )


@app.head("/")
async def head_item():

    return HTMLResponse(
        content="",
        status_code=200
    )


# =========================================================
# ASK AI
# TEXT + IMAGE
# =========================================================

@app.post("/ask")
async def ask_ai(
    message: str = Form(""),
    file: UploadFile | None = File(None)
):

    try:

        message = (message or "").strip()

        # =================================================
        # IMAGE REQUEST
        # =================================================

        if file is not None:

            # MIME TYPE
            mime_type = file.content_type or ""

            if not mime_type.startswith("image/"):

                return {
                    "reply":
                    "कृपया JPG, PNG या WEBP image upload करें।"
                }


            # IMAGE BYTES
            image_bytes = await file.read()


            # 10 MB LIMIT
            if len(image_bytes) > 10 * 1024 * 1024:

                return {
                    "reply":
                    "Image 10 MB से बड़ी है। कृपया छोटी image upload करें।"
                }


            # DEFAULT PROMPT
            if not message:

                message = (
                    "इस image को ध्यान से देखकर बताइए "
                    "कि इसमें क्या दिखाई दे रहा है। "
                    "अगर image में text है तो उसे भी पढ़कर बताइए।"
                )


            # =================================================
            # GEMINI MULTIMODAL REQUEST
            # =================================================

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )


            response = client.models.generate_content(

                model="gemini-3.6-flash",

                contents=[
                    message,
                    image_part
                ]

            )


            return {
                "reply":
                response.text or "Image का जवाब नहीं मिला।"
            }


        # =================================================
        # TEXT ONLY
        # =================================================

        if not message:

            return {
                "reply":
                "कृपया अपना सवाल लिखें या image attach करें।"
            }


        response = client.models.generate_content(

            model="gemini-3.6-flashh",

            contents=message

        )


        return {
            "reply":
            response.text or "कोई जवाब नहीं मिला।"
        }


    except Exception as e:

        print(
            "ASK ERROR:",
            repr(e)
        )


        return {
            "reply":
            "AI Server Error: " + str(e)
        }
