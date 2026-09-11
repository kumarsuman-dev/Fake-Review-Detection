/**
 * Fake Review Detection — Client Application Logic
 * Modern, Human-Crafted SaaS Web Interface
 * GitHub: https://github.com/kumarsuman-dev/Fake-Review-Detection
 * Author: kumarsuman-dev
 */

// Global State
let allReviewsData = [];
let currentFilter = 'all'; // 'all' | 'real' | 'fake'
let currentSearchQuery = '';
let currentMode = 'url'; // 'url' | 'text'

document.addEventListener("DOMContentLoaded", () => {
    const urlInput = document.getElementById("url");
    const clearBtn = document.getElementById("btn-clear-input");

    if (urlInput) {
        urlInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                analyzeReviews();
            }
        });

        urlInput.addEventListener("input", () => {
            if (clearBtn) {
                if (urlInput.value.trim().length > 0) {
                    clearBtn.classList.remove("hidden");
                } else {
                    clearBtn.classList.add("hidden");
                }
            }
            detectPlatform(urlInput.value);
        });
    }
});

/**
 * Switch between URL scanner and Direct Text auditor
 */
function switchMode(mode) {
    currentMode = mode;
    const urlBtn = document.getElementById("mode-url-btn");
    const textBtn = document.getElementById("mode-text-btn");
    const urlContainer = document.getElementById("container-url-mode");
    const textContainer = document.getElementById("container-text-mode");

    if (mode === 'url') {
        urlBtn.className = "px-3 py-1.5 rounded-md mode-btn-active transition-all";
        textBtn.className = "px-3 py-1.5 rounded-md mode-btn-inactive transition-all";
        urlContainer.classList.remove("hidden");
        textContainer.classList.add("hidden");
    } else {
        textBtn.className = "px-3 py-1.5 rounded-md mode-btn-active transition-all";
        urlBtn.className = "px-3 py-1.5 rounded-md mode-btn-inactive transition-all";
        textContainer.classList.remove("hidden");
        urlContainer.classList.add("hidden");
        const rawText = document.getElementById("raw-review-text");
        if (rawText) rawText.focus();
    }
}

/**
 * Dynamically detects e-commerce platform from URL and updates icon
 */
function detectPlatform(url) {
    const icon = document.getElementById("platform-icon");
    if (!icon) return;

    const lower = url.toLowerCase();
    if (lower.includes("amazon.") || lower.includes("amzn.")) {
        icon.className = "fa-brands fa-amazon text-sm text-ink";
    } else if (lower.includes("walmart.")) {
        icon.className = "fa-solid fa-asterisk text-sm text-ink";
    } else if (lower.includes("flipkart.")) {
        icon.className = "fa-solid fa-cart-shopping text-sm text-ink";
    } else if (lower.includes("shopify.") || lower.includes("myshopify.")) {
        icon.className = "fa-brands fa-shopify text-sm text-ink";
    } else if (lower.includes("ebay.")) {
        icon.className = "fa-brands fa-ebay text-sm text-ink";
    } else if (lower.includes("bestbuy.")) {
        icon.className = "fa-solid fa-tag text-sm text-ink";
    } else if (lower.includes("target.")) {
        icon.className = "fa-solid fa-bullseye text-sm text-ink";
    } else if (lower.startsWith("http://") || lower.startsWith("https://")) {
        icon.className = "fa-solid fa-link text-sm text-accent";
    } else {
        icon.className = "fa-solid fa-globe text-sm text-muted";
    }
}

/**
 * Clears the main input field
 */
function clearInput() {
    const urlInput = document.getElementById("url");
    const clearBtn = document.getElementById("btn-clear-input");
    if (urlInput) {
        urlInput.value = "";
        urlInput.focus();
    }
    if (clearBtn) {
        clearBtn.classList.add("hidden");
    }
    detectPlatform("");
}

/**
 * Displays user error modal/notification
 */
