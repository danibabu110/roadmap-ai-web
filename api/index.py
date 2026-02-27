from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests

app = Flask(__name__)
CORS(app)

# ===============================
# ENV VARIABLES
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
# AI REQUEST (OPENROUTER FREE)
# ===============================
def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "⚠️ AI key not configured."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://roadmap-ai-web.vercel.app",
        "X-Title": "Roadmap AI Mentor"
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

        result = r.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]

        return "⚠️ AI temporarily unavailable."

    except:
        return "⚠️ AI request failed."

# ===============================
# AI INDUSTRY CERTIFICATIONS
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

Include providers:
Google, AWS, Microsoft, IBM, Meta, Coursera, Udemy.

Maximum 6 items.
"""

    result = ask_ai([
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

    explanation = ask_ai([
        {"role": "system", "content": "Explain shortly: What it is, Why important, How to learn, Time required."},
        {"role": "user", "content": topic}
    ])

    return jsonify({"explanation": explanation})

@app.route("/api/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")

    reply = ask_ai([
        {"role": "system", "content": "You are an AI learning mentor. Be concise and encouraging."},
        {"role": "user", "content": question}
    ])

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)