from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests

app = Flask(__name__)
# Enable CORS for all routes (Vercel handles routing, but good for local dev)
CORS(app)

# ======================================
# OPENROUTER API
# ======================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# ======================================
# LOAD ROADMAP DATA (Vercel Serverless Safe Path)
# ======================================
current_dir = os.path.dirname(os.path.abspath(__file__))
roadmap_path = os.path.join(current_dir, "roadmaps_master.json")

with open(roadmap_path, "r", encoding="utf-8") as f:
    ROADMAPS = json.load(f)

# ======================================
# HELPER FUNCTIONS
# ======================================
def normalize_skill(skill):
    return skill.lower().replace(" ", "-").replace("_", "-")

def generate_free_certs(topic):
    q = topic.replace(" ", "%20")
    return [
        {"title": f"freeCodeCamp - {topic}", "url": f"https://www.freecodecamp.org/news/search/?query={q}"},
        {"title": f"Coursera Free Courses - {topic}", "url": f"https://www.coursera.org/search?query={q}&price=free"},
        {"title": f"edX Free Courses - {topic}", "url": f"https://www.edx.org/search?q={q}&price=free"},
        {"title": f"Google Digital Garage - {topic}", "url": f"https://learndigital.withgoogle.com/digitalgarage/search?q={q}"},
        {"title": f"Kaggle Learn - {topic}", "url": f"https://www.kaggle.com/search?q={q}"}
    ]

def ask_openrouter(messages):
    if not OPENROUTER_API_KEY:
        return "AI not configured. Add OPENROUTER_API_KEY to Vercel Environment Variables."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://roadmap-project.vercel.app", # Recommended by OpenRouter
        "X-Title": "Roadmap AI App" # Recommended by OpenRouter
    }
    
    payload = {
        # Note: If you have no credits, you can change this to a free model like: "meta-llama/llama-3-8b-instruct:free"
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }
    
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        result = r.json()
        
        # Check for successful response
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
            
        # If it failed, check for a specific error message from OpenRouter
        if "error" in result:
            error_msg = result["error"].get("message", "Unknown OpenRouter Error")
            return f"OpenRouter API Error: {error_msg}"
            
        return f"Unexpected Response: {str(result)}"
        
    except Exception as e:
        return f"Server/Request Error: {str(e)}"

# ======================================
# API ROUTES (Prefixed with /api for Vercel)
# ======================================
@app.route("/api/")
def home():
    return jsonify({"status": "Backend Running on Vercel 🚀"})

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
    certs = generate_free_certs(node)
    return jsonify({"certifications": certs})

@app.route("/api/explain", methods=["POST"])
def explain():
    topic = request.json.get("topic", "")
    explanation = ask_openrouter([
        {"role": "system", "content": "Explain in short sections: What it is, Why important, How to learn, Time required."},
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

# Note: Vercel uses the `app` object directly, so app.run() is only for local dev.
if __name__ == "__main__":
    app.run(debug=True, port=5000)