function showError(msg) {
    const errorDiv = document.getElementById("error-container");
    const errorText = document.getElementById("error-text");
    if (errorDiv && errorText) {
        errorText.textContent = msg;
        errorDiv.classList.remove("hidden");
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Classifies raw review text directly (any platform / offline text)
 */
function analyzeDirectText() {
    const textArea = document.getElementById("raw-review-text");
    const ratingSelect = document.getElementById("raw-rating");
    const text = textArea ? textArea.value.trim() : "";
    const rating = ratingSelect ? parseFloat(ratingSelect.value) : 5.0;

    if (!text) {
        showError("Please enter review text to evaluate.");
        return;
    }

    const dashboardDiv = document.getElementById("dashboard-container");
    const errorDiv = document.getElementById("error-container");
    const loadingDiv = document.getElementById("loading");
    const btnAnalyzeText = document.getElementById("btn-analyze-text");

    dashboardDiv.classList.add("hidden");
    errorDiv.classList.add("hidden");
    loadingDiv.classList.remove("hidden");
    if (btnAnalyzeText) {
        btnAnalyzeText.disabled = true;
        btnAnalyzeText.classList.add("opacity-50", "cursor-wait");
    }

    fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, rating: rating })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Inference error."); });
        }
        return response.json();
    })
    .then(data => {
        loadingDiv.classList.add("hidden");
        if (btnAnalyzeText) {
            btnAnalyzeText.disabled = false;
            btnAnalyzeText.classList.remove("opacity-50", "cursor-wait");
        }

        const reviews = data.reviews || [];
        if (reviews.length === 0) {
            showError("No review results returned.");
            return;
        }

        allReviewsData = reviews;
        currentFilter = 'all';
        currentSearchQuery = '';
        renderDashboardOverview(reviews, false, data.platform || "Direct Text", "Direct raw review text classified successfully.");
        applyFiltersAndRender();
    })
    .catch(error => {
        loadingDiv.classList.add("hidden");
        if (btnAnalyzeText) {
            btnAnalyzeText.disabled = false;
            btnAnalyzeText.classList.remove("opacity-50", "cursor-wait");
        }
        showError(error.message || "Classification failed.");
    });
}

/**
 * Triggers review analysis via Flask REST API
 */
function analyzeReviews() {
    const urlInput = document.getElementById("url");
    const url = urlInput ? urlInput.value.trim() : "";
    const dashboardDiv = document.getElementById("dashboard-container");
    const errorDiv = document.getElementById("error-container");
    const loadingDiv = document.getElementById("loading");
    const btnAnalyze = document.getElementById("btn-analyze");

    // Input Validation
    if (!url) {
        showError("Please enter a product URL (Amazon, Flipkart, Walmart, etc.) or choose a benchmark sample.");
        return;
    }

    // Reset UI State
    dashboardDiv.classList.add("hidden");
    errorDiv.classList.add("hidden");
    loadingDiv.classList.remove("hidden");
    if (btnAnalyze) {
        btnAnalyze.disabled = true;
        btnAnalyze.classList.add("opacity-50", "cursor-wait");
    }

    fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Server processing failed."); });
        }
        return response.json();
    })
    .then(data => {
        loadingDiv.classList.add("hidden");
        if (btnAnalyze) {
            btnAnalyze.disabled = false;
            btnAnalyze.classList.remove("opacity-50", "cursor-wait");
        }

        const reviews = data.reviews || [];
        const isDemo = data.is_demo || false;
        const platform = data.platform || "E-Commerce";
        const message = data.message || "";

        if (reviews.length === 0) {
            showError("No reviews could be parsed or retrieved for this URL.");
            return;
        }

        allReviewsData = reviews;
        currentFilter = 'all';
        currentSearchQuery = '';
        
        const filterInput = document.getElementById("filter-search");
        if (filterInput) filterInput.value = '';

        renderDashboardOverview(reviews, isDemo, platform, message);
        applyFiltersAndRender();
    })
    .catch(error => {
        loadingDiv.classList.add("hidden");
        if (btnAnalyze) {
            btnAnalyze.disabled = false;
            btnAnalyze.classList.remove("opacity-50", "cursor-wait");
        }
        showError(error.message || "Network or inference pipeline exception occurred.");
        console.error("Pipeline failure:", error);
    });
}

/**
 * Renders high-level summary cards, Trust Index, and telemetry
 */
