import os
from io import BytesIO

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import google.generativeai as genai
from PIL import Image


app = FastAPI()

# =========================================================
# GEMINI
# =========================================================

API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "YOUR_FALLBACK_KEY"
)

genai.configure(api_key=API_KEY)

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
async def ask_ai(request: Request):

    try:

        content_type = request.headers.get(
            "content-type",
            ""
        )

        # =================================================
        # OLD JSON REQUEST
        # =================================================

        if "application/json" in content_type:

            data = await request.json()

            user_message = data.get(
                "message",
                ""
            )

            if not user_message:
                return {
                    "reply": "कृपया अपना सवाल लिखें।"
                }

            model = genai.GenerativeModel(
                "gemini-3.6-flash"
            )

            response = model.generate_content(
                user_message
            )

            return {
                "reply": response.text
            }


        # =================================================
        # NEW MULTIPART REQUEST
        # =================================================

        form = await request.form()

        user_message = form.get(
            "message",
            ""
        )

        uploaded_file = form.get(
            "file"
        )


        # Text नहीं और image भी नहीं
        if (
            not user_message
            and not isinstance(
                uploaded_file,
                UploadFile
            )
        ):

            return {
                "reply":
                "कृपया सवाल लिखें या image attach करें।"
            }


        model = genai.GenerativeModel(
            "gemini-3.6-flash"
        )


        # =================================================
        # IMAGE + TEXT
        # =================================================

        if isinstance(
            uploaded_file,
            UploadFile
        ):

            # केवल image स्वीकार करें
            if not uploaded_file.content_type.startswith(
                "image/"
            ):

                return {
                    "reply":
                    "अभी केवल JPG, PNG, WEBP जैसी image files upload करें।"
                }


            # 10 MB limit
            file_bytes = await uploaded_file.read()

            if len(file_bytes) > 10 * 1024 * 1024:

                return {
                    "reply":
                    "Image का size 10 MB से ज्यादा है। कृपया छोटी image upload करें।"
                }


            try:

                image = Image.open(
                    BytesIO(file_bytes)
                )

                # Gemini-compatible RGB conversion
                if image.mode not in (
                    "RGB",
                    "RGBA"
                ):

                    image = image.convert(
                        "RGB"
                    )


            except Exception:

                return {
                    "reply":
                    "Image पढ़ी नहीं जा सकी। कृपया दूसरी image try करें।"
                }


            prompt = user_message.strip()

            if not prompt:

                prompt = (
                    "इस image को ध्यान से देखें "
                    "और मुझे बताएं कि इसमें क्या दिखाई दे रहा है।"
                )


            response = model.generate_content(
                [
                    prompt,
                    image
                ]
            )


            return {
                "reply":
                response.text
            }


        # =================================================
        # TEXT ONLY MULTIPART
        # =================================================

        response = model.generate_content(
            user_message
        )

        return {
            "reply":
            response.text
        }


    except Exception as e:

        print(
            "ASK ERROR:",
            repr(e)
        )

        return {
            "reply":
            f"Error: {str(e)}"
        }
