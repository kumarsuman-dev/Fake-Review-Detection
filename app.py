import os
from flask import Flask, render_template, request, jsonify
from scraper import scrape_reviews
from model import load_models, classify_reviews
from preprocessing import preprocess_text

# Get the absolute path to the directory where app.py is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(basedir, "templates"),
    static_folder=os.path.join(basedir, "statics"),
    static_url_path="/static"
)

# Load models at application startup
word2vec_model, svm_model = load_models()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    API endpoint to analyze reviews from any e-commerce product URL or direct raw review text.
    - Scrapes reviews using scrape_reviews() if URL is provided.
    - Direct classification if raw review text is supplied.
    - Preprocesses reviews using preprocess_text().
    - Classifies reviews using the trained SVM model.
    - Returns structured analysis results as JSON.
    """
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

        detailed_predictions = classify_reviews(preprocessed_reviews, word2vec_model, svm_model)

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

    reviews, is_demo, platform_name, notice_message = scrape_reviews(url)
    if reviews.empty:
        return jsonify({"error": "No reviews found and unable to load fallback dataset"}), 404

    if "Review Text" not in reviews.columns or "Rating" not in reviews.columns:
        return jsonify({"error": "Invalid reviews format"}), 400

    preprocessed_reviews = []
    for i, review_text_raw in enumerate(reviews["Review Text"]):
        review_text_processed = preprocess_text(review_text_raw)

        try:
            rating = float(reviews.iloc[i]["Rating"])
        except ValueError:
            rating = 3.0

        preprocessed_reviews.append({
            "Review Text": review_text_processed,
            "Rating": rating,
            "Original Review Text": review_text_raw
        })

    detailed_predictions = classify_reviews(preprocessed_reviews, word2vec_model, svm_model)

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
