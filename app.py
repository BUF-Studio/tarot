import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import time


import json
from database import get_session, create_or_update_session, clear_session


import logging

from postgres import TarotDatabase

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

db = TarotDatabase(db_params)


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


def check_similar(question, past_questions):
    formatted_questions = "\n".join([f"- {q}" for q in past_questions])

    prompt = f"""
        You are a question similarity checker. Below is a list of questions and a target question. Determine if the target question is similar to any of the questions in the list.

        List of Questions:
        {formatted_questions}

        Target Question:
        {question}

        Check if the Target Question is similar to any of the questions in the list. If there is a similar question, respond with:
        "The question '{{question}}' is similar to '{{similar_question}}'"

        If there is no similar question, respond with:
        no

        Provide a clear and concise response.
    """

    response = ask_openai(prompt)

    print("response")
    print(response)

    return response


# user_limit_checker = UserLimitChecker(db_params)
def testRead():
    # db.create_user('1','kks','kks','60189869935')

    # db.create_session('1','ohh','question')
    # db.create_response('1','asg','asx','card','1')
    # plan = db.get_plan("60189869935")
    # response = db.get_response('1')
    # questions = db.get_question('1')
    # usage = db.get_usage('1')
    # db.update_session(session_id='1',current_card=2)
    # sess = db.get_session('1')
    # print(sess)

    # print(plan)
    # print(response)
    # print(usage)
    # print(questions)

    # (user_id, plan, sub_id,enddate) = db.get_plan('60189869935')
    # print(plan)
    pass


# @app.route('/ask', methods=['POST'])

# VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN')

WHATSAPP_API_URL = "https://graph.facebook.com/v20.0/391867514003939/"
ACCESS_TOKEN = "EAAQZATIbxyeQBO5thd4icVMJzK4WawCYr8qZAxbWzf1LWLJzdaK2scdK2ZAIKJ7up6asE1hZAE7VB8bxT8FESi0cZCQM1EVNskHVEG8ZCb2xXwanrzt2aDxRKNi4YWg0C5LZCKh3wQeyiLs7sFgV7SSDLIlBT1PCtLvXsSyX6Ifox3rZBvMJd9T648fJPBq6RgqvBo7ObjOrVgC1MEoEIirUx98OTJ0ZD"
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


def send_whatsapp_interactive(to, message, buttonId, label):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message,
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": buttonId,
                            "title": label,
                        },
                    }
                ]
            },
        },
    }
    response = requests.post(
        WHATSAPP_API_URL + "messages", headers=headers, json=payload
    )

    if response.status_code == 200:
        logging.debug(f"Message sent successfully: {response.json()}")
    else:
        logging.error(f"Failed to send message: {response.text}")


