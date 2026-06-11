import requests

urls = [
    'http://localhost:8000/',
    'http://localhost:8000/login/',
    'http://localhost:8000/ping-command/',
]

for u in urls:
    try:
        r = requests.get(u, timeout=5)
        print(f"URL: {u} -> {r.status_code}")
        snippet = r.text[:400].replace('\n', ' ')
        print('SNIPPET:', snippet)
    except Exception as e:
        print(f"URL: {u} -> ERROR: {e}")
