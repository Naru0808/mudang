<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>사주팔자 계산기</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color: #f8f9fa; font-family: 'Noto Sans KR', sans-serif; }
    .container { padding-top: 20px; max-width: 800px; }
    .form-section {
      background: #fff; padding: 15px; margin-bottom: 20px;
      border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .form-row { display: flex; align-items: center; margin-bottom: 10px; }
    .form-row > label { margin-right: 10px; width: 80px; }
    .form-row > div { flex-grow: 1; }
    .message-window {
      background-color: #ffffff;
      border: 2px dashed #bbb;
      padding: 20px;
      border-radius: 10px;
      margin-top: 20px;
      font-size: 1rem;
      line-height: 1.6;
    }
    .btn-group { margin-top: 10px; }
    .loading-message { font-style: italic; color: #777; margin-top: 10px; }
  </style>
</head>
<body>

<div class="container">
  <h3>정확한 사주 계산기</h3>
  <form id="birthdayForm">
    <div class="form-section">
      <div class="form-row">
        <label>양력/음력</label>
        <div>
          <select id="calendarType" class="form-select">
            <option value="solar">양력</option>
            <option value="lunar">음력</option>
          </select>
        </div>
        <label>윤달</label>
        <div>
          <select id="leap" class="form-select">
            <option value="false">아니오</option>
            <option value="true">예</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <label>생년월일</label>
        <div><input id="year" type="number" class="form-control" placeholder="년" /></div>
        <div><input id="month" type="number" class="form-control" placeholder="월" /></div>
        <div><input id="day" type="number" class="form-control" placeholder="일" /></div>
      </div>
      <div class="form-row">
        <label>출생 시간</label>
        <div><input id="hour" type="number" class="form-control" placeholder="시 (0~23)" /></div>
      </div>
      <div class="btn-group">
        <button type="button" class="btn btn-primary" onclick="calculateSaju()">사주 보기</button>
        <button type="button" class="btn btn-secondary" onclick="resetForm()">초기화</button>
      </div>
    </div>
  </form>

  <div class="loading-message" id="loadingMessage" style="display:none;">⏳ 결과를 계산 중입니다...</div>
  <div class="message-window" id="messageWindow">사주 결과가 여기에 표시됩니다.</div>
</div>

<script>
  function calculateSaju() {
    const year = parseInt(document.getElementById("year").value);
    const month = parseInt(document.getElementById("month").value);
    const day = parseInt(document.getElementById("day").value);
    const hour = parseInt(document.getElementById("hour").value);
    const isLunar = document.getElementById("calendarType").value === "lunar";
    const leap = document.getElementById("leap").value === "true";

    document.getElementById("loadingMessage").style.display = "block";
    document.getElementById("messageWindow").innerHTML = "";

    fetch("/calculate-saju", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ year, month, day, hour, isLunar, leap })
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById("loadingMessage").style.display = "none";
      if (data.error) {
        document.getElementById("messageWindow").innerHTML = `<span style="color:red;">오류: ${data.error}</span>`;
      } else {
        document.getElementById("messageWindow").innerHTML = `
          <strong>🗓 날짜 정보</strong><br>
          - 양력: <strong>${data.solar}</strong><br>
          - 음력: <strong>${data.lunar}</strong><br><br>
          <strong>📜 사주 네 기둥</strong><br>
          - 연주: ${data.year}<br>
          - 월주: ${data.month}<br>
          - 일주: ${data.day}<br>
          - 시주: ${data.hour}<br>
        `;
      }
    });
  }

  function resetForm() {
    document.getElementById("birthdayForm").reset();
    document.getElementById("messageWindow").innerHTML = "사주 결과가 여기에 표시됩니다.";
    document.getElementById("loadingMessage").style.display = "none";
  }
</script>

</body>
</html>
