import requests
import json

api_key = "AIzaSyCFyOQdzqJ2-zebASJwcBnSyRvm-KlBpT4"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print("Available Models with generateContent:")
    for model in data.get("models", []):
        if "generateContent" in model.get("supportedGenerationMethods", []):
            print(model["name"])
else:
    print(f"Error {response.status_code}: {response.text}")
