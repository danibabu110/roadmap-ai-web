from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests

app = Flask(__name__)
CORS(app)

# ===============================
# ENV (Vercel uses Environment Variables)
# ===============================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# ===============================
# LOAD ROADMAP DATA
# ===============================
current_dir = os.path.dirname(os.path.abspath(__file__))
roadmap_path = os.path.join(current_dir, "roadmaps_master.json")

with open(roadmap_path, "r", encoding="utf-8") as f:
    ROADMAPS = json.load(f)

# ===============================
# HELPERS
# ===============================
def normalize_skill(skill):
    return skill.lower().replace(" ", "-").replace("_", "-")

def generate_free_certs(topic):
    q = topic.replace(" ", "%20")
    return [
        {"title": f"freeCodeCamp - {topic}", "url": f"https://www.freecodecamp.org/news/search/?query={q}"},
        {"title": f"Coursera Free Courses - {topic}", "url": f"https://www.coursera.org/search?query={q}&price=free"},
        {"title": f"edX Free Courses - {topic}", "url": f"https://www.edx.org/search?q={q}&price=free"},
        {"title": f"Google Digital Garage - {topic}", "url": f"https://learndigital.withgoogle.com/digitalgarage/search?q={q}"}
    ]

# ===============================
# AI REQUEST (AUTO FALLBACK)
# ===============================
def ask_openrouter(messages):

    if not OPENROUTER_API_KEY:
        return "⚠️ AI not configured. Add OPENROUTER_API_KEY in Vercel."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://roadmap-ai-web.vercel.app",
        "X-Title": "Roadmap AI Mentor"
    }

    models = [
        "stepfun/step-3.5-flash:free",
        "openai/gpt-oss-120b:free"
    ]

    for model in models:
        try:
            payload = {
                "model": model,
                "messages": messages
            }

            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            result = r.json()

            if "choices" in result:
                return result["choices"][0]["message"]["content"]

        except:
            continue

    return "⚠️ AI is busy right now. Please try again."

# ===============================
# ROUTES
# ===============================
@app.route("/api/")
def home():
    return jsonify({"status": "Backend Running 🚀"})

@app.route("/api/skills", methods=["GET"])
def skills():
    return jsonify(list(ROADMAPS.keys()))

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    skill = normalize_skill(data.get("skill", ""))

    if skill not in ROADMAPS:
        return jsonify({"error": "Skill not found"}), 404

    return jsonify({"roadmap": ROADMAPS[skill]})

@app.route("/api/node-certs", methods=["POST"])
def node_certs():
    node = request.json.get("node", "")
    return jsonify({"certifications": generate_free_certs(node)})

@app.route("/api/explain", methods=["POST"])
def explain():
    topic = request.json.get("topic", "")

    explanation = ask_openrouter([
        {"role": "system", "content": "Explain shortly: What it is, Why important, How to learn, Time required."},
        {"role": "user", "content": topic}
    ])

    return jsonify({"explanation": explanation})

@app.route("/api/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")

    reply = ask_openrouter([
        {"role": "system", "content": "You are an AI learning mentor. Be concise and encouraging."},
        {"role": "user", "content": question}
    ])

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)