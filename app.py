import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import time

from groq import Groq

import json

# from database import get_session, create_or_update_session, clear_session


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

# Initialize the database with database parameters
db_params = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

db = TarotDatabase(db_params)


groq_api_key = "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"
os.environ["GROQ_API_KEY"] = groq_api_key


def ask_llama(prompt):
    try:

        client = Groq()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )

        # print(response)
        # print(response.choices[0].message)
        return response.choices[0].message.content

    except openai.OpenAIError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def ask_openai(prompt, model):
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


def generate_tarot_cards(question, model):
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
            - The accurate card name using 1909 the Rider-Waite tarot deck in words
            - A detailed explanation of what the card signifies in the given position
            - Link the interpretation to the question

            Return the descriptions and summary in the following format without additional heading and footing description:
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

    # "gpt-4o", "gpt-4o-mini", "llama3.1"
    if model == "llama3.1":
        response = ask_llama(prompt)
        return eval(response)
    else:
        response = ask_openai(prompt, model)
        return eval(response)

    # # response = ask_openai(prompt)

    # print(response)

    # return eval(response)


def check_similar(question, past_questions):
    formatted_questions = "\n".join([f"- {q}" for q in past_questions])

    prompt = f"""
        You are a question similarity checker for tarot reading. Below is a list of questions and a target question. Your task is to determine if the target question is similar to any of the questions in the list.

        **Important:**
        - Consider questions similar only if they are asking about the exact same topic or concern (e.g., finances, career, love).
        - Do not consider questions similar if they are about different topics, even if they share similar structures, time frames, or keywords.
        - Pay close attention to the underlying intent and purpose of each question. Only mark them as similar if they are fundamentally asking about the same issue.

        List of Questions:
        {formatted_questions}

        Target Question:
        {question}

        Instructions:

        1. If the target question is similar in both meaning and context to any question in the list, respond with:
        "Similar: '{{target_question}}' is similar to '{{similar_question}}'."
        

        2. If the target question is not similar in meaning or context, respond with:
        no

        Ensure your response accurately reflects the meaning and context of the questions and following the response format without excessive description.
     """

    response = ask_llama(prompt)

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
ACCESS_TOKEN = "EAAQZATIbxyeQBO9ShLvTETB9CKo173Y0NxYwPKiw7gNodNZAoNZAjj4dBw1iElTDqmBq8aThn0ZBkEs985ZCZAmKTh93vQl6h0wlBXrkLAsE154r6oZAFLLIVql5iBt2asKkIyTTIB5zp9EYDIMRUcdhDuBtc5raR833MZCfO6R3SQpdjVmULt9EZB0s2k0jbBjkXXwcO9sKeTvo3GSiTnujVrZBD7w9YZD"
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
                                incoming_msg = message["interactive"]["button_reply"][
                                    "id"
                                ].lower()
                            sender_id = message["from"]

                            print(f"Message: {incoming_msg}")

                            # Retrieve session from the database
                            # session = get_session(sender_id)
                            # print(sender_id)
                            (user_id, plan, enddate) = db.get_plan(str(sender_id))

                            media_id = None
                            free = True
                            buttonId = None
                            buttonLabel = None

                            if plan == "premium" and is_subscription_active(enddate):
                                free = False

                            usage = db.get_usage(user_id)
                            if free and usage >= 5:
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
                                    response_message = "Now, please try to think about your question thoroughly 💭. Once you are decided, tell me through sending a message to me 💬."
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
                                        model = db.get_model(user_id)
                                        tarot_reading = generate_tarot_cards(
                                            incoming_msg, model
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
                                        response_message += (
                                            "Press _'Next'_ to continue."
                                        )

                                        buttonId = "next"
                                        buttonLabel = "Next"

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
                                        response_message += "I am sorry 😓, but I think you have asked similar question before within 1 week time. While I would really want to help you with this, but you may refer back to the previous session by login in at www.tarotmate.com. I hope that those answers may guide you as you go. \n[Note that asking the same question in short period of time is not allowed in tarot reading]"
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
                                        response_message += (
                                            "Press _'Next'_ to continue."
                                        )

                                        buttonId = "next"
                                        buttonLabel = "Next"
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
                                        response_message += "\n\nPlease ask me any other questions if you have, always ready to help and wish you have a good day ahead 🔮"

                                        db.end_session(session[0])

                                        # db.update_session(session_id=session[0],stage='end')

                                        # clear_session(
                                        #     sender_id
                                        # )  # Clear session after the reading is complete
                                else:
                                    response_message = "Welcome to TarotMate, is there anything intriguing in your mind? Please let me help you with tarot reading 🔮. \n\n[Press “Start Now” to begin a new tarot reading journey]"
                                    buttonId = "start"
                                    buttonLabel = "Start Now"

                            print(response_message)

                            if media_id != None:
                                send_whatsapp_pic(sender_id, media_id)
                                time.sleep(1)

                            if buttonId:
                                send_whatsapp_interactive(
                                    sender_id, response_message, buttonId, buttonLabel
                                )
                            else:
                                send_whatsapp_message(sender_id, response_message)

    return jsonify({"status": "success"}), 200


@app.route("/user", methods=["GET"])
def user():
    user_id = request.args.get("userId")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = db.get_user_info(user_id)

    if user:
        (
            name,
            email,
            phone_number,
            age,
            gender,
            model,
            created_at,
            subscription_type,
            subscription_start,
            subscription_end,
            usage,
        ) = user
        user_info = {
            "name": name,
            "email": email,
            "phone_number": phone_number,
            "age": age,
            "gender": gender,
            "model": model,
            "created_at": created_at,
            "subscription_type": subscription_type,
            "subscription_start": subscription_start,
            "subscription_end": subscription_end,
            "usage": usage,
        }
        return jsonify(user_info), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route("/createUser", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        id = data["id"]
        username = data["username"]
        email = data["email"]
        phone_number = data["phone_number"]
        age = data["age"]
        gender = data["gender"]

        print(data)

        user_id = db.create_user(id, username, email, phone_number, age, gender)
        return jsonify({"status": "success", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/userSessions", methods=["GET"])
def user_session():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    sessions = db.get_user_session(user_id)

    if sessions:
        result = []
        for session in sessions:
            session_id, question, stage, session_created, cards, summary = session
            card = json.loads(cards)
            result.append(
                {
                    "session_id": session_id,
                    "question": question,
                    "stage": stage,
                    "session_created": session_created,
                    "cards": card,
                    "summary": summary,
                }
            )
        return jsonify(result), 200
    else:
        return jsonify({"error": "No sessions found"}), 404


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


@app.route("/updateUserModel", methods=["POST"])
def updateUserModel():
    try:
        data = request.get_json()
        id = data["id"]
        model = data["model"]

        db.update_model(id, model)
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/updateUserSubscription", methods=["POST"])
def updateUserSubscription():
    try:
        data = request.get_json()
        id = data["id"]
        plan = data["plan"]
        duration = data["duration"]

        db.update_subscription(id, plan, duration)
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# @app.route("/createUser", methods=["POST"])
# def create_user():
#     try:
#         data = request.get_json()
#         id = data["id"]
#         username = data["username"]
#         email = data["email"]
#         phone_number = data["phone_number"]
#         age = data["age"]
#         gender = data["gender"]
#         model = data["model"]

#         print(data)

#         user_id = db.create_user(id, username, email, phone_number, age, gender,model)
#         return jsonify({"status": "success", "user_id": user_id}), 201
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/getUser", methods=["GET"])
def get_user():
    user_id = request.args.get("userId")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        user = db.get_user_info(user_id)

        if user is None:
            return jsonify(None), 200

        user_info = {
            "name": user[0],
            "email": user[1],
            "phone_number": user[2],
            "age": user[3],
            "gender": user[4],
            "model": user[5],
            "created_at": user[6],
            "subscription_type": user[7],
            "subscription_start": user[8],
            "subscription_end": user[9],
        }

        return jsonify(user_info), 200
    except Exception as e:
        print("Error fetching user:", str(e))
        return jsonify({"message": "Internal server error"}), 500


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
    app.run(port=5001, debug=True)
