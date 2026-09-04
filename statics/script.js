/**
 * SENTINEL Review Audit & Synthetic Detection Engine
 * Client Application Logic (Top 1% UI/UX Architecture)
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
        urlBtn.className = "px-3 py-1.5 rounded-lg bg-surface-100 border border-border-active text-xs font-medium text-white flex items-center gap-1.5 transition-all";
        textBtn.className = "px-3 py-1.5 rounded-lg bg-surface-200 border border-border-subtle text-xs font-medium text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-all";
        urlContainer.classList.remove("hidden");
        textContainer.classList.add("hidden");
    } else {
        textBtn.className = "px-3 py-1.5 rounded-lg bg-surface-100 border border-border-active text-xs font-medium text-white flex items-center gap-1.5 transition-all";
        urlBtn.className = "px-3 py-1.5 rounded-lg bg-surface-200 border border-border-subtle text-xs font-medium text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-all";
        textContainer.classList.remove("hidden");
        urlContainer.classList.add("hidden");
        document.getElementById("raw-review-text").focus();
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
        icon.className = "fa-brands fa-amazon text-base text-amber-400";
    } else if (lower.includes("walmart.")) {
        icon.className = "fa-solid fa-asterisk text-base text-blue-400";
    } else if (lower.includes("flipkart.")) {
        icon.className = "fa-solid fa-cart-shopping text-base text-yellow-400";
    } else if (lower.includes("shopify.") || lower.includes("myshopify.")) {
        icon.className = "fa-brands fa-shopify text-base text-emerald-400";
    } else if (lower.includes("ebay.")) {
        icon.className = "fa-brands fa-ebay text-base text-rose-400";
    } else if (lower.includes("bestbuy.")) {
        icon.className = "fa-solid fa-tag text-base text-yellow-300";
    } else if (lower.includes("target.")) {
        icon.className = "fa-solid fa-bullseye text-base text-red-400";
    } else if (lower.startsWith("http://") || lower.startsWith("https://")) {
        icon.className = "fa-solid fa-link text-base text-indigo-400";
    } else {
        icon.className = "fa-solid fa-globe text-base text-slate-500";
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
        showError("Please enter a product URL (Amazon, Flipkart, Walmart, etc.) or choose a benchmark.");
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
            showError("No reviews could be parsed or generated for this URL.");
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
            if (demoBannerText) demoBannerText.textContent = message || `${platform} returned 0 written customer reviews or restricted direct connection. Loaded benchmark dataset.`;
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
        sampleEl.innerHTML = `${totalCount} items <span class="text-[10px] text-slate-400 font-normal">(${isDemo ? 'Benchmark' : 'Live ' + platform})</span>`;
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
        riskBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        trustDesc.textContent = "High organic density. Genuine human consumer language patterns dominant.";
    } else if (trustScore >= 50) {
        riskBadge.textContent = "MODERATE RISK";
        riskBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20";
        trustDesc.textContent = "Elevated synthetic signature detected across multiple reviews.";
    } else {
        riskBadge.textContent = "HIGH RISK";
        riskBadge.className = "text-[10px] font-mono px-2 py-0.5 rounded font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20";
        trustDesc.textContent = "Heavy bot / computer-generated footprint flagged.";
    }

    // Unhide dashboard & scroll
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
                starsHtml += '<i class="fa-solid fa-star text-amber-400 text-[11px] mr-0.5"></i>';
            } else if (i - 0.5 <= ratingVal) {
                starsHtml += '<i class="fa-solid fa-star-half-stroke text-amber-400 text-[11px] mr-0.5"></i>';
            } else {
                starsHtml += '<i class="fa-regular fa-star text-slate-600 text-[11px] mr-0.5"></i>';
            }
        }

        const cardHtml = `
            <div class="review-card ${cardClass}" id="review-card-${index}">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                    <div class="flex items-center gap-3">
                        <div class="flex items-center">${starsHtml} <span class="text-xs font-mono text-slate-400 ml-1.5">${ratingVal.toFixed(1)}</span></div>
                        <span class="px-2 py-0.5 rounded ${badgeClass}">
                            ${badgeLabel}
                        </span>
                    </div>
                    <button onclick="toggleAccordion(${index})" class="accordion-btn text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 py-0.5">
                        <span>Telemetry</span>
                        <i class="fa-solid fa-chevron-down text-[10px]"></i>
                    </button>
                </div>

                <p class="text-slate-300 text-xs sm:text-sm leading-relaxed font-normal">
                    "${escapeHtml(review.Review)}"
                </p>

                <!-- Expandable Technical Audit Panel -->
                <div class="accordion-content">
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 mt-3 border-t border-border-subtle font-mono text-[11px]">
                        <div class="p-2 rounded bg-surface-300/80 border border-border-subtle">
                            <div class="text-slate-500">Confidence</div>
                            <div class="font-bold ${isFake ? 'text-rose-400' : 'text-emerald-400'} mt-0.5">${review.confidence || 50}%</div>
                        </div>
                        <div class="p-2 rounded bg-surface-300/80 border border-border-subtle">
                            <div class="text-slate-500">Token Count</div>
                            <div class="text-slate-200 font-semibold mt-0.5">${review.word_count} words</div>
                        </div>
                        <div class="p-2 rounded bg-surface-300/80 border border-border-subtle">
                            <div class="text-slate-500">Caps Ratio</div>
                            <div class="text-slate-200 font-semibold mt-0.5">${review.uppercase_ratio}%</div>
                        </div>
                        <div class="p-2 rounded bg-surface-300/80 border border-border-subtle">
                            <div class="text-slate-500">Avg Word Length</div>
                            <div class="text-slate-200 font-semibold mt-0.5">${review.avg_word_len} chars</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        resultDiv.innerHTML += cardHtml;
    });
}

/**
 * Helper to escape HTML tags to prevent XSS
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

/**
 * Toggle accordion details for a single card
 */
