import requests
import json

url = "https://hyper-download-manager-web.vercel.app/api/version?platform=windows"
try:
    print(f"Fetching {url}...")
    resp = requests.get(url, timeout=10)
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")