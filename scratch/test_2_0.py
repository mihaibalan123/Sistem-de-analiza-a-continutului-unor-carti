import os
import sys

# Read keys from .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
keys = []
if os.path.exists(dotenv_path):
    with open(dotenv_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                val = line.split('=', 1)[1].strip()
                keys = [k.strip() for k in val.split(',') if k.strip()]
                break

import google.generativeai as genai
from pydantic import BaseModel
from typing import List

class Interaction(BaseModel):
    personaj_1: str
    personaj_2: str

class DialogueExtraction(BaseModel):
    interactiuni: List[Interaction]

print(f"Testing key: {keys[0][:6]}...")
genai.configure(api_key=keys[0])
model = genai.GenerativeModel('gemini-2.0-flash')

try:
    res = model.generate_content(
        "Extract interactions: Ion talks to Ana.",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DialogueExtraction,
        )
    )
    print("SUCCESS:")
    print(res.text)
except Exception as e:
    print("FAILED:")
    print(e)
