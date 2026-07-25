# 🕵️‍♂️ Fake Review Detection Web App

Detect fraudulent Amazon product reviews and shop smarter!  
Empowered by AI, NLP, and machine learning, this web app classifies reviews as **Real** or **Fake** and generates AI-powered summaries to help you make informed decisions.

![Fake Review Detection Banner](https://img.shields.io/badge/AI-Powered-blueviolet?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&style=flat-square)
![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey?logo=flask&style=flat-square)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-ML-orange?logo=scikit-learn&style=flat-square)
![Gensim](https://img.shields.io/badge/Gensim-NLP-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

<br>

---

## 🚀 Features

- 🔎 **Detect Fake Reviews** — Classifies Amazon reviews as **Real (Original)** or **Fake (Computer Generated)**
- 🤖 **AI-Powered Summaries** — Generates concise summaries using **Gemini API**
- 🌐 **Web Scraping** — Fetches reviews directly from Amazon product pages
- 📊 **Confidence Score** — Shows prediction confidence, word count, and text analysis metrics
- 💡 **User-Friendly Interface** — Modern, responsive design with Tailwind CSS
- 🔒 **Enhances Shopping Trust** — Makes online shopping safer and smarter

---

## 🛠️ Built With

| Technology | Purpose |
|---|---|
| **Python 3.x** | Core programming language |
| **Flask** | Web framework / Backend server |
| **Scikit-learn (SVM)** | Review classification model |
| **Gensim (Word2Vec)** | Text embedding / NLP |
| **NLTK** | Natural language preprocessing |
| **Gemini API** | AI-powered review summarization |
| **HTML / JavaScript** | Frontend interface |
| **Tailwind CSS** | UI styling |

---

## 📸 Screenshots

>
![alt text](image.png)
![alt text](image-1.png)
---

## 🚚 Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Installation

```bash
git clone https://github.com/kumarsuman-dev/Fake-Review-Detection.git
cd Fake-Review-Detection
```

### Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

# Upgrade pip
python3 -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Run the App

```bash
python3 app.py
```

Open your browser and go to 👉 `http://localhost:5001`

### Stop the Server

```
Press Ctrl + C
```

Then deactivate the virtual environment:

```bash
deactivate
```

---

## 🎯 Usage

1. Open the app at `http://localhost:5001`
2. Enter or paste an **Amazon product URL**
3. The app **scrapes and analyzes** the reviews automatically
4. Results display which reviews are **Real ✅** or **Fake ❌**
5. Each result includes:
   - Prediction label
   - Confidence score
   - Word count & text statistics
6. Get **AI-powered summaries** for quick insights

---

## 🧠 How It Works

```
Amazon URL
    ↓
Web Scraper (scraper.py)
    ↓
Text Preprocessing (preprocessing.py)
    ↓
Word2Vec Embeddings + Feature Extraction
    ↓
SVM Classifier (SVM_model.pkl)
    ↓
Real / Fake Prediction + Confidence Score
    ↓
Gemini API → AI Summary
    ↓
Results displayed on Web UI
```

---

## 🙏 Acknowledgements

- [Scikit-learn](https://scikit-learn.org/) — Machine learning library
- [Gensim](https://radimrehurek.com/gensim/) — Word2Vec NLP model
- [Flask](https://flask.palletsprojects.com/) — Lightweight web framework
- [NLTK](https://www.nltk.org/) — Natural language processing toolkit
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS framework
- [Gemini API](https://ai.google.dev/gemini-api/docs) — Google AI summarization
- Inspired by the need for **trustworthy online shopping**!

---

## 👨‍💻 Developer

**Suman Kumar**
- GitHub: [@kumarsuman-dev](https://github.com/kumarsuman-dev)

---

> _Enhance your shopping trust. Detect fake reviews with AI power!_ 🛡️
