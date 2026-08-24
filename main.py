import os

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from google import genai
from google.genai import types


app = FastAPI()

# =========================================================
# GEMINI API
# =========================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable नहीं मिली।"
    )

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# MODELS
# Primary → Fallback 1 → Fallback 2
# =========================================================

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash"
]


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
# GEMINI REQUEST WITH FALLBACK
# =========================================================

def generate_with_fallback(contents):

    last_error = None

    for model_name in MODELS:

        try:

            print(
                f"Trying Gemini model: {model_name}"
            )

            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )

            print(
                f"SUCCESS: {model_name}"
            )

            return response


        except Exception as e:

            last_error = e

            error_text = str(e)

            print(
                f"MODEL ERROR {model_name}: {error_text}"
            )


            # ---------------------------------------------
            # केवल temporary capacity/rate errors पर
            # अगला model try करें
            # ---------------------------------------------

            if (
                "503" in error_text
                or
                "UNAVAILABLE" in error_text
                or
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED" in error_text
            ):

                print(
                    f"Fallback activated after {model_name}"
                )

                continue


            # ---------------------------------------------
            # बाकी errors पर तुरंत stop
            # ---------------------------------------------

            raise e


    # सभी models fail
    raise last_error


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

        message = (
            message or ""
        ).strip()


        # =================================================
        # IMAGE REQUEST
        # =================================================

        if file is not None:

            mime_type = (
                file.content_type
                or ""
            )


            # ---------------------------------------------
            # IMAGE CHECK
            # ---------------------------------------------

            if not mime_type.startswith(
                "image/"
            ):

                return {
                    "reply":
                    "कृपया JPG, PNG, WEBP या GIF image upload करें।"
                }


            # ---------------------------------------------
            # READ IMAGE
            # ---------------------------------------------

            image_bytes = await file.read()


            # ---------------------------------------------
            # 10 MB LIMIT
            # ---------------------------------------------

            if len(image_bytes) > 10 * 1024 * 1024:

                return {
                    "reply":
                    "Image 10 MB से बड़ी है। कृपया छोटी image upload करें।"
                }


            # ---------------------------------------------
            # DEFAULT IMAGE PROMPT
            # ---------------------------------------------

            if not message:

                message = (
                    "इस image को ध्यान से देखकर बताइए "
                    "कि इसमें क्या दिखाई दे रहा है। "
                    "अगर image में कोई text है तो उसे पढ़कर "
                    "उसका अर्थ भी बताइए।"
                )


            # ---------------------------------------------
            # GEMINI IMAGE PART
            # ---------------------------------------------

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )


            # ---------------------------------------------
            # IMAGE + TEXT
            # ---------------------------------------------

            response = generate_with_fallback(
                [
                    message,
                    image_part
                ]
            )


            reply = (
                response.text
                or
                "Image का जवाब नहीं मिला।"
            )


            return {
                "reply": reply
            }


        # =================================================
        # TEXT ONLY
        # =================================================

        if not message:

            return {
                "reply":
                "कृपया अपना सवाल लिखें या image attach करें।"
            }


        # ---------------------------------------------
        # TEXT REQUEST
        # ---------------------------------------------

        response = generate_with_fallback(
            message
        )


        reply = (
            response.text
            or
            "कोई जवाब नहीं मिला।"
        )


        return {
            "reply": reply
        }


    except Exception as e:

        print(
            "===================================="
        )

        print(
            "FINAL ASK ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "===================================="
        )


        return {
            "reply":
            "AI Server Error: " + str(e)
        }
