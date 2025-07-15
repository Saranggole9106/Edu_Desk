import vonage
import os

def send_whatsapp_message(to, body):
    client = vonage.Client(
        key=os.environ['VONAGE_API_KEY'],
        secret=os.environ['VONAGE_API_SECRET']
    )
    messages = vonage.Messages(client)
    response = messages.send_message({
        "channel": "whatsapp",
        "message_type": "text",
        "to": to,
        "from": os.environ['VONAGE_WHATSAPP_NUMBER'],
        "text": body,
    })
    return response 
