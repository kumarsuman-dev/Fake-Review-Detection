/**
 * Submits analysis request to Flask backend for reviews classification.
 */
function analyzeReviews() {
    const urlInput = document.getElementById("url");
    const url = urlInput.value.trim();
    const dashboardDiv = document.getElementById("dashboard-container");
    const errorDiv = document.getElementById("error-container");
    const loadingDiv = document.getElementById("loading");
    const btnAnalyze = document.getElementById("btn-analyze");

    // Input Validation
    if (!url) {
        showError("Please enter a valid Amazon product URL or click a demo product below.");
        return;
    }

    // Reset UI States
    dashboardDiv.classList.add("hidden");
    errorDiv.classList.add("hidden");
    loadingDiv.classList.remove("hidden");
    btnAnalyze.disabled = true;
    btnAnalyze.classList.add("opacity-70", "cursor-wait");

    fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Server error occurred"); });
        }
        return response.json();
    })
    .then(data => {
        loadingDiv.classList.add("hidden");
        btnAnalyze.disabled = false;
        btnAnalyze.classList.remove("opacity-70", "cursor-wait");

        const reviews = data.reviews || [];
        const isDemo = data.is_demo || false;

        if (reviews.length === 0) {
            showError("No reviews could be scraped or generated for this URL.");
            return;
        }

        renderDashboard(reviews, isDemo);
    })
    .catch(error => {
        loadingDiv.classList.add("hidden");
        btnAnalyze.disabled = false;
        btnAnalyze.classList.remove("opacity-70", "cursor-wait");
        showError(error.message || "An unexpected error occurred. Please verify your connection.");
        console.error("Analysis error:", error);
    });
}

/**
 * Display errors in the error container
 */
