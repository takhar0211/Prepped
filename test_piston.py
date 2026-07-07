import requests

def test():
    url = "https://emkc.org/api/v2/piston/execute"
    payload = {
        "language": "python",
        "version": "3.10.0",
        "files": [{"content": "print('Hello Piston')"}],
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(response.status_code, response.json())
    except Exception as e:
        print("Piston Error:", e)

test()
