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

from analyzer.agents import DialogAgent, Interaction

outputs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
import glob
json_paths = glob.glob(os.path.join(outputs_dir, "carte_24_*.json"))
if not json_paths:
    # Try any other json file
    json_paths = glob.glob(os.path.join(outputs_dir, "*.json"))

if not json_paths:
    print("No book JSON files found in outputs directory.")
    sys.exit(1)

json_path = json_paths[0]
data = json.load(open(json_path, "r", encoding="utf-8"))

# Let's take lot 8 (indices 35 to 39)
lot = data[35:40] if len(data) >= 40 else data
text_lot = ""
for pag in lot:
    if pag.get("text_extras", "").strip():
        text_lot += f"\n\n--- PAGINA {pag.get('pagina_pdf')} ---\n\n{pag.get('text_extras')}"

print("Text lot length:", len(text_lot))

agent = DialogAgent()
print("Calling extrage_interactiuni on Lot 8...")
try:
    import google.generativeai as genai
    from analyzer.agents import DialogueExtractionSchema
    
    res = agent.model.generate_content(
        text_lot,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DialogueExtractionSchema,
        )
    )
    print("SUCCESS:")
    print(res.text)
except Exception as e:
    print("FAILED:")
    print(e)