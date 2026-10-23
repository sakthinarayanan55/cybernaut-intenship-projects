
import base64
import os

from flask import Flask, jsonify, render_template, request, send_from_directory

from src.predictor import SpamPredictor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_chart_b64():
    for rel in [
        os.path.join("public", "reports", "top_keywords.png"),
        os.path.join("reports", "top_keywords.png"),
        os.path.join("public", "top_keywords.png"),
    ]:
        full = os.path.join(BASE_DIR, rel)
        if os.path.exists(full):
            try:
                with open(full, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass
    return ""


TOP_KEYWORDS_B64 = load_chart_b64()

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates")
)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024   # 1 MB request limit

predictor = SpamPredictor(model_dir=os.path.join(BASE_DIR, "models"))


@app.route("/", methods=["GET", "POST"])
@app.route("/api/index", methods=["GET", "POST"])
@app.route("/api/index.py", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return predict()
    return render_template(
        "index.html",
        metrics=predictor.metrics,
        top_keywords_b64=TOP_KEYWORDS_B64
    )


@app.route("/predict", methods=["GET", "POST"])
@app.route("/api/predict", methods=["GET", "POST"])
@app.route("/api/index/predict", methods=["GET", "POST"])
@app.route("/api/index.py/predict", methods=["GET", "POST"])
def predict():
    data = request.get_json(silent=True) or request.form or request.args
    text = data.get("text", "")
    try:
        return jsonify(predictor.predict(text))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500


@app.route("/api/metrics")
@app.route("/metrics")
def metrics():
    return jsonify(predictor.metrics)


@app.route("/reports/<path:filename>")
@app.route("/api/reports/<path:filename>")
@app.route("/top_keywords.png")
def reports(filename="top_keywords.png"):
    for folder in [
        os.path.join(BASE_DIR, "public", "reports"),
        os.path.join(BASE_DIR, "public"),
        os.path.join(BASE_DIR, "reports"),
    ]:
        p = os.path.join(folder, filename)
        if os.path.exists(p):
            return send_from_directory(folder, filename, mimetype="image/png")
    return send_from_directory(os.path.join(BASE_DIR, "reports"), "top_keywords.png", mimetype="image/png")


@app.route("/health")
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.errorhandler(404)
def handle_404(e):
    if request.method == "POST":
        return predict()
    if request.path.startswith("/api/metrics"):
        return metrics()
    if "top_keywords.png" in request.path or request.path.startswith(("/reports", "/api/reports")):
        filename = request.path.split("/")[-1] or "top_keywords.png"
        return reports(filename)
    return render_template(
        "index.html",
        metrics=predictor.metrics,
        top_keywords_b64=TOP_KEYWORDS_B64
    ), 200


@app.errorhandler(405)
def handle_405(e):
    if request.method == "POST":
        return predict()
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
