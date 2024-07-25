import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set your API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/ask', methods=['POST'])
def ask_openai():
    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    # 
    # return jsonify({'prompt': prompt})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use a supported model
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=15
        )
        return jsonify({'response': response.choices[0].message['content'].strip()})
    except openai.OpenAIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN')

WHATSAPP_API_URL = 'https://graph.facebook.com/v17.0/391867514003939/messages'
ACCESS_TOKEN = 'EAAQZATIbxyeQBOxjxN2DiN6YP26t2LMldZBygGz4RiKBchf8DTifj7k9awFx1bhXNdwLle7jX7zmVp50VptgZCiZBHuDo6gr5l91HK1DvyNIZBnuIxMISsZBvqcax3HpCGby89iyulnI9WcGOyyrEsSfJS2jjagLvepSRUKMi4EkPD0ObDgVJVM97IH41MvSrYJaFTHPXEOryCqV8WZCZBUjjDPf1UgZD'
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
                            if 'capital of france' in incoming_msg:
                                response_message = 'The capital of France is Paris.'
                            else:
                                response_message = "I don't understand that question."

                            print(response_message)
                            
                            send_whatsapp_message(sender_id, response_message)

    return jsonify({"status": "success"}), 200


@app.route('/webhook', methods=['GET'])
def webhook_setup():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

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
    app.run(port=4000,debug=True)


