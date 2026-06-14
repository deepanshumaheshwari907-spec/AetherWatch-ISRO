import requests

sizes = [32, 100, 180, 300]
for s in sizes:
    url = f"http://127.0.0.1:8000/api/v1/analyses/latest/preview?max_size={s}"
    print('\n===', url)
    try:
        r = requests.get(url, timeout=20)
        print('Status', r.status_code)
        print(r.text[:1000])
    except Exception as e:
        print('Error', e)
