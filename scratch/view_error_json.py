import os
import sys
import json
from pydantic import BaseModel, Field
from typing import List

# Setup Django settings path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mds_backend.settings")

import django
django.setup()

import google.generativeai as genai

class ChapterSummarySchema(BaseModel):
    titlu_sectiune: str = Field(description="Titlul acestei secțiuni mari sau capitol")
    rezumat_sectiune: str = Field(description="Un rezumat detaliat al acestei secțiuni.")
    idei_principale: List[str] = Field(description="O listă cu idei principale.")

class BookSummarySchema(BaseModel):
    rezumat_general: str = Field(description="Un rezumat general al romanului.")
    teme_principale: List[str] = Field(description="O listă cu teme literare.")
    sectiuni: List[ChapterSummarySchema] = Field(description="Capitolele sau secțiunile cărții.")

# Load book JSON
outputs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
import glob
json_paths = glob.glob(os.path.join(outputs_dir, "carte_24_*.json"))
if not json_paths:
    json_paths = glob.glob(os.path.join(outputs_dir, "*.json"))

if not json_paths:
    print("No book JSON files found in outputs directory.")
    sys.exit(1)

json_path = json_paths[0]
data = json.load(open(json_path, "r", encoding="utf-8"))

test_pages = data[:100]
text_complet = ""
for pag in test_pages:
    if pag.get("text_extras", "").strip():
        text_complet += f"\n\n--- PAGINA {pag.get('pagina_pdf')} ---\n\n{pag.get('text_extras')}"

key = (os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY"))

print("Testing Gemini model generation for structured output...")
if not key:
    print("No GEMINI_API_KEY found.")
    sys.exit(1)

genai.configure(api_key=key.split(',')[0].strip())
model = genai.GenerativeModel("gemini-2.5-flash")
try:
    response = model.generate_content(
        f"Generate a structured summary for: {text_complet[:2000]}",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=BookSummarySchema
        )
    )
    print("Response text:")
    print(response.text)
except Exception as e:
    print("Error:", e)