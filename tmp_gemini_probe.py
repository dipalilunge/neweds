import os
import requests

key = os.getenv('GEMINI_API_KEY')
if not key:
    raise RuntimeError('Set GEMINI_API_KEY before running this probe.')
body = {'contents': [{'parts': [{'text': 'Say hello'}]}]}
for model in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    r = requests.post(url, params={'key': key}, json=body, timeout=30)
    print(model, r.status_code)
    print(r.text[:500])
