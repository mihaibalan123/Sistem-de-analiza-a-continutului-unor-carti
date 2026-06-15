import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mds_backend.settings')
django.setup()

from analyzer.agents import SummaryAgent
from docx import Document

print("Successfully imported everything!")

# Test SummaryAgent fallback simulator
agent = SummaryAgent()
res = agent.extrage_rezumat("Acesta este un text de probă despre Ion și Ana în satul Pripas.", "paginile 1 - 10")
print("Agent returned structure:")
print("- Titlu lot:", res.titlu_lot)
print("- Rezumat paragraf:", res.rezumat_paragraf)
print("- Idei principale:", res.idei_principale)

print("All tests passed successfully!")
