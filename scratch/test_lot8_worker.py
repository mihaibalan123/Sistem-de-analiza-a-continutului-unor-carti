import os
import sys
import json
import logging

sys.stdout.reconfigure(encoding='utf-8')

# Setup logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Setup Django settings path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mds_backend.settings")

import django
django.setup()

from analyzer.agents import DialogAgent
from analyzer.models import Carte

outputs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
import glob
json_path = glob.glob(os.path.join(outputs_dir, "carte_24_*.json"))[0]

# Load book JSON
data = json.load(open(json_path, "r", encoding="utf-8"))

# Lot 8 is indices 35 to 40 (pages 36 to 40)
lot = data[35:40]
text_lot = ""
for pag in lot:
    if pag["text_extras"].strip():
        text_lot += f"\n\n--- PAGINA {pag['pagina_pdf']} ---\n\n{pag['text_extras']}"

print("Text lot length:", len(text_lot))

agent = DialogAgent()
print("Calling agent.proceseaza_pagina_si_salveaza for Lot 8...")
try:
    agent.proceseaza_pagina_si_salveaza(text_lot, 24)
    print("SUCCESS: proceseaza_pagina_si_salveaza completed!")
except Exception as e:
    import traceback
    print("FAILED with exception:")
    traceback.print_exc()
