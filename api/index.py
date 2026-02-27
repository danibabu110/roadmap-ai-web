from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
# GEMINI VERSION FINAL

app = Flask(__name__)
CORS(app)

# ===============================
# ENV VARIABLES
# ===============================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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
# GEMINI REQUEST
# ===============================
def ask_gemini(messages):

    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key not configured."

    try:
        prompt = messages[-1]["content"]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        r = requests.post(url, json=payload, timeout=30)
        result = r.json()

        if "candidates" in result:
            return result["candidates"][0]["content"]["parts"][0]["text"]

        return "⚠️ Gemini busy. Try again."

    except:
        return "⚠️ Gemini request failed."

# ===============================
# AI INDUSTRY CERTS
# ===============================
def generate_ai_certifications(topic):

    prompt = f"""
Give industry-recognized certifications for learning {topic}.

Return ONLY JSON list like:
[
  {{
    "title":"Certificate name",
    "provider":"Company",
    "type":"Free or Paid",
    "url":"official link"
  }}
]

Include providers like:
Google, AWS, Microsoft, IBM, Meta, Coursera, Udemy.

Maximum 6 items.
"""

    result = ask_gemini([
        {"role": "user", "content": prompt}
    ])

    try:
        return json.loads(result)
    except:
        return []

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

    free_certs = generate_free_certs(node)
    industry_certs = generate_ai_certifications(node)

    return jsonify({
        "free_certifications": free_certs,
        "industry_certifications": industry_certs
    })

@app.route("/api/explain", methods=["POST"])
def explain():
    topic = request.json.get("topic", "")

    explanation = ask_gemini([
        {"role": "user", "content": f"Explain shortly: What is {topic}, why important, how to learn, time required."}
    ])

    return jsonify({"explanation": explanation})

@app.route("/api/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")

    reply = ask_gemini([
        {"role": "user", "content": question}
    ])

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)