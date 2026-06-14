import requests

ENDPOINTS = [
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/api/v1/analyses/latest",
    "http://127.0.0.1:8000/api/v1/analyses/latest/preview",
    "http://127.0.0.1:8501/",
]

for url in ENDPOINTS:
    print("\n=== GET", url)
    try:
        r = requests.get(url, timeout=10)
        print("Status:", r.status_code)
        text = r.text
        if len(text) > 1000:
            text = text[:1000] + "... (truncated)"
        print(text)
    except Exception as e:
        print("Error:", e)
