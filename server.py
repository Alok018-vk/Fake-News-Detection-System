import os
import json
import joblib
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

from train_helpers import clean_text, is_news_text, classify_text_type
from news_graph import analyze_news_structure
from credibility_scorer import greedy_credibility_score
from fact_checker import (
    extract_claims,
    csp_check_claims,
    check_with_gemini,
    fetch_india_news,
    compare_with_current_news
)

app = Flask(__name__, static_folder="static")

print("[*] Loading ML models and artifacts...")
vectorizer = joblib.load("model/vectorizer.pkl")
model = joblib.load("model/model.pkl")

with open("model/results.json", "r") as f:
    results_data = json.load(f)

clusters_data = {}
if os.path.exists("model/clusters.json"):
    with open("model/clusters.json", "r") as f:
        clusters_data = json.load(f)

print("[+] Models and artifacts loaded successfully.")

HISTORY_FILE = "analysis_history.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


@app.route("/api/models", methods=["GET"])
def get_model_info():
    names = [k for k in results_data.keys() if k != "best_model"]
    acc = [results_data[n]["accuracy"] for n in names]

    bandit_data = [
        {"arm": n, "reward_accuracy": results_data[n]["accuracy"]}
        for n in names
    ]

    best_model_name = results_data.get("best_model", "Random Forest")
    cm = results_data[best_model_name]["confusion_matrix"]

    return jsonify({
        "models": names,
        "accuracies": acc,
        "best_model": best_model_name,
        "results": results_data,
        "confusion_matrix": {
            "model": best_model_name,
            "matrix": cm,
            "labels": ["Fake", "Real"]
        },
        "bandit": bandit_data,
        "clusters": clusters_data
    })


DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or ""


@app.route("/api/analyze", methods=["POST"])
def analyze_article():
    data = request.get_json(force=True, silent=True) or {}
    user_text = (data.get("text") or "").strip()
    api_key = (data.get("api_key") or DEFAULT_GEMINI_KEY or "").strip()

    if not user_text:
        return jsonify({"detail": "Text cannot be empty."}), 400

    text_type = classify_text_type(user_text)
    is_news, news_reason = is_news_text(user_text)

    cleaned = clean_text(user_text)
    vec = vectorizer.transform([cleaned])
    prediction = int(model.predict(vec)[0])
    proba = [float(p) for p in model.predict_proba(vec)[0]]
    fake_prob = round(proba[0] * 100, 1)
    real_prob = round(proba[1] * 100, 1)

    cred_score, breakdown, cred_verdict = greedy_credibility_score(user_text)

    graph_res = analyze_news_structure(user_text)

    claims = extract_claims(user_text)
    if claims:
        claim_results, consistency_score = csp_check_claims(claims)
    else:
        claim_results = []
        consistency_score = 50

    ml_real_pct = real_prob
    composite_score = round(
        (ml_real_pct * 0.40) +
        (cred_score * 0.30) +
        (graph_res["structure_score"] * 0.15) +
        (consistency_score * 0.15),
        1
    )

    if composite_score >= 65:
        overall_verdict = "REAL"
        overall_desc = "Analysis indicates high probability of authentic journalism."
    elif composite_score >= 40:
        overall_verdict = "UNCERTAIN"
        overall_desc = "Mixed signals detected. Exercise scrutiny and verify primary sources."
    else:
        overall_verdict = "FAKE"
        overall_desc = "High probability of deceptive, synthetic, or fabricated content."

    result_payload = {
        "text_type": {
            "type": text_type,
            "is_news": is_news,
            "reason": news_reason
        },
        "ml_prediction": {
            "best_model": results_data.get("best_model", "Random Forest"),
            "prediction": "REAL" if prediction == 1 else "FAKE",
            "fake_probability": fake_prob,
            "real_probability": real_prob
        },
        "credibility": {
            "score": cred_score,
            "breakdown": breakdown,
            "verdict": cred_verdict
        },
        "graph_analysis": {
            "num_keywords": graph_res["num_keywords"],
            "num_connections": graph_res["num_connections"],
            "connected_components": graph_res["connected_components"],
            "max_depth": graph_res["max_depth"],
            "graph_density": graph_res["graph_density"],
            "structure_score": graph_res["structure_score"],
            "bfs_order": graph_res["bfs_order"],
            "dfs_order": graph_res["dfs_order"],
            "graph": graph_res["graph"],
            "keyword_freq": graph_res["keyword_freq"]
        },
        "csp": {
            "claims_count": len(claims),
            "claims": claim_results,
            "consistency_score": consistency_score
        },
        "composite": {
            "score": composite_score,
            "verdict": overall_verdict,
            "description": overall_desc
        }
    }

    history = load_history()
    snippet = user_text[:120] + ("..." if len(user_text) > 120 else "")
    history_entry = {
        "id": len(history) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text_snippet": snippet,
        "verdict": overall_verdict,
        "composite_score": composite_score,
        "ml_prediction": "REAL" if prediction == 1 else "FAKE",
        "real_probability": real_prob,
        "fake_probability": fake_prob,
        "credibility_score": cred_score,
        "consistency_score": consistency_score
    }
    history.append(history_entry)
    save_history(history)

    return jsonify(result_payload)


@app.route("/api/history", methods=["GET"])
def get_history():
    history = load_history()
    history.reverse()
    return jsonify({"history": history, "total": len(history)})


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    save_history([])
    return jsonify({"message": "History cleared successfully."})


@app.route("/api/history/<int:entry_id>", methods=["DELETE"])
def delete_history_entry(entry_id):
    history = load_history()
    history = [h for h in history if h["id"] != entry_id]
    save_history(history)
    return jsonify({"message": "Entry deleted.", "total": len(history)})


@app.route("/api/india-news", methods=["POST"])
def get_india_news():
    data = request.get_json(force=True, silent=True) or {}
    api_key = (data.get("api_key") or "").strip()
    if not api_key:
        return jsonify({
            "source": "curated_archive",
            "news": (
                "[Economy] RBI maintains repo rate amid steady inflation forecast - "
                "Central bank signals sustained growth and controlled liquidity.\n"
                "[Technology] ISRO initiates preliminary checkout for next lunar landing mission - "
                "Scientific payloads undergo environmental testing in Bengaluru.\n"
                "[Infrastructure] National Highway expansion reaches record milestone - "
                "Transport ministry records over 12,000 km completed within fiscal timeline.\n"
                "[Governance] Supreme Court reviews constitutional bench guidelines on digital data privacy - "
                "Court seeks comprehensive compliance frameworks from regulatory authorities.\n"
                "[Renewables] Solar capacity crosses major gigawatt landmark in western states - "
                "Grid integration projects accelerate clean power distribution."
            )
        })
    news_text, err = fetch_india_news(api_key)
    if err:
        return jsonify({"source": "gemini", "error": err})
    return jsonify({"source": "gemini", "news": news_text})


@app.route("/api/compare-news", methods=["POST"])
def compare_news():
    data = request.get_json(force=True, silent=True) or {}
    user_text = (data.get("text") or "").strip()
    api_key = (data.get("api_key") or "").strip()
    if not api_key:
        return jsonify({
            "detail": "Gemini API Key required for live event cross-referencing."
        }), 400
    result, error = compare_with_current_news(user_text, api_key)
    if error:
        return jsonify({"error": error})
    return jsonify({"result": result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8501))
    print(f"[*] RAW_VISION Brutalist Core serving on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
