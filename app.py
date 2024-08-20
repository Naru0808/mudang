from flask import Flask, render_template, request, jsonify
import openai
import os
import asyncio
from cachelib import SimpleCache
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

client = openai.OpenAI(api_key=API_KEY)
assistant_id = 'asst_YdIRpe6lAQIw9OBU9UOIFnJG'
thread_id = None

app = Flask(__name__)
cache = SimpleCache()

@app.route("/", methods=["GET"])
async def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
async def chat():
    global thread_id
    message = request.json.get("message", "")

    # Use the message as the key to check the cache
    cache_key = f"response-{message}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return jsonify({"response": cached_response})

    if not thread_id:
        thread = await asyncio.to_thread(client.beta.threads.create)
        thread_id = thread.id

    # Send user's message to the thread
    await asyncio.to_thread(
        client.beta.threads.messages.create,
        thread_id=thread_id,
        role="user",
        content=message
    )

    # Initiate a run
    run = await asyncio.to_thread(
        client.beta.threads.runs.create,
        thread_id=thread_id, 
        assistant_id=assistant_id,
    )

    # Wait for run completion
    while run.status != "completed":
        await asyncio.sleep(0.2)
        run = await asyncio.to_thread(
            client.beta.threads.runs.retrieve,
            thread_id=thread_id, 
            run_id=run.id
        )

    # Retrieve messages and find the latest assistant's response
    responses = await asyncio.to_thread(
        client.beta.threads.messages.list,
        thread_id=thread_id
    )
    assistant_message = next((msg.content[0].text.value for msg in responses.data if msg.role == "assistant"), "No response found")

    # Cache the response before returning it
    cache.set(cache_key, assistant_message, timeout=50)  # Cache timeout of 50 seconds
    return jsonify({"response": assistant_message})

@app.route("/reset", methods=["POST"])
async def reset():
    global thread_id
    thread_id = None
    return jsonify({"message": "Chat has been reset."})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
