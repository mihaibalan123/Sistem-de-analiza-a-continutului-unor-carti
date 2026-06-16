import os
import django
import sys

# Set up Django environment to read .env
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mds_backend.settings')
django.setup()

import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
print(f"API Key: {api_key[:10] if api_key else 'None'}...")

if api_key:
    genai.configure(api_key=api_key)
    try:
        print("Listing models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name} ({m.display_name})")
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("No GEMINI_API_KEY found in environment.")
