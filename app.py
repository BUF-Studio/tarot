import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

import time


import json
from database import get_session, create_or_update_session, clear_session


import logging

from postgres import UserLimitChecker

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Set your API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the UserLimitChecker with database parameters
db_params = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}
user_limit_checker = UserLimitChecker(db_params)


# @app.route('/ask', methods=['POST'])
def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use a supported model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )

        return response.choices[0].message["content"].strip()
    except openai.OpenAIError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_tarot_cards(question):
    prompt = f"""
                You are a tarot card reader. Please provide a detailed reading for the following question : "{question}". 

                Draw six cards and interpret each one according to its position. The positions are:

            1. You
            2. Situation / Context
            3. Challenge
            4. Development
            5. Outcome
            6. Advice

            Each card description should include:
            - The card name
            - A detailed explanation of what the card signifies in the given position
            - Link the interpretation to the question

            Return the descriptions and summary in the following format:
            {{
                "cards": [
                    {{"position": "You", "description": "Card Name - Detailed Description"}},
                    {{"position": "Situation / Context", "description": "Card Name - Detailed Description"}},
                    {{"position": "Challenge", "description": "Card Name - Detailed Description"}},
                    {{"position": "Development", "description": "Card Name - Detailed Description"}},
                    {{"position": "Outcome", "description": "Card Name - Detailed Description"}},
                    {{"position": "Advice", "description": "Card Name - Detailed Description"}}
                ],
                "summary": "Summary of the reading that links to the question"
            }}
    
       
    """
    response = ask_openai(prompt)

    return eval(response)


# VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN')

WHATSAPP_API_URL = "https://graph.facebook.com/v20.0/391867514003939/"
ACCESS_TOKEN = "EAAQZATIbxyeQBO6EJsoMor0y1ofTsj9dIguHFw5xj9zq4h5hOEXVwje1hZAEb5TPk21qYJkTKdCKHujrlCQQZBke8tzZC48RqzPAFX8SBBY9RleQJZBNayZBZBVD8ZAQjGUTsn2MZC7e8LeA3hcZB7DPiZCRCpiZBGnoElDu4FiJcVjwdtFozuucfnKVdNCmOUcVKCfQpkt3Qa1yoqPjbd9yfUvWeJUD9LcZD"
VERIFY_TOKEN = "123456"


def send_whatsapp_pic(to, mediaId):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "id": mediaId,
        },
    }

    response = requests.post(
        f"{WHATSAPP_API_URL}messages", headers=headers, json=payload
    )

    if response.status_code == 200:
        logging.debug(f"Message sent successfully: {response.json()}")
    else:
        logging.error(f"Failed to send message: {response.text}")


