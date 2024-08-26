from flask import Flask, request, jsonify
from chatbot_multiagent import submitUserMessage

app = Flask(__name__)

@app.route('/', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '')

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        response = submitUserMessage(user_message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)