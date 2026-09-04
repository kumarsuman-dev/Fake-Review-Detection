import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from preprocessing import preprocess_text

# Get absolute directory path
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(basedir, "templates"),
    static_folder=os.path.join(basedir, "statics"),
    static_url_path="/static"
)

# Global model holders
_word2vec_model = None
_svm_model = None

def get_models():
    """Lazy load models with error catching to ensure serverless resilience."""
    global _word2vec_model, _svm_model
    if _word2vec_model is None or _svm_model is None:
        from model import load_models
        _word2vec_model, _svm_model = load_models()
    return _word2vec_model, _svm_model

@app.route("/")
@app.route("/api")
@app.route("/api/index")
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        # Fallback if template is located in alternate path in serverless container
        alt_paths = [
            os.path.join(basedir, "templates", "index.html"),
            os.path.join(os.getcwd(), "templates", "index.html"),
            os.path.join(os.path.dirname(basedir), "templates", "index.html"),
            os.path.join("/var/task", "templates", "index.html")
        ]
        for p in alt_paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
        return f"Template Error: {str(e)} | Basedir: {basedir} | CWD: {os.getcwd()} | Files: {os.listdir(basedir) if os.path.exists(basedir) else []}", 500

@app.route("/static/<path:filename>")
def serve_static(filename):
    for base in [os.path.join(basedir, "statics"), os.path.join(os.getcwd(), "statics"), os.path.join("/var/task", "statics")]:
        fp = os.path.join(base, filename)
        if os.path.exists(fp):
            return send_from_directory(base, filename)
    return f"Static file {filename} not found", 404

@app.route("/api/health")
@app.route("/health")
@app.route("/api/index/health")
def health():
    models_ready = False
    model_err = None
    try:
        w2v, svm = get_models()
        models_ready = (w2v is not None and svm is not None)
    except Exception as e:
        model_err = str(e)

    return jsonify({
        "status": "healthy",
        "models_ready": models_ready,
        "model_error": model_err,
        "python_version": sys.version,
        "basedir": basedir,
        "cwd": os.getcwd()
    })

@app.route("/analyze", methods=["POST"])
@app.route("/api/analyze", methods=["POST"])
@app.route("/api/index/analyze", methods=["POST"])
def analyze():
    """
    API endpoint to analyze reviews from any e-commerce product URL or direct raw review text.
    """
    try:
        from model import classify_reviews
        w2v_model, svm_clf = get_models()
    except Exception as e:
        return jsonify({"error": f"Model loading failed: {str(e)}"}), 500

    data = request.json or {}
    url = data.get("url", "").strip()
    raw_text = data.get("text", "").strip()

    # Handle Direct Raw Text Input
    if raw_text:
        lines = [line.strip() for line in raw_text.split("\n") if len(line.strip()) > 5]
        if not lines:
            lines = [raw_text]

        preprocessed_reviews = []
        for review_text_raw in lines:
            review_text_processed = preprocess_text(review_text_raw)
            rating = float(data.get("rating", 5.0))
            preprocessed_reviews.append({
                "Review Text": review_text_processed,
                "Rating": rating,
                "Original Review Text": review_text_raw
            })

        detailed_predictions = classify_reviews(preprocessed_reviews, w2v_model, svm_clf)

        response_reviews = []
        for r, p in zip(preprocessed_reviews, detailed_predictions):
            label = "Fake (Computer Generated)" if p["prediction"] == 1 else "Real (Original)"
            response_reviews.append({
                "Review": r["Original Review Text"],
                "Rating": r["Rating"],
                "Prediction": label,
                "prediction_code": p["prediction"],
                "confidence": p["confidence"],
                "word_count": p["word_count"],
                "uppercase_ratio": p["uppercase_ratio"],
                "avg_word_len": p["avg_word_len"]
            })

        return jsonify({
            "is_demo": False,
            "platform": "Direct Text / Universal",
            "reviews": response_reviews
        })

    # Handle URL input
    if not url:
        return jsonify({"error": "No URL or review text provided"}), 400

    try:
        from scraper import scrape_reviews
        reviews, is_demo, platform_name, notice_message = scrape_reviews(url)
    except Exception as e:
        return jsonify({"error": f"Scraping error: {str(e)}"}), 500

    if not reviews:
        return jsonify({"error": notice_message or "No customer reviews found for this product listing."}), 404

    preprocessed_reviews = []
    for item in reviews:
        review_text_raw = item.get("Review Text", "")
        review_text_processed = preprocess_text(review_text_raw)

        try:
            rating = float(item.get("Rating", 5.0))
        except (ValueError, TypeError):
            rating = 5.0

        preprocessed_reviews.append({
            "Review Text": review_text_processed,
            "Rating": rating,
            "Original Review Text": review_text_raw
        })

    detailed_predictions = classify_reviews(preprocessed_reviews, w2v_model, svm_clf)

    response_reviews = []
    for r, p in zip(preprocessed_reviews, detailed_predictions):
        label = "Fake (Computer Generated)" if p["prediction"] == 1 else "Real (Original)"
        response_reviews.append({
            "Review": r["Original Review Text"],
            "Rating": r["Rating"],
            "Prediction": label,
            "prediction_code": p["prediction"],
            "confidence": p["confidence"],
            "word_count": p["word_count"],
            "uppercase_ratio": p["uppercase_ratio"],
            "avg_word_len": p["avg_word_len"]
        })

    return jsonify({
        "is_demo": is_demo,
        "platform": platform_name,
        "message": notice_message,
        "reviews": response_reviews
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
