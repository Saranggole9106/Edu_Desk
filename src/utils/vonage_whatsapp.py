import vonage
import os

def send_whatsapp_message(to, body):
    client = vonage.Client(
        key=os.environ['VONAGE_API_KEY'],
        secret=os.environ['VONAGE_API_SECRET']
    )
    response = client.post(
        'https://api.nexmo.com/v0.1/messages',
        {
            "from": {"type": "whatsapp", "number": os.environ['VONAGE_WHATSAPP_NUMBER']},
            "to": {"type": "whatsapp", "number": to},
            "message": {
                "content": {
                    "type": "text",
                    "text": body
                }
            }
        }
    )
    return response 