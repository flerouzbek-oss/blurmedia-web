import os
import json
import sqlite3
import urllib.request
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

DB_PATH = os.path.expanduser("~/blurmedia.db")
TOKEN = os.environ.get("9061854857:AAEMu5zwdNOurOsKFU1PBdHuzG2sSY_SuH8")

HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BLURMEDIA</title>
<style>
body {
    margin: 0;
    padding: 25px 16px;
    background: #101010;
    color: white;
    font-family: Arial;
}
.container { max-width: 500px; margin: auto; }
h1 { text-align: center; color: #e50914; font-size: 35px; }
.subtitle { text-align: center; color: #aaa; }
.search { background: #202020; padding: 20px; border-radius: 15px; }
input {
    width: 100%; padding: 15px; box-sizing: border-box;
    border: 0; border-radius: 8px; font-size: 17px;
}
button {
    width: 100%; padding: 15px; margin-top: 12px;
    background: #e50914; color: white; border: 0;
    border-radius: 8px; font-weight: bold;
}
.result { background: #202020; padding: 18px; margin-top: 20px; border-radius: 15px; }
video { width: 100%; border-radius: 10px; margin-top: 12px; }
.error { color: #ff5555; text-align: center; }
</style>
</head>
<body>
<div class="container">
<h1>BLURMEDIA 🎬</h1>
<p class="subtitle">KINO OLAMIGA XUSH KELIBSIZ</p>

<div class="search">
<form method="POST">
<input name="code" placeholder="Kino kodini kiriting" required>
<button type="submit">🔎 KINONI TOPISH</button>
</form>
</div>

{% if movie %}
<div class="result">
<h2>{{ movie[1] }}</h2>
<p>🎭 Janr: {{ movie[2] }}</p>
<p>🔢 Kod: {{ movie[0] }}</p>
<p>{{ movie[3] }}</p>
<video controls playsinline preload="metadata">
<source src="/video/{{ movie[0] }}" type="video/mp4">
</video>
</div>
{% endif %}

{% if error %}
<p class="error">{{ error }}</p>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    movie = None
    error = ""

    if request.method == "POST":
        code = request.form.get("code", "").strip()

        with sqlite3.connect(DB_PATH) as db:
            cur = db.cursor()
            cur.execute(
                "SELECT code, title, genre, description FROM movies WHERE code = ?",
                (code,)
            )
            movie = cur.fetchone()

        if not movie:
            error = "❌ Bunday kodli kino topilmadi!"

    return render_template_string(HTML, movie=movie, error=error)


@app.route("/video/<code>")
def show_video(code):
    if not TOKEN:
        return "Bot token sozlanmagan", 500

    with sqlite3.connect(DB_PATH) as db:
        cur = db.cursor()
        cur.execute("SELECT video FROM movies WHERE code = ?", (code,))
        row = cur.fetchone()

    if not row or not row[0]:
        return "Video topilmadi", 404

    file_id = row[0]

    try:
        api_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"

        with urllib.request.urlopen(api_url, timeout=30) as response:
            result = json.loads(response.read())

        if not result.get("ok"):
            return "Telegram videoni topa olmadi", 502

        file_path = result["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

        with urllib.request.urlopen(download_url, timeout=60) as response:
            video_data = response.read()
            content_type = response.headers.get("Content-Type", "video/mp4")

        return Response(video_data, content_type=content_type)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return "Videoni yuklashda xatolik yuz berdi", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

