# Fake Review Detection — E-Commerce Review Integrity & Synthetic Manipulation Detection Engine

> End-to-end Machine Learning & NLP system that audits live e-commerce reviews (Amazon, Flipkart, Walmart) in real time, generates 100-dimensional semantic embeddings, and detects computer-generated/synthetic review manipulation using Linear SVM.

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python&style=flat-square)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-lightgrey?logo=flask&style=flat-square)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-SVM-orange?logo=scikit-learn&style=flat-square)](https://scikit-learn.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Fast%20Inference-013243?logo=numpy&style=flat-square)](https://numpy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## Overview

**Fake Review Detection** is an engineering-first review verification platform designed to combat the rising proliferation of AI-generated and fraudulent consumer reviews. 

Instead of relying solely on keyword matching or static heuristics, it combines **live web scraping** with **100-dimensional semantic Word2Vec vector embeddings** and a **Linear Support Vector Machine (SVM)** classifier trained on 72,000+ labeled organic and synthetic reviews.

---

## Core Features

- **Live Multi-Platform Scraping:**
  - **Amazon Engine:** Direct ASIN extraction, request header impersonation, and review page traversal.
  - **Flipkart Engine:** Live `window.__INITIAL_STATE__` JSON hydration parsing with multi-page pagination, extracting verified customer reviews per run.
  - **Direct Text Auditor:** Evaluate offline or unformatted review texts directly with custom star ratings.

- **Machine Learning & NLP Pipeline:**
  - Full NLP text normalization, tokenization, stopword filtering, and punctuation removal.
  - 100-dimensional continuous dense vector generation via custom **Word2Vec** embeddings.
  - Feature concatenation with normalized review length and star ratings (102-dimensional feature space).
  - High-confidence binary classification: **Organic (OR)** vs. **Synthetic / Computer-Generated (CG)**.

- **Clean SaaS Dashboard:**
  - Modern, human-designed light interface with clear metric readouts and responsive typography.
  - Real-time **Trust Index (%)** calculation with Risk Level categorizations (Low, Moderate, High Risk).
  - Real-time client-side keyword search & Organic vs. Synthetic tab filtering.
  - One-click export to **JSON telemetry** and **CSV datasets**.
  - Expandable per-review diagnostic panels displaying confidence scores, token counts, uppercase ratios, and average word lengths.

---

## Architecture & Pipeline Flow

```
Product URL (Amazon / Flipkart / Walmart)  OR  Direct Review Text
                        |
                        v
         Universal Live Scraper (scraper.py)
    (Browser Impersonation + JSON State Parsing)
                        |
                        v
          NLP Preprocessing (preprocessing.py)
        (Lowercasing, Regex Cleaning, Stopword Removal)
                        |
                        v
          Word2Vec 100D Vectorization (model.py)
          + Metadata Features (Length & Rating)
                        |
                        v
            Linear SVM Classification Core
                        |
                        v
         Real-Time Telemetry & Trust Analytics UI
           (Trust Index, Risk Badges, JSON/CSV Export)
```

---

## Tech Stack

| Component | Technologies |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Backend & API** | Flask, Werkzeug |
| **Machine Learning** | Fast NumPy inference, Scikit-Learn (Linear SVM), Joblib |
| **Natural Language Processing** | Word2Vec, NLTK Porter Stemmer, Emoji handling |
| **Scraping & Networking** | Requests, BeautifulSoup4 |
| **Frontend & UI/UX** | HTML5, Tailwind CSS, JavaScript (ES6+), FontAwesome, Plus Jakarta Sans |

---

## Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/kumarsuman-dev/Fake-Review-Detection.git
cd Fake-Review-Detection
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
**`http://localhost:5001`**

---

## Usage Modes

### Mode 1: Product URL Scanner
1. Paste any Amazon or Flipkart product link into the console.
2. Click **Audit Reviews** (or hit `Enter`).
3. The platform extracts live customer reviews, passes them through the inference pipeline, and visualizes the aggregate Trust Index.

### Mode 2: Direct Review Text Auditor
1. Switch to **Direct Review Text** mode.
2. Paste any single or multi-line product review.
3. Select the associated star rating and click **Classify Review Text** for instant anomaly telemetry.

---

## Author

**Suman Kumar**  
- GitHub: [@kumarsuman-dev](https://github.com/kumarsuman-dev)  
- Repository: [https://github.com/kumarsuman-dev/Fake-Review-Detection](https://github.com/kumarsuman-dev/Fake-Review-Detection)

---

## License
This project is open source and available under the [MIT License](LICENSE).