function renderDashboardOverview(reviews, isDemo, platform = "E-Commerce", message = "") {
    const dashboardDiv = document.getElementById("dashboard-container");
    const demoBanner = document.getElementById("demo-banner");
    const demoBannerTitle = document.getElementById("demo-banner-title");
    const demoBannerText = document.getElementById("demo-banner-text");

    // Dynamic Platform & Fallback Banner
    if (demoBanner) {
        if (isDemo) {
            demoBanner.classList.remove("hidden");
            if (demoBannerTitle) demoBannerTitle.textContent = `${platform} Notice:`;
            if (demoBannerText) demoBannerText.textContent = message || `${platform} anti-bot restrictions limited direct headless access. Loaded verified benchmark dataset.`;
        } else {
            demoBanner.classList.add("hidden");
        }
    }

    const totalCount = reviews.length;
    let fakeCount = 0;
    let totalConfidence = 0;

    reviews.forEach(r => {
        if (r.prediction_code === 1) fakeCount++;
        totalConfidence += (r.confidence || 50);
    });

    const realCount = totalCount - fakeCount;
    const trustScore = totalCount > 0 ? Math.round((realCount / totalCount) * 100) : 0;
    const avgConfidence = totalCount > 0 ? Math.round(totalConfidence / totalCount) : 0;
    const realPercent = totalCount > 0 ? Math.round((realCount / totalCount) * 100) : 0;
    const fakePercent = totalCount > 0 ? Math.round((fakeCount / totalCount) * 100) : 0;

    // Update Counts & Badges
    document.getElementById("stat-trust-score").textContent = `${trustScore}%`;
    document.getElementById("stat-real-count").textContent = realCount;
    document.getElementById("stat-fake-count").textContent = fakeCount;
    document.getElementById("stat-real-percent-text").textContent = `${realPercent}% of total sample`;
    document.getElementById("stat-fake-percent-text").textContent = `${fakePercent}% flagged anomalous`;
    
    // Tab counters
    document.getElementById("tab-count-all").textContent = totalCount;
    document.getElementById("tab-count-real").textContent = realCount;
    document.getElementById("tab-count-fake").textContent = fakeCount;

    // Metadata
    const sampleEl = document.getElementById("meta-sample-count");
    if (sampleEl) {
        sampleEl.innerHTML = `${totalCount} reviews <span class="text-[11px] text-muted font-medium">(${isDemo ? 'Benchmark' : 'Live ' + platform})</span>`;
    }
    document.getElementById("meta-avg-conf").textContent = `${avgConfidence}%`;

    // Progress Bars
    document.getElementById("bar-real-percent").style.width = `${realPercent}%`;
    document.getElementById("bar-fake-percent").style.width = `${fakePercent}%`;

    // Risk Level Badge
    const riskBadge = document.getElementById("stat-risk-badge");
    const trustDesc = document.getElementById("stat-trust-desc");
    if (trustScore >= 80) {
        riskBadge.textContent = "LOW RISK";
        riskBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-accent-light text-accent border border-accent/15";
        trustDesc.textContent = "High organic density. Genuine human language patterns dominant.";
    } else if (trustScore >= 50) {
        riskBadge.textContent = "MODERATE RISK";
        riskBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-warn-light text-warn border border-warn/20";
        trustDesc.textContent = "Elevated synthetic patterns detected across multiple reviews.";
    } else {
        riskBadge.textContent = "HIGH RISK";
        riskBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-warn-light text-warn border border-warn/20";
        trustDesc.textContent = "Heavy computer-generated manipulation flagged.";
    }

    // Unhide dashboard & smooth scroll
    dashboardDiv.classList.remove("hidden");
    dashboardDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Filter reviews by tab (all, real, fake)
 */
function filterReviews(filterType) {
    currentFilter = filterType;

    // Update active tab buttons
    ['all', 'real', 'fake'].forEach(type => {
        const tab = document.getElementById(`tab-${type}`);
        if (tab) {
            if (type === filterType) tab.classList.add('active');
            else tab.classList.remove('active');
        }
    });

    applyFiltersAndRender();
}

/**
 * Search reviews in real-time
 */
function searchReviews(query) {
    currentSearchQuery = query.toLowerCase().trim();
    applyFiltersAndRender();
}

/**
 * Filters dataset and renders individual review cards
 */
function applyFiltersAndRender() {
    const resultDiv = document.getElementById("result");
    const emptyState = document.getElementById("filter-empty");
    if (!resultDiv) return;

    let filtered = allReviewsData.filter(item => {
        // Tab check
        if (currentFilter === 'real' && item.prediction_code !== 0) return false;
        if (currentFilter === 'fake' && item.prediction_code !== 1) return false;

        // Search check
        if (currentSearchQuery) {
            const textMatch = (item.Review || '').toLowerCase().includes(currentSearchQuery);
            return textMatch;
        }
        return true;
    });

    resultDiv.innerHTML = "";

    if (filtered.length === 0) {
        if (emptyState) emptyState.classList.remove("hidden");
        return;
    } else {
        if (emptyState) emptyState.classList.add("hidden");
    }

    filtered.forEach((review, index) => {
        const isFake = review.prediction_code === 1;
        const cardClass = isFake ? "card-fake" : "card-real";
        const badgeClass = isFake ? "badge-fake" : "badge-real";
        const badgeLabel = isFake ? "SYNTHETIC (CG)" : "ORGANIC (OR)";
        const ratingVal = parseFloat(review.Rating) || 3.0;

        // Star rating glyphs
        let starsHtml = "";
        for (let i = 1; i <= 5; i++) {
            if (i <= Math.floor(ratingVal)) {
                starsHtml += '<i class="fa-solid fa-star text-ink text-xs mr-0.5"></i>';
            } else if (i - 0.5 <= ratingVal) {
                starsHtml += '<i class="fa-solid fa-star-half-stroke text-ink text-xs mr-0.5"></i>';
            } else {
                starsHtml += '<i class="fa-regular fa-star text-muted/40 text-xs mr-0.5"></i>';
            }
        }

        const cardHtml = `
            <div class="review-card ${cardClass}" id="review-card-${index}">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                    <div class="flex items-center gap-3">
                        <div class="flex items-center">${starsHtml} <span class="text-xs font-semibold text-muted ml-1.5">${ratingVal.toFixed(1)}</span></div>
                        <span class="${badgeClass}">
                            ${badgeLabel}
                        </span>
                    </div>
                    <button onclick="toggleAccordion(${index})" class="accordion-btn text-xs font-semibold text-muted hover:text-ink transition-colors flex items-center gap-1.5 py-0.5">
                        <span>Telemetry</span>
                        <i class="fa-solid fa-chevron-down text-[10px]"></i>
                    </button>
                </div>

                <p class="text-ink/90 text-xs sm:text-sm leading-relaxed font-normal">
                    "${escapeHtml(review.Review)}"
                </p>

                <!-- Expandable Technical Audit Panel -->
                <div class="accordion-content">
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 mt-3 border-t border-border font-sans text-xs">
                        <div class="p-2.5 rounded-lg bg-gray-50 border border-border">
                            <div class="text-muted text-[11px]">Model Confidence</div>
                            <div class="font-bold ${isFake ? 'text-warn' : 'text-accent'} mt-0.5">${review.confidence || 50}%</div>
                        </div>
                        <div class="p-2.5 rounded-lg bg-gray-50 border border-border">
                            <div class="text-muted text-[11px]">Token Count</div>
                            <div class="text-ink font-semibold mt-0.5">${review.word_count} words</div>
                        </div>
                        <div class="p-2.5 rounded-lg bg-gray-50 border border-border">
                            <div class="text-muted text-[11px]">Uppercase Ratio</div>
                            <div class="text-ink font-semibold mt-0.5">${review.uppercase_ratio}%</div>
                        </div>
                        <div class="p-2.5 rounded-lg bg-gray-50 border border-border">
                            <div class="text-muted text-[11px]">Avg Word Length</div>
                            <div class="text-ink font-semibold mt-0.5">${review.avg_word_len} chars</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        resultDiv.innerHTML += cardHtml;
    });
}

/**
 * Accordion toggle for review telemetry
 */
function toggleAccordion(index) {
    const card = document.getElementById(`review-card-${index}`);
    if (card) {
        card.classList.toggle("accordion-active");
    }
}

/**
 * Loads predefined demo benchmark products
 */
function loadDemoProduct(productType) {
    const urlInput = document.getElementById("url");
    const clearBtn = document.getElementById("btn-clear-input");
    let url = "";

    switch(productType) {
        case 'amazon':
        case 'headphones':
            url = "https://www.amazon.com/Sony-WH-1000XM4-Canceling-Overhead-Headphones/dp/B08445CXRL";
            break;
        case 'flipkart':
        case 'flipkart_iphone':
        case 'mobile':
            url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4";
            break;
        case 'flipkart_boat':
            url = "https://www.flipkart.com/boat-airdopes-131-bluetooth-headset/p/itmfb5e28a50c8e3";
            break;
        case 'walmart':
        case 'chair':
            url = "https://www.walmart.com/ip/PlayStation-5-Console/363472942";
            break;
        case 'amazon_in':
            url = "https://www.amazon.in/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY";
            break;
        case 'kindle':
        case 'echo':
            url = "https://www.amazon.com/Echo-Dot-5th-Gen-Charcoal/dp/B09B8V1LZ3";
            break;
        default:
            url = "https://www.amazon.com/Sony-WH-1000XM4-Canceling-Overhead-Headphones/dp/B08445CXRL";
            break;
    }

    if (urlInput) {
        urlInput.value = url;
        if (clearBtn) clearBtn.classList.remove("hidden");
        detectPlatform(url);
    }
    analyzeReviews();
}

/**
 * Export JSON payload to clipboard
 */
function exportJSON() {
    if (!allReviewsData || allReviewsData.length === 0) return;
    const jsonStr = JSON.stringify(allReviewsData, null, 2);
    const label = document.getElementById("btn-json-label");
    navigator.clipboard.writeText(jsonStr).then(() => {
        if (label) {
            const prev = label.textContent;
            label.textContent = "Copied!";
            setTimeout(() => { label.textContent = prev; }, 1500);
        }
    }).catch(() => {
        if (label) {
            label.textContent = "Error";
            setTimeout(() => { label.textContent = "JSON"; }, 1500);
        }
    });
}

/**
 * Export reviews to CSV file
 */
function exportCSV() {
    if (!allReviewsData || allReviewsData.length === 0) return;
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Rating,Prediction,Confidence,WordCount,Review\n";

    allReviewsData.forEach(r => {
        const safeReview = (r.Review || "").replace(/"/g, '""');
        const row = `"${r.Rating}","${r.Prediction}","${r.confidence}","${r.word_count}","${safeReview}"`;
        csvContent += row + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `fake_review_detection_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Basic XSS sanitization
 */
function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
