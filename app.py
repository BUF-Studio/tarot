import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

import json
from database import get_session, create_or_update_session, clear_session


import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set your API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# @app.route('/ask', methods=['POST'])
def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use a supported model
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )


        return response.choices[0].message['content'].strip()
    except openai.OpenAIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


def generate_tarot_cards(question):
    prompt = f"""
    The user has asked the following question: "{question}".

    Draw six tarot cards for a reading. Each card should have a description. The positions are:
    1. You
    2. Situation / Context
    3. Challenge
    4. Development
    5. Outcome
    6. Advice

    Provide a summary of the reading based on the six cards drawn.

    Return the descriptions and summary in the following format:
    {{
        "cards": [
            {{"position": "You", "description": "Description of the first card"}},
            {{"position": "Situation / Context", "description": "Description of the second card"}},
            {{"position": "Challenge", "description": "Description of the third card"}},
            {{"position": "Development", "description": "Description of the fourth card"}},
            {{"position": "Outcome", "description": "Description of the fifth card"}},
            {{"position": "Advice", "description": "Description of the sixth card"}}
        ],
        "summary": "Summary of the reading"
    }}
    """
    response = ask_openai(prompt)
    
    return eval(response)

# VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN')

WHATSAPP_API_URL = 'https://graph.facebook.com/v17.0/391867514003939/messages'
ACCESS_TOKEN = 'EAAQZATIbxyeQBOzVx93HZBA8FKlj1yi3GvBBdEJtGSD7wmEZCeF9EI97YLwIa4Vku8EA02yjs5ZChH2ITBa2jb697ZC1rQUHRrZBjj1awAtRzZB6cppuOEyBzLKqYZBcW722GZAi7tZBX78ahtfzSdizFgRbqcIbGy0ewFQIZAM6CtgFVE2GO1kl0GhZCLF3ZAZC2TDneqIJETdZA6PDoIwAlSynyD17fkU7zi5'
VERIFY_TOKEN = '123456'

def send_whatsapp_message(to, message):
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'text': {'body': message}
    }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        logging.debug(f"Message sent successfully: {response.json()}")
    else:
        logging.error(f"Failed to send message: {response.text}")



@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    
    if data['object'] == 'whatsapp_business_account':
        for entry in data['entry']:
            for change in entry['changes']:
                if 'messages' in change['value']:
                    for message in change['value']['messages']:
                        if 'text' in message:
                            incoming_msg = message['text']['body'].lower()
                            sender_id = message['from']

                            print(f"Message: {incoming_msg}")

                            
                            # Retrieve session from the database
                            session = get_session(sender_id)



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
                                stage = 'start'
                                
                            if incoming_msg == 'start now':
                                response_message = "Great! Please focus on your question and type it below."
                                stage = 'question'
                                create_or_update_session(sender_id, '', '', '', 0, stage)
                            elif stage == 'question':
                                question = incoming_msg
                                tarot_reading = generate_tarot_cards(incoming_msg)
                                # print(tarot_reading)
                                cards = tarot_reading['cards']
                                summary = tarot_reading['summary']

                                split_description = cards[0]['description'].split(' - ')

                                response_message = f"Question: {incoming_msg}. \n\n"
                                response_message += f"*{cards[0]['position']} : {split_description[0]}* \n\n"
                                response_message += f"{split_description[1]}\n\n"
                                response_message += "Type _'Next'_ to continue."

                                current_card = 1
                                stage = 'next_card'
                                create_or_update_session(sender_id, question, json.dumps(cards), summary, current_card, stage)
                            elif stage == 'next_card':
                                if current_card < 6:
                                    current_card_data = cards[current_card]

                                    split_description = cards[current_card]['description'].split(' - ')

                                    response_message = f"*{current_card_data['position']} : {split_description[0]}*\n\n"
                                    response_message += f"{split_description[1]}\n\n"
                                    response_message += "Type _'Next'_ to continue."
                                    current_card += 1
                                    create_or_update_session(sender_id, question, json.dumps(cards), summary, current_card, stage)
                                else:
                                    response_message = "*Summary*\n\n"
                                    response_message += summary
                                    clear_session(sender_id)  # Clear session after the reading is complete
                            else:
                                response_message = "Type _'Start Now'_ to begin the tarot reading."

                            print(response_message)

                            send_whatsapp_message(sender_id, response_message)

    return jsonify({"status": "success"}), 200






@app.route('/clear', methods=['GET'])
def clear():
    clear_session('60189869935')
    return jsonify({"status": "success"}), 200


@app.route('/webhook', methods=['GET'])
def webhook_setup():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # print("Received data: ")



    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Forbidden', 403
    return 'Bad Request', 400
    # return challenge, 200








@app.route('/')
def home():
    return "Hello, Flask!"


if __name__ == '__main__':
    app.run(port=5001,debug=True)


