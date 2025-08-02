import os
from flask import Flask, request, render_template_string
import requests
from dotenv import load_dotenv
import base64

load_dotenv()
app = Flask(__name__)

# Use your actual key or keep it in .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDHFTMIgNpOSwOnGRhgaL2Y960BYV2O56s"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>JEE Question Solver (Gemini 2.0 Flash)</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f9f9f9; text-align: center; padding: 30px; }
        .box { background: white; padding: 20px; border-radius: 10px; display: inline-block; }
        input, button, textarea { margin: 10px; padding: 10px; }
        img { max-width: 500px; margin: 10px auto; }
    </style>
</head>
<body>
    <div class="box">
        <h1>📘 JEE Image Question Solver (Free Gemini API)</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="text" name="image_url" placeholder="Paste Image URL" size="50"><br>
            <input type="file" name="image_file"><br>
            <button type="submit">🧠 Solve with Gemini</button>
        </form>

        {% if image_url %}
        <div><h3>🖼️ Input Image:</h3><img src="{{ image_url }}"></div>
        {% endif %}

        {% if solution %}
        <div><h3>✅ Gemini 2.0 Answer:</h3>
        <pre style="white-space: pre-wrap; text-align: left;">{{ solution }}</pre></div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    image_url = None
    solution = None

    if request.method == 'POST':
        image_url = request.form.get('image_url')
        prompt_text = "Solve this JEE question step-by-step:\n"

        # If uploaded file instead of URL
        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            image_data = base64.b64encode(file.read()).decode()
            image_url = f"data:image/png;base64,{image_data}"  # embed as URL
            prompt_text += f"Here is the image of the question:\n{image_url}"
        elif image_url:
            prompt_text += f"Here is the question image URL: {image_url}"
        else:
            solution = "❌ Please upload an image or paste an image URL."

        # Request to Gemini API
        if image_url:
            try:
                response = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "X-goog-api-key": GEMINI_API_KEY
                    },
                    json={
                        "contents": [{
                            "parts": [{"text": prompt_text}]
                        }]
                    }
                )
                result = response.json()
                solution = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No solution found.")
            except Exception as e:
                solution = f"❌ Error calling Gemini: {str(e)}"

    return render_template_string(HTML_TEMPLATE, image_url=image_url, solution=solution)

if __name__ == '__main__':
    app.run(debug=True)
