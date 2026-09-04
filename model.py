import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))

class FastModelWrapper:
    """Lightweight pure-numpy model container for instant serverless inference."""
    def __init__(self, coef, intercept, words, vectors):
        self.coef = coef
        self.intercept = intercept
        self.words = list(words)
        self.word_map = {w: i for i, w in enumerate(self.words)}
        self.vectors = vectors
        self.dim = self.vectors.shape[1]

    def get_text_vector(self, text):
        tokens = text.split()
        indices = [self.word_map[t] for t in tokens if t in self.word_map]
        if indices:
            return np.mean(self.vectors[indices], axis=0)
        return np.zeros(self.dim, dtype=np.float32)

def load_models():
    """
    Loads compressed numpy model weights (fast, <15MB RAM, zero scikit-learn dependency).
    Falls back to legacy .pkl/.model files if npz files are not found.
    """
    search_dirs = [
        base_dir,
        os.getcwd(),
        os.path.abspath(os.path.join(base_dir, "..")),
        "/var/task"
    ]

    svm_npz = None
    w2v_npz = None

    for d in search_dirs:
        cand_svm = os.path.join(d, "svm_weights.npz")
        cand_w2v = os.path.join(d, "w2v_weights.npz")
        if not svm_npz and os.path.exists(cand_svm):
            svm_npz = cand_svm
        if not w2v_npz and os.path.exists(cand_w2v):
            w2v_npz = cand_w2v

    if svm_npz and w2v_npz:
        svm_data = np.load(svm_npz, allow_pickle=True)
        w2v_data = np.load(w2v_npz, allow_pickle=True)
        model = FastModelWrapper(
            coef=svm_data["coef"],
            intercept=svm_data["intercept"],
            words=w2v_data["words"],
            vectors=w2v_data["vectors"]
        )
        return model, model

    # Fallback to legacy loader
    from gensim.models import Word2Vec
    import joblib
    w2v_path = os.path.join(base_dir, "word2vec_model.model")
    svm_path = os.path.join(base_dir, "SVM_model.pkl")
    word2vec_model = Word2Vec.load(w2v_path)
    svm_model = joblib.load(svm_path)
    return word2vec_model, svm_model

def classify_reviews(reviews, word2vec_model, svm_model):
    """
    Classifies reviews based on text features, rating, and length.
    Supports both FastModelWrapper and legacy models.
    """
    from preprocessing import preprocess_text
    results = []

    is_fast_model = isinstance(word2vec_model, FastModelWrapper)

    for review in reviews:
        raw_text = review.get("Original Review Text", review.get("Review Text", ""))
        preprocessed_review = preprocess_text(review.get("Review Text", raw_text))
        words = preprocessed_review.split()

        try:
            rating = float(review.get("Rating", 5.0))
        except (ValueError, TypeError):
            rating = 5.0

        review_length = len(words)

        # Raw text stats
        char_count = len(raw_text)
        uppercase_ratio = (sum(1 for c in raw_text if c.isupper()) / max(char_count, 1)) * 100
        word_count = len(raw_text.split())
        avg_word_len = np.mean([len(w) for w in raw_text.split()]) if word_count > 0 else 0.0

        if is_fast_model:
            text_vec = word2vec_model.get_text_vector(preprocessed_review)
            features = np.hstack([[rating], [review_length], text_vec]).reshape(1, -1)
            decision_val = float(np.dot(features, word2vec_model.coef.T)[0, 0] + word2vec_model.intercept[0])
            prob = 1.0 / (1.0 + np.exp(-decision_val))
            prediction = 1 if decision_val > 0 else 0
            confidence = prob * 100 if prediction == 1 else (1.0 - prob) * 100
        else:
            vectors = np.array([word2vec_model.wv[w] for w in words if w in word2vec_model.wv])
            if vectors.size > 0:
                text_vec = np.mean(vectors, axis=0).reshape(1, -1)
                features = np.hstack([[[rating]], [[review_length]], text_vec])
                prediction = int(svm_model.predict(features)[0])
                decision_val = float(svm_model.decision_function(features)[0])
                prob = 1.0 / (1.0 + np.exp(-decision_val))
                confidence = prob * 100 if prediction == 1 else (1.0 - prob) * 100
            else:
                prediction = 0
                confidence = 50.0

        results.append({
            "prediction": int(prediction),
            "confidence": round(float(confidence), 1),
            "word_count": word_count,
            "uppercase_ratio": round(float(uppercase_ratio), 1),
            "avg_word_len": round(float(avg_word_len), 1)
        })

    return results