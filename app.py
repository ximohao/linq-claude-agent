import os
from flask import Flask, request
import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LINQ_TOKEN = os.getenv("LINQ_TOKEN")
LINQ_PHONE = os.getenv("LINQ_PHONE")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_URL = "https://api.linqapp.com/api/partner/v3"

headers = {
    "Authorization": f"Bearer {LINQ_TOKEN}",
    "Content-Type": "application/json"
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    return request.args.get("challenge", ""), 200

@app.route("/webhook", methods=["POST"])
def handle_inbound():
    print("got a request")
    print(request.json)

    event = request.json

    if event["event_type"] == "message.received":
        chat_id = event["data"]["chat"]["id"]
        text = event["data"]["parts"][0]["value"]

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": text}]
        )

        reply = response.content[0].text
        print(f"Claude says: {reply}")

        try:
            r = requests.post(
                f"{BASE_URL}/chats/{chat_id}/messages",
                headers=headers,
                json={
                    "message": {
                        "parts": [{"type": "text", "value": reply}]
                    }
                }
            )
            print(f"Linq response: {r.status_code} {r.text}")
        except Exception as e:
            print(f"Error sending to Linq: {e}")
            print(f"Linq response: {r.status_code} {r.text}")

    return "", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)