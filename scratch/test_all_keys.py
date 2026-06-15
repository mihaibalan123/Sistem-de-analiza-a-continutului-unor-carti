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

if not keys:
    print("No keys found in .env")
    sys.exit(1)

import google.generativeai as genai

print(f"Found {len(keys)} keys in .env. Testing with gemini-2.5-flash...")

for idx, key in enumerate(keys):
    masked = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "..."
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        res = model.generate_content("Hello")
        # simple check
        text = res.text.strip().replace('\n', ' ')
        print(f"Key index {idx} ({masked}): SUCCESS -> {text[:50]}")
    except Exception as e:
        print(f"Key index {idx} ({masked}): FAILED -> {str(e)[:150]}")
