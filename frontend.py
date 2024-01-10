from flask import Flask, request, jsonify, render_template
from redis import Redis
import requests

app = Flask(__name__)
redis_client = Redis.from_url("redis://localhost:6379")

@app.route('/get_matrix_state')
def get_matrix_state():
    try:
        matrix_state = redis_client.get(':matrix_state')

        matrix = matrix_state.decode('utf-8') if matrix_state else '[]'

        return jsonify(matrix)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_conversations')
def get_conversations():
    try:
        # Fetch conversations from Redis queue "agent_conversations"
        conversations = redis_client.lrange(':agent_conversations', 0, -1)[::-1]

        # Convert byte strings to regular strings
        conversations = [conversation.decode('utf-8') for conversation in conversations]

        return jsonify(conversations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('frontend.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/embeddings', methods=['POST'])
def embeddings():
    # Get data from the request
    data = request.json

    # Extract values from the payload
    model = data.get('model')
    prompt = data.get('prompt')

    # Create the payload for the POST request to the external API
    payload = {
        "model": model,
        "prompt": prompt
    }

    # Make the POST request to the external API
    external_api_url = "http://localhost:11434/api/embeddings"
    response = requests.post(external_api_url, json=payload)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response from the external API
        result = response.json()
        return jsonify(result)
    else:
        # If the request was not successful, return an error message
        return jsonify({"error": f"Failed to generate data. Status code: {response.status_code}"}), response.status_code

@app.route('/generate', methods=['POST'])
def generate():
    # Get data from the request
    data = request.json

    # Extract values from the payload
    model = data.get('model')
    prompt = data.get('prompt')

    # Create the payload for the POST request to the external API
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    # Make the POST request to the external API
    external_api_url = "http://localhost:11434/api/generate"
    response = requests.post(external_api_url, json=payload)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response from the external API
        result = response.json()
        return jsonify(result)
    else:
        # If the request was not successful, return an error message
        return jsonify({"error": f"Failed to generate data. Status code: {response.status_code}"}), response.status_code

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
