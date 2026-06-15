import os
import sys
import json
from pydantic import BaseModel, Field
from typing import List

sys.stdout.reconfigure(encoding='utf-8')

# Setup Django settings path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mds_backend.settings")

import django
django.setup()

import google.generativeai as genai

class ChapterSummarySchema(BaseModel):
    titlu_sectiune: str = Field(description="Titlul acestei secțiuni mari sau capitol (ex: 'Capitolul I: Glasul pământului')")
    rezumat_sectiune: str = Field(description="Un rezumat concis, fluid și redactat literar al acțiunii din această secțiune (maximum 2 paragrafe).")
    idei_principale: List[str] = Field(description="O listă cu exact 3 idei esențiale din această secțiune.")

class BookSummarySchema(BaseModel):
    rezumat_general: str = Field(description="Un rezumat general al romanului (maximum 3 paragrafe).")
    teme_principale: List[str] = Field(description="O lista cu exact 3-4 teme literare principale.")
    sectiuni: List[ChapterSummarySchema] = Field(description="Capitolele sau secțiunile mari ale cărții (exact 5-7 secțiuni mari care acoperă cronologic toată opera de la început la sfârșit).")

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

text_complet = ""
for pag in data:
    if pag.get("text_extras", "").strip():
        text_complet += f"\n\n--- PAGINA {pag.get('pagina_pdf')} ---\n\n{pag.get('text_extras')}"

print("Calling SummaryAgent with complete text length:", len(text_complet))
from analyzer.agents import SummaryAgent
agent = SummaryAgent()
try:
    res = agent.genereaza_rezumat_complet(text_complet)
    print("SUCCESS:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print("FAILED:")
    print(e)