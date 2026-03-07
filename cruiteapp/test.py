import requests

url = "http://localhost:11434/api/generate"

payload = {
    "model": "llama3.1",
    "prompt": "Explain ATS in one sentence",
    "stream": False
}

response = requests.post(url, json=payload)
response.raise_for_status()

print(response.json()["response"])
