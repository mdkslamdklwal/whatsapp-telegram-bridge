import os
import requests

from config import WHATSAPP_ACCESS_TOKEN

BASE_URL = "https://graph.facebook.com/v25.0"


def get_media_url(media_id):

    url = f"{BASE_URL}/{media_id}"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    return response.json()


def download_media(media_id):

    media = get_media_url(media_id)

    print("Media response:")
    print(media)

    if "url" not in media:
        raise Exception(f"Cannot get media URL: {media}")

    media_url = media["url"]

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    response = requests.get(media_url, headers=headers)

    print("Download status:", response.status_code)

    response.raise_for_status()

    os.makedirs("downloads", exist_ok=True)

    filename = f"downloads/{media_id}.jpg"

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename