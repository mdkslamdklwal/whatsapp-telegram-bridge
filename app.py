processed_messages = set()
print("Processed IDs:", processed_messages)
from flask import Flask, request
from telegram_bot import send_message, send_photo
from whatsapp_api import download_media

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
        elif message_type == "image":

            print("Processing IMAGE", flush=True)

            media_id = message["image"]["id"]
            caption = message["image"].get("caption", "")

            print("MEDIA ID:", media_id, flush=True)
            print("CAPTION:", caption, flush=True)

            print("Downloading WhatsApp image...", flush=True)

            photo = download_media(media_id)

            print("PHOTO DOWNLOADED:", photo, flush=True)

            telegram_caption = (
                "📷 WhatsApp Photo\n\n"
                f"👤 {contact_name}\n"
                f"📱 {sender}\n\n"
            )

            if caption:
                telegram_caption += f"📝 Caption:\n{caption}"

            print("Sending photo to Telegram...", flush=True)

            send_photo(photo, telegram_caption)

            print("PHOTO SENT TO TELEGRAM", flush=True)

        else:

            print("UNSUPPORTED MESSAGE TYPE:", message_type, flush=True)

    except Exception as e:

        print("========== ERROR ==========", flush=True)
        print(type(e).__name__, flush=True)
        print(str(e), flush=True)

    return "OK", 200