function showError(message) {
    const errorDiv = document.getElementById("error-container");
    const errorText = document.getElementById("error-text");
    errorText.textContent = message;
    errorDiv.classList.remove("hidden");
    errorDiv.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Reset all UI components and input fields
 */
function clearResults() {
    document.getElementById("url").value = "";
    document.getElementById("dashboard-container").classList.add("hidden");
    document.getElementById("error-container").classList.add("hidden");
    document.getElementById("loading").classList.add("hidden");
}

/**
 * Sets a template product URL and triggers analysis.
 */
function loadDemoProduct(productType) {
    const urlInput = document.getElementById("url");
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

    urlInput.value = url;
    analyzeReviews();
}

/**
 * Renders statistical dashboard and populates review cards list.
 */
function renderDashboard(reviews, isDemo) {
    const dashboardDiv = document.getElementById("dashboard-container");
    const demoBanner = document.getElementById("demo-banner");
    const resultDiv = document.getElementById("result");

    // Toggle demo warning banner
    if (isDemo) {
        demoBanner.classList.remove("hidden");
    } else {
        demoBanner.classList.add("hidden");
    }

    // Compute stats
    const totalCount = reviews.length;
    let fakeCount = 0;
    reviews.forEach(r => {
        if (r.prediction_code === 1) fakeCount++;
    });
    const realCount = totalCount - fakeCount;
    
    // Trust Score: percentage of real reviews
    const trustScore = totalCount > 0 ? Math.round((realCount / totalCount) * 100) : 0;

    // Update Text Fields
    document.getElementById("stat-real-count").textContent = realCount;
    document.getElementById("stat-fake-count").textContent = fakeCount;
    document.getElementById("stat-total-reviews").textContent = `Showing ${totalCount} reviews`;
    document.getElementById("stat-trust-score").textContent = `${trustScore}%`;
    document.getElementById("stat-trust-gauge-text").textContent = `${trustScore}%`;

    // Set descriptive text depending on Trust Score
    const descEl = document.getElementById("stat-trust-desc");
    if (trustScore >= 80) {
        descEl.textContent = "High Trust. Reviews appear highly organic and authentic.";
        descEl.className = "text-xs text-emerald-400 mt-2";
    } else if (trustScore >= 50) {
        descEl.textContent = "Moderate Trust. Some reviews contain spam patterns.";
        descEl.className = "text-xs text-amber-400 mt-2";
    } else {
        descEl.textContent = "Low Trust. Significant fake/AI activity detected.";
        descEl.className = "text-xs text-rose-400 mt-2";
    }

    // Animate Progress Bars
    const realPercent = totalCount > 0 ? (realCount / totalCount) * 100 : 0;
    const fakePercent = totalCount > 0 ? (fakeCount / totalCount) * 100 : 0;
    document.getElementById("bar-real-percent").style.width = `${realPercent}%`;
    document.getElementById("bar-fake-percent").style.width = `${fakePercent}%`;

    // Animate SVG Trust Circle Gauge
    // Circumference = 2 * PI * r = 2 * PI * 40 = 251.2
    const circle = document.getElementById("trust-gauge-circle");
    const offset = 251.2 - (251.2 * trustScore / 100);
    circle.style.strokeDashoffset = offset;

    // Render Review Cards
    resultDiv.innerHTML = "";
    reviews.forEach((review, index) => {
        const isFake = review.prediction_code === 1;
        const badgeClass = isFake ? "badge-fake" : "badge-real";
        const badgeIcon = isFake ? "fa-solid fa-triangle-exclamation" : "fa-solid fa-check-double";
        const borderClass = isFake ? "border-rose-500/10 hover:border-rose-500/30" : "border-emerald-500/10 hover:border-emerald-500/30";
        
        // Generate Star icons
        let starsHtml = "";
        const ratingVal = parseFloat(review.Rating) || 3.0;
        for (let i = 1; i <= 5; i++) {
            if (i <= Math.floor(ratingVal)) {
                starsHtml += '<i class="fa-solid fa-star text-amber-400 mr-0.5 text-sm"></i>';
            } else if (i - 0.5 <= ratingVal) {
                starsHtml += '<i class="fa-solid fa-star-half-stroke text-amber-400 mr-0.5 text-sm"></i>';
            } else {
                starsHtml += '<i class="fa-regular fa-star text-slate-600 mr-0.5 text-sm"></i>';
            }
        }

        // Add review card HTML
        const cardHtml = `
            <div class="glass-panel p-5 rounded-xl border ${borderClass} transition-all duration-300 review-card-anim shadow-lg" style="animation-delay: ${index * 100}ms;" id="review-card-${index}">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
                    <div class="flex items-center gap-3">
                        <div class="flex">${starsHtml}</div>
                        <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full ${badgeClass} flex items-center gap-1">
                            <i class="${badgeIcon}"></i> ${review.Prediction}
                        </span>
                    </div>
                    <button onclick="toggleAccordion(${index})" class="accordion-btn text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1.5 focus:outline-none">
                        <span>Linguistic Details</span> <i class="fa-solid fa-chevron-down"></i>
                    </button>
                </div>
                
                <p class="text-slate-300 leading-relaxed text-sm md:text-base font-light italic mb-3">
                    "${review.Review}"
                </p>

                <!-- Expandable Accordion Audit -->
                <div class="accordion-content">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 mt-3 bg-slate-950/45 rounded-lg border border-white/5 text-xs">
                        <div>
                            <div class="text-slate-500 font-medium mb-0.5">Model Confidence</div>
                            <div class="text-slate-200 font-bold text-sm flex items-center gap-1">
                                <span class="${isFake ? 'text-rose-400' : 'text-emerald-400'}">${review.confidence}%</span>
                            </div>
                        </div>
                        <div>
                            <div class="text-slate-500 font-medium mb-0.5">Word Count</div>
                            <div class="text-slate-200 font-bold text-sm">${review.word_count} words</div>
                        </div>
                        <div>
                            <div class="text-slate-500 font-medium mb-0.5">Capitalization Ratio</div>
                            <div class="text-slate-200 font-bold text-sm">${review.uppercase_ratio}%</div>
                        </div>
                        <div>
                            <div class="text-slate-500 font-medium mb-0.5">Avg Word Length</div>
                            <div class="text-slate-200 font-bold text-sm">${review.avg_word_len} chars</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        resultDiv.innerHTML += cardHtml;
    });

    // Show Dashboard
    dashboardDiv.classList.remove("hidden");
    dashboardDiv.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Expand/Collapse Accordion Details for specific card
 */
function toggleAccordion(index) {
    const card = document.getElementById(`review-card-${index}`);
    if (card) {
        card.classList.toggle("accordion-active");
    }
}
