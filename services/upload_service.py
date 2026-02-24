import requests

API_URL = "https://api-storage-dev.diamond.co.id/v1/uploadFiles"
BEARER_TOKEN = "RElHSVRBTDpkb2NkaWdpdGFsMjAyNQ=="

def upload_to_api(uploaded_file):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    file_content = uploaded_file.read()

    files = {
        "uploadFiles": (uploaded_file.name, file_content)
    }

    data = {
        "type": "images",
        "fileName": uploaded_file.name
    }

    response = requests.post(API_URL, headers=headers, files=files, data=data, timeout=60)

    print("STATUS:", response.status_code)
    print("TEXT:", response.text)

    if response.status_code == 200:
        json_resp = response.json()

        # Coba beberapa kemungkinan struktur
        if "FilePath" in json_resp:
            return json_resp["FilePath"]

        if "data" in json_resp and isinstance(json_resp["data"], dict):
            return json_resp["data"].get("filePath")

        if "data" in json_resp:
            return json_resp["data"]

    return None