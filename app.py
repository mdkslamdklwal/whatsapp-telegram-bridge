processed_messages = set()
print("Processed IDs:", processed_messages)
from flask import Flask, request
from telegram_bot import send_message, send_photo
from whatsapp_api import download_media
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

VERIFY_TOKEN = "datekin123"


@app.route("/")
def home():
    return "WhatsApp Bridge Running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    print("========== WEBHOOK RECEIVED ==========", flush=True)
    print(data, flush=True)

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        print("VALUE RECEIVED", flush=True)

        if "messages" not in value:
            print("No messages in webhook", flush=True)
            return "OK", 200

        message = value["messages"][0]
        message_id = message["id"]
        message_type = message["type"]
        message_timestamp = int(message["timestamp"])

        message_time = datetime.fromtimestamp(
        message_timestamp,
            timezone.utc
        ).astimezone(
            ZoneInfo("Asia/Makassar")
        )

        formatted_time = message_time.strftime("%d %B %Y, %H:%M:%S")

        print("MESSAGE ID:", message_id, flush=True)
        print("MESSAGE TYPE:", message_type, flush=True)
        print("TIMESTAMP:", message["timestamp"], flush=True)

        if message_id in processed_messages:
            print("Duplicate ignored:", message_id, flush=True)
            return "OK", 200

        processed_messages.add(message_id)

        sender = message["from"]
        contact_name = sender

        if "contacts" in value:
            contact_name = value["contacts"][0]["profile"]["name"]

        print("SENDER:", sender, flush=True)
        print("CONTACT:", contact_name, flush=True)

        # TEXT
        if message_type == "text":

            print("Processing TEXT", flush=True)

            text = message["text"]["body"]

            send_message(
                f"📩 WhatsApp Message\n\n"
                f"👤 {contact_name}\n"
                f"📱 {sender}\n\n"
                f"💬 {text}"
            )

            print("TEXT SENT TO TELEGRAM", flush=True)

        # IMAGE
        elif message["type"] == "image":

    media_id = message["image"]["id"]
    caption = message["image"].get("caption", "")

    photo = download_media(media_id)

    telegram_message = (
        "📷 WhatsApp Photo\n\n"
        f"👤 {contact_name}\n"
        f"📱 {sender}\n"
        f"🕐 {formatted_time}\n\n"
    )

    if caption:
        telegram_message += f"📝 Caption:\n{caption}"

        # Send information FIRST
        send_message(telegram_message)

    # Send photo WITHOUT caption
        send_photo(photo)

        else:

            print("UNSUPPORTED MESSAGE TYPE:", message_type, flush=True)

    except Exception as e:

        print("========== ERROR ==========", flush=True)
        print(type(e).__name__, flush=True)
        print(str(e), flush=True)

    return "OK", 200