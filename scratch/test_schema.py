import os
import sys
import json
from pydantic import BaseModel, Field
from typing import List
import google.generativeai as genai

class InteractionSchema(BaseModel):
    personaj_1: str = Field(description="p1")
    personaj_2: str = Field(description="p2")
    gen_personaj_1: str = Field(description="g1")
    gen_personaj_2: str = Field(description="g2")
    tip_personaj_1: str = Field(description="t1")
    tip_personaj_2: str = Field(description="t2")

class DialogueExtractionSchema(BaseModel):
    interactiuni: List[InteractionSchema]

# Read .env to load keys
import environ
environ.Env.read_env(os.path.join(os.path.dirname(__file__), "..", ".env"), overwrite=True)

key = (os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or "").split(",")[0].strip()
genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

prompt = "Ion vorbește cu Ana în ogradă."

try:
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DialogueExtractionSchema,
            temperature=0.1
        )
    )
    print("SUCCESS: API call returned output:")
    print(response.text)
except Exception as e:
    print(f"FAILED: {e}")