def is_subscription_active(end_date):
    # Get the current date and time
    current_datetime = datetime.now()

    # Convert end_date to a datetime object if it's not already
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(
            end_date
        )  # Adjust if end_date format is different

    # Validate if end_date is greater than the current date and time
    return end_date > current_datetime


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data["object"] == "whatsapp_business_account":
        for entry in data["entry"]:
            for change in entry["changes"]:
                if "messages" in change["value"]:
                    for message in change["value"]["messages"]:
                        if "text" in message or "interactive" in message:
                            if "text" in message:
                                incoming_msg = message["text"]["body"].lower()
                            else:
                                incoming_msg = message["interactive"]["button_reply"]['id'].lower()
                            sender_id = message["from"]

                            print(f"Message: {incoming_msg}")

                            # Retrieve session from the database
                            # session = get_session(sender_id)
                            # print(sender_id)
                            (user_id, plan, enddate) = db.get_plan(str(sender_id))

                            media_id = None
                            free = True
                            buttonId =None
                            buttonLabel =None

                            if plan == "premium" and is_subscription_active(enddate):
                                free = False

                            usage = db.get_usage(user_id)
                            if free and usage >= 6:
                                response_message = "You have reached your limit. Please upgrade plan for more readings"
                            else:

                                session = db.get_session(user_id)

                                print("session")
                                print(session)

                                if session:
                                    question = session[3]
                                    cards = None
                                    summary = ""
                                    try:
                                        response = db.get_response(session[0])

                                        print("response")
                                        print(response)
                                        # Load the JSON string into a Python object
                                        cards = json.loads(response[0])
                                        summary = response[1]
                                    except json.JSONDecodeError as e:
                                        # Handle JSON decoding errors
                                        print("No cards")
                                    except Exception as e:
                                        print("No cards")
                                        # cards = None
                                    # cards = json.loads(session[2])  # Load the JSON string into a Python object
                                    stage = session[1]
                                    current_card = session[2]
                                else:
                                    question = cards = summary = None
                                    current_card = 0
                                    stage = "start"

                                if incoming_msg == "start":
                                    response_message = "Great! Please focus on your question and type it below."
                                    media_id = upload_image("back")
                                    stage = "question"
                                    if not session:
                                        db.create_session(user_id, stage)
                                    # db.update_session(session_id=)
                                    # create_or_update_session(
                                    #     sender_id, "", "", "", 0, stage
                                    # )
                                elif stage == "question":
                                    question = incoming_msg
                                    past_ques = db.get_question(user_id)

                                    repeat = check_similar(question, past_ques)
                                    if repeat == "no":
                                        tarot_reading = generate_tarot_cards(
                                            incoming_msg
                                        )
                                        # print(tarot_reading)
                                        cards = tarot_reading["cards"]
                                        summary = tarot_reading["summary"]

                                        split_description = cards[0][
                                            "description"
                                        ].split(" - ")

                                        response_message = (
                                            f"Question: {incoming_msg}. \n\n"
                                        )
                                        response_message += f"*{cards[0]['position']} : {split_description[0]}* \n\n"
                                        response_message += (
                                            f"{split_description[1]}\n\n"
                                        )
                                        response_message += "Press _'Next'_ to continue."

                                        buttonId='next'
                                        buttonLabel='Next'

                                        media_id = upload_image(split_description[0])

                                        current_card = 1
                                        stage = "next_card"



                                        db.create_response(
                                            session_id=session[0],
                                            cards=json.dumps(cards),
                                            summary=summary,
                                            stage=stage,
                                            current_card=current_card,
                                            question=question,
                                        )
                                    else:
                                        response_message = repeat
                                    # create_or_update_session(
                                    #     sender_id,
                                    #     question,
                                    #     json.dumps(cards),
                                    #     summary,
                                    #     current_card,
                                    #     stage,
                                    # )
                                elif stage == "next_card":
                                    if current_card < 6:
                                        current_card_data = cards[current_card]

                                        split_description = cards[current_card][
                                            "description"
                                        ].split(" - ")

                                        response_message = f"*{current_card_data['position']} : {split_description[0]}*\n\n"
                                        response_message += (
                                            f"{split_description[1]}\n\n"
                                        )
                                        response_message += "Press _'Next'_ to continue."

                                        buttonId='next'
                                        buttonLabel='Next'
                                        media_id = upload_image(split_description[0])

                                        current_card += 1

                                        db.update_session(
                                            session_id=session[0],
                                            current_card=current_card,
                                        )
                                        # create_or_update_session(
                                        #     sender_id,
                                        #     question,
                                        #     json.dumps(cards),
                                        #     summary,
                                        #     current_card,
                                        #     stage,
                                        # )
                                    else:
                                        response_message = "*Summary*\n\n"
                                        response_message += summary

                                        db.end_session(session[0])

                                        # db.update_session(session_id=session[0],stage='end')

                                        # clear_session(
                                        #     sender_id
                                        # )  # Clear session after the reading is complete
                                else:
                                    response_message = (
                                        "Press _'Start Now'_ to begin the tarot reading."
                                    )
                                    buttonId='start'
                                    buttonLabel='Start Now'

                            print(response_message)

                            if media_id != None:
                                send_whatsapp_pic(sender_id, media_id)
                                time.sleep(1)

                            if buttonId:
                                send_whatsapp_interactive(sender_id,response_message,buttonId,buttonLabel)
                            else:
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

        user_id = db.create_user(id, username, email, phone_number)
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


@app.route("/")
def home():
    return jsonify({"status": "success", "message": "Hello World"}), 200


if __name__ == "__main__":
    # testRead()
    app.run(port=5001, debug=True)
