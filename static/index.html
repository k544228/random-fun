<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>隨機跳轉</title>
<style>
  body {
    height: 100vh;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #111;
    font-family: sans-serif;
  }
  button {
    padding: 24px 60px;
    font-size: 24px;
    border: none;
    border-radius: 12px;
    background: #4f8cff;
    color: white;
    cursor: pointer;
  }
  button:disabled {
    background: #555;
    cursor: wait;
  }
  #status {
    position: absolute;
    bottom: 40px;
    color: #aaa;
    font-size: 14px;
  }
</style>
</head>
<body>
  <button id="jumpBtn" onclick="doJump()">跳轉</button>
  <div id="status"></div>

<script>
async function doJump() {
  const btn = document.getElementById('jumpBtn');
  const status = document.getElementById('status');
  btn.disabled = true;
  btn.innerText = '搜尋中...';
  status.innerText = '';

  try {
    const res = await fetch('/api/jump');
    if (!res.ok) throw new Error('failed');
    const data = await res.json();
    status.innerText = `即將前往：${data.source} - ${data.title}`;
    setTimeout(() => {
      window.location.href = data.url;
    }, 800);
  } catch (e) {
    status.innerText = '取得內容失敗，請再試一次';
    btn.disabled = false;
    btn.innerText = '跳轉';
  }
}
</script>
</body>
</html>
