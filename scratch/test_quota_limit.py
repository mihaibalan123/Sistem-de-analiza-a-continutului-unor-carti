import os
import sys
import time

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

genai.configure(api_key=keys[0])
model = genai.GenerativeModel('gemini-2.5-flash-lite')

print("Testing limit for gemini-2.5-flash-lite by making 25 requests...")
for i in range(1, 26):
    try:
        res = model.generate_content("Hello")
        print(f"Request {i}: SUCCESS")
        # Sleep to avoid RPM limit (15 RPM means we need ~4 seconds spacing)
        time.sleep(4.2)
    except Exception as e:
        print(f"Request {i}: FAILED -> {str(e)[:150]}")
        break