def send_whatsapp_message(to, message):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {
            "body": message,
        },
    }

    response = requests.post(
        WHATSAPP_API_URL + "messages", headers=headers, json=payload
    )

    if response.status_code == 200:
        logging.debug(f"Message sent successfully: {response.json()}")
    else:
        logging.error(f"Failed to send message: {response.text}")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data["object"] == "whatsapp_business_account":
        for entry in data["entry"]:
            for change in entry["changes"]:
                if "messages" in change["value"]:
                    for message in change["value"]["messages"]:
                        if "text" in message:
                            incoming_msg = message["text"]["body"].lower()
                            sender_id = message["from"]

                            print(f"Message: {incoming_msg}")

                            # Retrieve session from the database
                            session = get_session(sender_id)

                            media_id = None

                            if session:
                                question = session[1]
                                cards = None
                                try:
                                    # Load the JSON string into a Python object
                                    cards = json.loads(session[2])
                                except json.JSONDecodeError as e:
                                    # Handle JSON decoding errors
                                    print("No cards")
                                    # cards = None
                                # cards = json.loads(session[2])  # Load the JSON string into a Python object
                                summary = session[3]
                                current_card = session[4]
                                stage = session[5]
                            else:
                                question = cards = summary = None
                                current_card = 0
                                stage = "start"

                            if incoming_msg == "start now":
                                response_message = "Great! Please focus on your question and type it below."
                                media_id = upload_image('back')
                                stage = "question"
                                create_or_update_session(
                                    sender_id, "", "", "", 0, stage
                                )
                            elif stage == "question":
                                question = incoming_msg
                                tarot_reading = generate_tarot_cards(incoming_msg)
                                # print(tarot_reading)
                                cards = tarot_reading["cards"]
                                summary = tarot_reading["summary"]

                                split_description = cards[0]["description"].split(" - ")

                                response_message = f"Question: {incoming_msg}. \n\n"
                                response_message += f"*{cards[0]['position']} : {split_description[0]}* \n\n"
                                response_message += f"{split_description[1]}\n\n"
                                response_message += "Type _'Next'_ to continue."

                                media_id = upload_image(split_description[0])

                                current_card = 1
                                stage = "next_card"
                                create_or_update_session(
                                    sender_id,
                                    question,
                                    json.dumps(cards),
                                    summary,
                                    current_card,
                                    stage,
                                )
                            elif stage == "next_card":
                                if current_card < 6:
                                    current_card_data = cards[current_card]

                                    split_description = cards[current_card][
                                        "description"
                                    ].split(" - ")

                                    response_message = f"*{current_card_data['position']} : {split_description[0]}*\n\n"
                                    response_message += f"{split_description[1]}\n\n"
                                    response_message += "Type _'Next'_ to continue."

                                    media_id = upload_image(split_description[0])

                                    current_card += 1
                                    create_or_update_session(
                                        sender_id,
                                        question,
                                        json.dumps(cards),
                                        summary,
                                        current_card,
                                        stage,
                                    )
                                else:
                                    response_message = "*Summary*\n\n"
                                    response_message += summary
                                    clear_session(
                                        sender_id
                                    )  # Clear session after the reading is complete
                            else:
                                response_message = (
                                    "Type _'Start Now'_ to begin the tarot reading."
                                )

                            print(response_message)

                            if media_id != None:
                                send_whatsapp_pic(sender_id, media_id)
                                time.sleep(1)
                                    
                            send_whatsapp_message(sender_id, response_message)

    return jsonify({"status": "success"}), 200


@app.route("/clear", methods=["GET"])
def clear():
    clear_session("60189869935")
    return jsonify({"status": "success"}), 200


@app.route("/webhook", methods=["GET"])
def webhook_setup():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # print("Received data: ")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403
    return "Bad Request", 400
    # return challenge, 200


@app.route("/createUser", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        id = data["id"]
        username = data["username"]
        email = data["email"]
        phone_number = data["phone_number"]

        user_id = user_limit_checker.create_user(id, username, email, phone_number)
        return jsonify({"status": "success", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


def upload_image(card):
    # card = "The Star"

    local_image_path = rf"/Users/kks/Documents/flask/tarot/pic/1909 (Pam A)/{card}.jpg"

    if not os.path.exists(local_image_path):
        logging.debug(f"File not found")
        return None

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Open the file from the local file system
    with open(local_image_path, "rb") as image_file:
        files = {
            "file": (os.path.basename(local_image_path), image_file, "image/jpeg"),
            "type": (None, "image/jpeg"),
            "messaging_product": (None, "whatsapp"),
        }

        response = requests.post(
            f"{WHATSAPP_API_URL}media", headers=headers, files=files
        )
        logging.debug(f"Response : {response.json()}")

        if response.status_code == 200:
            media_id = response.json()["id"]
            logging.debug(f"Media Id: {media_id}")
            return media_id
        else:
            logging.error(f"Failed to send message: {response.text}")
            return None

        # if response.status_code == 200:
        #     media_id = response.json()[id]

        #     return jsonify({"media_id": media_id}), 200
        # else:
        #     return jsonify({"error": response.json()}), response.status_code


# def testMedia():
#     card = "The Star"
#     return upload_image(card)


@app.route("/")
def home():
    return jsonify({"status": "success", "message": "Hello World"}), 200


if __name__ == "__main__":
    app.run(port=5001, debug=True)
