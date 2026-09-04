import os
import requests

from config import WHATSAPP_ACCESS_TOKEN

BASE_URL = "https://graph.facebook.com/v25.0"


def test_access_token():

    token = WHATSAPP_ACCESS_TOKEN

    print("========== TOKEN DIAGNOSTIC ==========", flush=True)

    if token is None:
        print("TOKEN STATUS: MISSING", flush=True)
        return

    print("TOKEN LENGTH:", len(token), flush=True)
    print("STARTS WITH EA:", token.startswith("EA"), flush=True)
    print("HAS BEARER:", token.startswith("Bearer"), flush=True)
    print("HAS LEADING SPACE:", token != token.lstrip(), flush=True)
    print("HAS TRAILING SPACE:", token != token.rstrip(), flush=True)
    print("HAS NEWLINE:", "\n" in token or "\r" in token, flush=True)
    print(
        "HAS QUOTES:",
        token.startswith('"') or token.endswith('"')
        or token.startswith("'") or token.endswith("'"),
        flush=True
    )

    url = f"{BASE_URL}/1197057296831033"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    print("HTTP STATUS:", response.status_code, flush=True)
    print("RESPONSE:", response.text, flush=True)
    print("=======================================", flush=True)

def get_media_url(media_id):

    url = f"{BASE_URL}/{media_id}"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    return response.json()


def download_media(media_id):

    # TEMPORARY: test the token before downloading the image
    test_access_token()

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


if __name__ == "__main__":
    test_access_token()