from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from lunardate import LunarDate
from datetime import datetime
import json
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load OpenAI API key
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=API_KEY)
assistant_id = 'asst_YdIRpe6lAQIw9OBU9UOIFnJG'
thread_id = None

app = Flask(__name__)
CORS(app)

# 간지 목록
gans = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
jis = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']

def get_60_ganji(index):
    return gans[index % 10] + jis[index % 12]

def calculate_day_ganji(date):
    base = datetime(1900, 1, 31)
    days = (date - base).days
    return get_60_ganji(days)

def calculate_year_ganji(date, ipchun_table):
    y = date.year
    ipchun = ipchun_table.get(str(y))
    if ipchun:
        ipchun_dt = datetime.strptime(ipchun, "%Y-%m-%d %H:%M")
        if date < ipchun_dt:
            y -= 1
    return get_60_ganji((y - 1984 + 60) % 60)

def calculate_month_ganji(date, jeol_table):
    y, m = date.year, date.month
    key = f"{y}-{str(m).zfill(2)}"
    jeol = jeol_table.get(key)
    if jeol:
        jeol_dt = datetime.strptime(jeol, "%Y-%m-%d %H:%M")
        if date < jeol_dt:
            m -= 1
            if m == 0:
                y -= 1
                m = 12
    return get_60_ganji(((y - 1984) * 12 + (m - 1)) % 60)

def calculate_hour_ganji(day_gan, hour):
    gan_idx = gans.index(day_gan)
    branch_idx = hour // 2 % 12
    stem_idx = (gan_idx * 2 + branch_idx) % 10
    return gans[stem_idx] + jis[branch_idx]

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

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    while run.status != "completed":
        time.sleep(0.2)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    responses = client.beta.threads.messages.list(thread_id=thread_id)
    assistant_message = next((msg.content[0].text.value for msg in responses.data if msg.role == "assistant"), "No response found")

    return jsonify({"response": assistant_message})

@app.route("/reset", methods=["POST"])
def reset():
    global thread_id
    thread_id = None
    return jsonify({"message": "Chat has been reset."})

@app.route('/calculate-saju', methods=['POST'])
def calculate_saju():
    try:
        data = request.json
        is_lunar = data.get('isLunar', False)
        year = data['year']
        month = data['month']
        day = data['day']
        hour = data['hour']
        leap = data.get('leap', False)

        with open('ipchun.json', encoding='utf-8') as f:
            ipchun_table = json.load(f)
        with open('jeol.json', encoding='utf-8') as f:
            jeol_table = json.load(f)

        if is_lunar:
            lunar = LunarDate(year, month, day, leap)
            date = lunar.toSolarDate()
        else:
            date = datetime(year, month, day)

        year_ganji = calculate_year_ganji(date, ipchun_table)
        month_ganji = calculate_month_ganji(date, jeol_table)
        day_ganji = calculate_day_ganji(date)
        hour_ganji = calculate_hour_ganji(day_ganji[0], hour)

        return jsonify({
            'solar': date.strftime('%Y-%m-%d'),
            'year': year_ganji,
            'month': month_ganji,
            'day': day_ganji,
            'hour': hour_ganji
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/convert-lunar', methods=['POST'])
def convert_lunar():
    try:
        data = request.json
        to = data.get("to")
        year = data['year']
        month = data['month']
        day = data['day']
        leap = data.get('leap', False)

        if to == 'solar':
            solar = LunarDate(year, month, day, leap).toSolarDate()
            return jsonify({"solar": solar.strftime('%Y-%m-%d')})
        elif to == 'lunar':
            solar = datetime(year, month, day)
            lunar = LunarDate.fromSolarDate(solar.year, solar.month, solar.day)
            return jsonify({
                "lunar": f"{lunar.year}-{str(lunar.month).zfill(2)}-{str(lunar.day).zfill(2)}",
                "leap": lunar.isleap()
            })
        else:
            return jsonify({"error": "Invalid conversion type"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
