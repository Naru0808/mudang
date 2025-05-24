from flask import Flask, request, jsonify
from lunardate import LunarDate
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/calculate-saju', methods=['POST'])
def calculate_saju():
    try:
        data = request.get_json()
        year = data['year']
        month = data['month']
        day = data['day']
        hour = data['hour']
        is_lunar = data.get('isLunar', False)
        leap = data.get('leap', False)

        if is_lunar:
            lunar = LunarDate(year, month, day, leap)
            solar_date = lunar.toSolarDate()
            lunar_str = f"{year}년 {month}월 {day}일 (윤달: {'예' if leap else '아니오'})"
        else:
            solar_date = datetime(year, month, day)
            lunar_date = LunarDate.fromSolarDate(year, month, day)
            lunar_str = f"{lunar_date.year}년 {lunar_date.month}월 {lunar_date.day}일 (윤달: {'예' if lunar_date.isleap() else '아니오'})"

        # 임시 간지 결과 예시 (실제는 정밀 계산 필요)
        year_ganji = "신해"
        month_ganji = "병술"
        day_ganji = "무진"
        hour_ganji = "갑사"

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

if __name__ == '__main__':
    app.run(debug=True)
