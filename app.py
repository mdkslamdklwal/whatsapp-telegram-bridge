from flask import Flask, request
from telegram_bot import send_message, send_photo
from whatsapp_api import download_media

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

VERIFY_TOKEN = "datekin123"

processed_messages = set()


@app.route("/")
def home():
    return "WhatsApp Bridge Running!"


@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    print(data)

    try:

        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        if "messages" not in value:
            return "OK", 200

        message = value["messages"][0]
        message_id = message["id"]

        # Prevent duplicate webhook messages
        if message_id in processed_messages:
            print("Duplicate ignored:", message_id)
            return "OK", 200

        processed_messages.add(message_id)

        print("MESSAGE ID:", message_id)
        print("TIMESTAMP:", message["timestamp"])

        # WhatsApp timestamp → WITA
        message_timestamp = int(message["timestamp"])

        message_time = datetime.fromtimestamp(
            message_timestamp,
            timezone.utc
        ).astimezone(
            ZoneInfo("Asia/Makassar")
        )

        formatted_time = message_time.strftime(
            "%d %B %Y, %H:%M:%S"
        )

        sender = message["from"]

        contact_name = sender

        if "contacts" in value:
            contact_name = value["contacts"][0]["profile"]["name"]

        # =========================
        # TEXT MESSAGE
        # =========================

        if message["type"] == "text":

            text = message["text"]["body"]

            send_message(
                f"📩 WhatsApp Message\n\n"
                f"👤 {contact_name}\n"
                f"📱 {sender}\n"
                f"🕐 {formatted_time} WITA\n\n"
                f"💬 {text}"
            )

        # =========================
        # IMAGE MESSAGE
        # =========================

        elif message["type"] == "image":

            media_id = message["image"]["id"]
            caption = message["image"].get("caption", "")

            photo = download_media(media_id)

            telegram_message = (
                "📷 WhatsApp Photo\n\n"
                f"👤 {contact_name}\n"
                f"📱 {sender}\n"
                f"🕐 {formatted_time} WITA\n\n"
            )

            if caption:
                telegram_message += f"📝 Caption:\n{caption}"

                # Send information FIRST
                send_message(telegram_message)

            # Send photo WITHOUT caption
            send_photo(photo)

    except Exception as e:

        print("Error:", e)

    return "OK", 200