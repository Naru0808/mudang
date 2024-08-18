from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os
import time

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')  # More robust error handling with getenv

client = OpenAI(api_key=API_KEY)
assistant_id = 'asst_YdIRpe6lAQIw9OBU9UOIFnJG'
thread_id = None

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global thread_id
    message = request.json.get("message", "")

    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id

    # Send user's message to the thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    # Initiate a run
    run = client.beta.threads.runs.create(
        thread_id=thread_id, 
        assistant_id=assistant_id,
    )

    # Poll for run completion
    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    # Retrieve messages and find the latest assistant's response
    responses = client.beta.threads.messages.list(thread_id=thread_id)
    assistant_message = next((msg.content[0].text.value for msg in responses.data if msg.role == "assistant"), "No response found")

    return jsonify({"response": assistant_message})


@app.route("/reset", methods=["POST"])
def reset():
    global thread_id
    thread_id = None
    return jsonify({"message": "Chat has been reset."})

if __name__ == "__main__":
    app.run(debug=True)
