import time
import requests
import os
import sys

# Change to the directory of this script to load .env easily if needed,
# but we'll just extract from environment or hardcode based on backend/.env
from dotenv import load_dotenv

# Load the root .env file
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(root_env)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TOKEN}"
LOCAL_WEBHOOK_URL = "http://localhost:8000/api/v1/telegram/webhook"


def delete_webhook():
    print("Deleting webhook to enable getUpdates polling...")
    requests.post(f"{API_URL}/deleteWebhook")


def poll_updates():
    offset = None
    print(f"Listening for Telegram messages... Forwarding to {LOCAL_WEBHOOK_URL}")
    while True:
        try:
            # Long polling for updates
            params = {"timeout": 30, "allowed_updates": ["message", "edited_message"]}
            if offset:
                params["offset"] = offset

            resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=40)
            if not resp.ok:
                print(f"Failed to get updates: {resp.text}")
                time.sleep(2)
                continue

            data = resp.json()
            if not data.get("ok"):
                print(f"Error from Telegram API: {data}")
                time.sleep(2)
                continue

            updates = data.get("result", [])
            for update in updates:
                # Forward to local webhook
                try:
                    res = requests.post(LOCAL_WEBHOOK_URL, json=update)
                    print(
                        f"Forwarded update {update['update_id']} -> Local Server [{res.status_code}]"
                    )
                except requests.exceptions.ConnectionError:
                    print(
                        f"Error: Could not connect to local server at {LOCAL_WEBHOOK_URL}. Is it running?"
                    )

                # Increment offset so we don't process the same update again
                offset = update["update_id"] + 1

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    delete_webhook()
    poll_updates()
