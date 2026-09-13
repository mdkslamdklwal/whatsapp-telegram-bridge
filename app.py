from flask import Flask, request
from telegram_bot import send_message, send_photo
from whatsapp_api import download_media

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from threading import Timer, Lock


app = Flask(__name__)

VERIFY_TOKEN = "datekin123"

processed_messages = set()

# Store photos temporarily before sending them
pending_albums = {}

# Prevent simultaneous album processing
album_lock = Lock()

# How long to wait for additional photos
ALBUM_WAIT_SECONDS = 5


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

        # =========================
        # DUPLICATE PROTECTION
        # =========================

        if message_id in processed_messages:

            print("Duplicate ignored:", message_id)

            return "OK", 200

        processed_messages.add(message_id)

        print("MESSAGE ID:", message_id)
        print("TIMESTAMP:", message["timestamp"])

        # =========================
        # CONTACT INFORMATION
        # =========================

        sender = message["from"]

        contact_name = sender

        if "contacts" in value:

            contact_name = value["contacts"][0]["profile"]["name"]

        # =========================
        # WHATSAPP TIMESTAMP
        # =========================

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

            print("IMAGE RECEIVED:", media_id)
            print("CAPTION:", caption)

            # Download the photo now
            photo = download_media(media_id)

            # =========================
            # CREATE ALBUM ENTRY
            # =========================

            album_data = {
                "photo": photo,
                "caption": caption,
                "contact_name": contact_name,
                "sender": sender,
                "formatted_time": formatted_time,
                "timestamp": message_timestamp
            }

            with album_lock:

                if sender not in pending_albums:

                    pending_albums[sender] = {
                        "photos": [],
                        "timer": None
                    }

                pending_albums[sender]["photos"].append(album_data)

                print(
                    "Pending photos:",
                    len(pending_albums[sender]["photos"])
                )

                # Cancel previous timer
                old_timer = pending_albums[sender]["timer"]

                if old_timer is not None:
                    old_timer.cancel()

                # Start a new timer
                timer = Timer(
                    ALBUM_WAIT_SECONDS,
                    process_album,
                    args=[sender]
                )

                timer.daemon = True

                pending_albums[sender]["timer"] = timer

                timer.start()

    except Exception as e:

        print("Error:", e)

    return "OK", 200


# ==========================================
# PROCESS COMPLETE WHATSAPP ALBUM
# ==========================================

def process_album(sender):

    with album_lock:

        if sender not in pending_albums:
            return

        album = pending_albums.pop(sender)

    photos = album["photos"]

    if not photos:
        return

    print(
        "Processing album for",
        sender,
        "-",
        len(photos),
        "photos"
    )

    # ======================================
    # FIND CAPTION
    # ======================================

    caption = ""

    for item in photos:

        if item["caption"]:

            caption = item["caption"]

            break

    # Use information from first photo
    first_photo = photos[0]

    contact_name = first_photo["contact_name"]
    formatted_time = first_photo["formatted_time"]

    # ======================================
    # SEND CAPTION FIRST
    # ======================================

    if caption:

        telegram_message = (
            "📷 WhatsApp Photo\n\n"
            f"👤 {contact_name}\n"
            f"📱 {sender}\n"
            f"🕐 {formatted_time} WITA\n\n"
            f"📝 Caption:\n{caption}"
        )

        print("Sending caption FIRST")

        send_message(telegram_message)

    # ======================================
    # SEND ALL PHOTOS AFTER CAPTION
    # ======================================

    print("Sending", len(photos), "photos")

    for item in photos:

        print("Sending photo:", item["photo"])

        send_photo(item["photo"])
