import requests
import json

with open("api_response.txt", "w") as f:
    try:
        url = "https://hyper-download-manager-web.vercel.app/api/version?platform=windows"
        f.write("WINDOWS RESPONSE:\n")
        resp = requests.get(url, timeout=10)
        f.write(json.dumps(resp.json(), indent=2))
        f.write("\n\n")

        url = "https://hyper-download-manager-web.vercel.app/api/version?platform=linux"
        f.write("LINUX RESPONSE:\n")
        resp = requests.get(url, timeout=10)
        f.write(json.dumps(resp.json(), indent=2))
        f.write("\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
