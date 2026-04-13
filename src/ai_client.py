import os
from google import genai
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv
import base64
import json

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-2.5-flash-lite"

# Initialize client if key is present
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


def get_gemini_client():
    return client, DEFAULT_MODEL


def ocr_tweet_from_screenshot(screenshot_b64: str) -> str | None:
    """
    Use Gemini to extract the main tweet text and author from an X.com screenshot.
    Returns a human-readable string, or None on failure.
    """
    if not screenshot_b64:
        return None

    gemini_client, model = get_gemini_client()
    if not gemini_client:
        return None

    try:
        image_bytes = base64.b64decode(screenshot_b64)
    except Exception:
        return None

    prompt = (
        "You are reading a screenshot of a single X.com tweet.\n"
        "Extract ONLY the main tweet text and author.\n"
        "Rules:\n"
        "1. Ignore sidebar content (Trending, Who to follow, etc.).\n"
        "2. Ignore UI text like 'Who can reply?', 'Views', 'Reposts', 'Likes'.\n"
        "3. Ignore replies below the main tweet.\n"
        "Format the output as:\n"
        "Author Name (@handle)\n\n"
        "Tweet text..."
    )

    try:
        response = gemini_client.models.generate_content(
            model=model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_bytes,
                            }
                        },
                    ],
                }
            ],
            config=GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=256,
            ),
        )

        return response.text.strip()

    except Exception as e:
        print(f"OCR Error: {e}")
        return None
