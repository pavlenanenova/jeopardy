import os

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite"))