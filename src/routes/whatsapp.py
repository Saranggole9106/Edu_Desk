from flask import Blueprint, request, jsonify
from utils.vonage_whatsapp import send_whatsapp_message

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.json
    to = data.get('to')
    body = data.get('body')
    if not to or not body:
        return jsonify({'error': 'Missing "to" or "body"'}), 400
    try:
        response = send_whatsapp_message(to, body)
        return jsonify({'status': 'sent', 'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 