from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests

app = Flask(__name__)
CORS(app)

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
        {"title": f"Coursera Free - {topic}", "url": f"https://www.coursera.org/search?query={q}&price=free"},
        {"title": f"edX Free - {topic}", "url": f"https://www.edx.org/search?q={q}&price=free"}
    ]

def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "⚠️ AI not configured."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openrouter/free",
        "messages": messages
    }

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        data = r.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return "⚠️ AI busy."

    except:
        return "⚠️ AI error."

# ===============================
# ROUTES
# ===============================
@app.route("/api/")
def home():
    return jsonify({"status":"Backend Running 🚀"})

@app.route("/api/skills")
def skills():
    return jsonify(list(ROADMAPS.keys()))

@app.route("/api/generate", methods=["POST"])
def generate():
    skill = normalize_skill(request.json.get("skill",""))

    if skill not in ROADMAPS:
        return jsonify({"error":"Skill not found"}),404

    return jsonify({"roadmap":ROADMAPS[skill]})

@app.route("/api/node-certs", methods=["POST"])
def node_certs():
    node = request.json.get("node","")
    return jsonify({
        "free_certifications": generate_free_certs(node),
        "industry_certifications":[]
    })

@app.route("/api/explain", methods=["POST"])
def explain():
    topic = request.json.get("topic","")

    text = ask_ai([
        {"role":"system","content":"Explain shortly: what it is, why important, how to learn."},
        {"role":"user","content":topic}
    ])

    return jsonify({"explanation":text})

@app.route("/api/chat", methods=["POST"])
def chat():
    q = request.json.get("question","")

    reply = ask_ai([
        {"role":"system","content":"You are AI learning mentor."},
        {"role":"user","content":q}
    ])

    return jsonify({"reply":reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)