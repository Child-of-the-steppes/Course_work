import argparse
import json
import time
from urllib.parse import quote

import requests
from tqdm import tqdm


class YandexDiskAPI:
    BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"OAuth {self.token}",
            "Accept": "application/json",
        }

    def create_folder(self, path):
        url = f"{self.BASE_URL}/resources?path={quote(path)}"
        response = requests.put(url, headers=self.headers)
        if response.status_code not in (201, 409):
            response.raise_for_status()
        return response.json()

    def upload_from_url(self, disk_path, source_url):
        url = f"{self.BASE_URL}/resources/upload?url={quote(source_url)}&path={quote(disk_path)}"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_operation_status(self, operation_id):
        url = f"{self.BASE_URL}/operations/{operation_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["status"]

    def get_file_info(self, path):
        url = f"{self.BASE_URL}/resources?path={quote(path)}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


def main(text, token):
    folder_name = "PD-142"
    file_name = f"{text}.jpg" 
    disk_path = f"/{folder_name}/{file_name}"

    cataas_url = f"https://cataas.com/cat/says/{quote(text)}?filter=mono&fontColor=red"

    api = YandexDiskAPI(token)

    print("Creating folder...")
    api.create_folder(f"/{folder_name}")

    print("Initiating upload from URL...")
    upload_response = api.upload_from_url(disk_path, cataas_url)
    operation_href = upload_response.get("href")
    if not operation_href:
        raise ValueError("No operation href returned")

    
    operation_id = operation_href.split("/")[-1]

    status = "in-progress"
    with tqdm(total=100, desc="Uploading", ncols=70) as pbar:
        while status == "in-progress":
            status = api.get_operation_status(operation_id)
            time.sleep(1)  
            pbar.update(1) 
            if pbar.n >= 100:
                pbar.n = 0  

    if status != "success":
        raise RuntimeError(f"Upload failed with status: {status}")

    print("Upload completed. Fetching file info...")
    file_info = api.get_file_info(disk_path)

    json_data = {
        "files": [
            {
                "path": disk_path,
                "size": file_info.get("size", 0),
                "name": file_name,
            }
        ]
    }

    json_filename = "uploaded_files.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    print(f"JSON file saved: {json_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload cat image with text to Yandex Disk")
    parser.add_argument("text", type=str, help="Text for the cat image")
    parser.add_argument("token", type=str, help="Yandex Disk OAuth token")
    args = parser.parse_args()

    main(args.text, args.token)