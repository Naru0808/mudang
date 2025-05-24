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

# 정확한 일주 간지 계산
def calculate_day_ganji(date):
    base_date = datetime(1900, 1, 31)
    delta_days = (date - base_date).days
    idx = delta_days % 60
    return gans[idx % 10] + jis[idx % 12]

# 입춘 기준 연주
def calculate_year_ganji(date, ipchun_table):
    year = date.year
    ipchun_dt = datetime.strptime(ipchun_table.get(str(year)), "%Y-%m-%d %H:%M")
    if date < ipchun_dt:
        year -= 1
    idx = (year - 1984 + 60) % 60
    return gans[idx % 10] + jis[idx % 12]

# 절입일 기준 월주
def calculate_month_ganji(date, jeol_table):
    year, month = date.year, date.month
    key = f"{year}-{str(month).zfill(2)}"
    jeol_dt = datetime.strptime(jeol_table.get(key), "%Y-%m-%d %H:%M")
    if date < jeol_dt:
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    idx = ((year - 1984) * 12 + (month - 1)) % 60
    return gans[idx % 10] + jis[idx % 12]

# 시주 계산
def calculate_hour_ganji(day_gan, hour):
    gan_index = gans.index(day_gan)
    branch_index = hour // 2 % 12
    stem_index = (gan_index * 2 + branch_index) % 10
    return gans[stem_index] + jis[branch_index]

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

        # 음력 날짜 → 양력으로 변환 (간지 계산은 이 변환된 양력을 기준으로)
        if is_lunar:
            lunar = LunarDate(year, month, day, leap)
            solar_date = lunar.toSolarDate()
            lunar_str = f"{year}년 {month}월 {day}일 (윤달: {'예' if leap else '아니오'})"
        else:
            solar_date = datetime(year, month, day)
            lunar_date = LunarDate.fromSolarDate(year, month, day)
            lunar_str = f"{lunar_date.year}년 {lunar_date.month}월 {lunar_date.day}일 (윤달: {'예' if lunar_date.isleap() else '아니오'})"

        # 사주 계산은 변환된 양력 날짜 기준
        year_ganji = calculate_year_ganji(solar_date, ipchun_table)
        month_ganji = calculate_month_ganji(solar_date, jeol_table)
        day_ganji = calculate_day_ganji(solar_date)
        hour_ganji = calculate_hour_ganji(day_ganji[0], hour)

        return jsonify({
            'solar': solar_date.strftime('%Y-%m-%d'),
            'lunar': lunar_str,
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
