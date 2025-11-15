import requests
import json

resp = requests.get('http://localhost:8000/patients')
print(f'Status: {resp.status_code}')
print(f'Content-Type: {resp.headers.get("content-type")}')
print(f'Response length: {len(resp.text)}')
print(f'Response text:\n{resp.text[:500]}')

try:
    data = resp.json()
    print(f'\nParsed JSON: {type(data).__name__} with {len(data) if isinstance(data, list) else "N/A"} items')
except Exception as e:
    print(f'\nJSON Parse Error: {e}')