function toggleAccordion(index) {
    const card = document.getElementById(`review-card-${index}`);
    if (card) {
        card.classList.toggle("accordion-active");
    }
}

/**
 * Displays error modal/message
 */
function showError(message) {
    const errorDiv = document.getElementById("error-container");
    const errorText = document.getElementById("error-text");
    if (errorText) errorText.textContent = message;
    if (errorDiv) {
        errorDiv.classList.remove("hidden");
        errorDiv.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Quick Benchmark Preset loader
 */
function loadDemoProduct(productType) {
    const urlInput = document.getElementById("url");
    const clearBtn = document.getElementById("btn-clear-input");
    let url = "";

    switch(productType) {
        case 'headphones':
            url = "https://www.amazon.com/Sony-WH-1000XM4-Wireless-Canceling-Headphones/dp/B08C56GNE8";
            break;
        case 'kindle':
            url = "https://www.amazon.com/Kindle-Paperwhite-Signature-Edition-Ad-Supported/dp/B08N36XNTT";
            break;
        case 'chair':
            url = "https://www.amazon.com/Ergonomic-Office-Chair-Adjustable-Lumbar/dp/B08Q3V1V4K";
            break;
        default:
            url = "https://www.amazon.com/dp/B0SAMPLE123";
            break;
    }

    if (urlInput) {
        urlInput.value = url;
        if (clearBtn) clearBtn.classList.remove("hidden");
    }
    analyzeReviews();
}

/**
 * Export JSON payload to clipboard
 */
function exportJSON() {
    if (!allReviewsData || allReviewsData.length === 0) return;
    const jsonStr = JSON.stringify(allReviewsData, null, 2);
    navigator.clipboard.writeText(jsonStr).then(() => {
        alert("Telemetry JSON copied to clipboard.");
    }).catch(() => {
        alert("Clipboard copy failed.");
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
    link.setAttribute("download", `sentinel_review_audit_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
