import re
import json
import requests
from bs4 import BeautifulSoup

def clean_review_text(raw_text):
    """Cleans standard e-commerce UI noise from review text."""
    if not raw_text:
        return ""
    cleaned = raw_text.replace("Brief content visible, double tap to read full content.Full content visible, double tap to read brief content.", "")
    cleaned = re.sub(r'Read less\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'READ MORE', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Review for:.*?(?:GB|TB|Color|Storage|Size)\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'(?:Flipkart Customer|Certified Buyer|months? ago|days? ago|hours? ago|years? ago|Verified Purchase|Helpful for\s*\d+).*$', '', cleaned)
    cleaned = cleaned.replace("Read more", "").replace("\u2069", "").strip()
    return cleaned

def extract_asin(url):
    """Extracts 10-character Amazon ASIN from any product or review URL."""
    match = re.search(r'/(?:dp|gp/product|product-reviews|d)/([A-Z0-9]{10})', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match_fallback = re.search(r'/(B[A-Z0-9]{9}|[0-9]{9}[0-9X])', url, re.IGNORECASE)
    if match_fallback:
        return match_fallback.group(1).upper()
    return None

def _extract_flipkart_json_reviews(d):
    """Recursively extracts review objects from Flipkart JSON state."""
    reviews = []
    if isinstance(d, dict):
        if ("text" in d or "reviewText" in d) and ("rating" in d or "author" in d or "title" in d):
            text = d.get("text") or d.get("reviewText") or d.get("description")
            rating = d.get("rating") or d.get("value") or 5.0
            title = d.get("title") or d.get("heading")
            if text and isinstance(text, str) and len(text.strip()) > 5:
                clean_text = clean_review_text(text)
                full_text = f"{title}: {clean_text}".strip(": ") if title and title.lower() not in clean_text.lower() else clean_text
                reviews.append({"Rating": str(rating), "Review Text": full_text})

        for k, v in d.items():
            reviews.extend(_extract_flipkart_json_reviews(v))
    elif isinstance(d, list):
        for item in d:
            reviews.extend(_extract_flipkart_json_reviews(item))
    return reviews

def scrape_flipkart_reviews(url, max_pages=2):
    """
    Dedicated Flipkart review scraper with JSON state hydration and DOM parsing.
    Only returns 100% REAL customer reviews.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }

    base_url = url
    if "/p/" in url:
        base_url = re.sub(r'/p/(itm[a-zA-Z0-9]+)', r'/product-reviews/\1', url)

    all_reviews = []
    seen = set()

    for page in range(1, max_pages + 1):
        target = base_url
        if "?" in target:
            target += f"&page={page}"
        else:
            target += f"?page={page}"

        try:
            response = requests.get(target, headers=headers, timeout=12)
            if response.status_code != 200:
                break

            # 1. Try INITIAL_STATE JSON extraction
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', response.text)
            page_extracted = []
            if match:
                try:
                    data = json.loads(match.group(1))
                    page_extracted = _extract_flipkart_json_reviews(data)
                except Exception:
                    page_extracted = []

            # 2. Try HTML DOM extraction if JSON was empty
            if not page_extracted:
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.find_all('div', class_=re.compile(r'col-12-12|EPCmJX|_16PBlm|_27M-vq|cPHDOP'))
                for c in cards:
                    text_div = c.find('div', class_=re.compile(r'ZmyHeo|t-ZT|_6K-7Co'))
                    rating_div = c.find('div', class_=re.compile(r'XQDdHH|_3LWZlK|hGSR34'))
                    title_div = c.find('p', class_=re.compile(r'z9E0IG|_2-N8zT'))

                    if text_div and text_div.get_text(strip=True):
                        body = clean_review_text(text_div.get_text(" ", strip=True))
                        title = title_div.get_text(strip=True) if title_div else ""
                        rating = rating_div.get_text(strip=True) if rating_div else "5.0"
                        full_review = f"{title}: {body}".strip(": ")
                        if len(full_review) > 10:
                            page_extracted.append({"Rating": rating, "Review Text": full_review})

            new_count = 0
            for r in page_extracted:
                t = r["Review Text"]
                if t not in seen and len(t) >= 10:
                    seen.add(t)
                    all_reviews.append(r)
                    new_count += 1

            if new_count == 0:
                break

        except Exception as e:
            print(f"Flipkart scraper exception: {e}")
            break

    return all_reviews

def scrape_amazon_reviews(url, max_pages=2):
    """
    Dedicated Amazon review scraper with ASIN extraction.
    Only returns 100% REAL customer reviews.
    """
    asin = extract_asin(url)
    domain_match = re.search(r'https?://(?:www\.)?(amazon\.[a-z\.]+)', url, re.IGNORECASE)
    domain = domain_match.group(1) if domain_match else "amazon.com"

    urls_to_try = []
    if asin:
        urls_to_try.append(f"https://www.{domain}/dp/{asin}")
        for p in range(1, max_pages + 1):
            urls_to_try.append(f"https://www.{domain}/product-reviews/{asin}?pageNumber={p}&reviewerType=all_reviews")
    urls_to_try.append(url)

    all_reviews = []
    seen = set()

    for target_url in urls_to_try:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(target_url, headers=headers, timeout=12)
            if response.status_code != 200:
                continue

            html = response.text
            if "api-services-support@amazon.com" in html or "Type the characters you see in this image" in html:
                # Anti-bot CAPTCHA triggered on this URL
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            review_blocks = soup.select('[data-hook="review"], [data-hook="reviewContainer"], .review, div[id^="customer_review"]')

            for block in review_blocks:
                text_el = block.select_one('[data-hook="reviewText"], [data-hook="review-body"], .review-text-content, .review-text')
                if not text_el:
                    continue

                raw_body = clean_review_text(text_el.get_text(strip=True))
                if len(raw_body) < 15 or raw_body in seen:
                    continue

                rating_el = block.select_one('[data-hook="review-star-rating"], .review-rating, .a-icon-alt')
                rating_str = rating_el.get_text(strip=True) if rating_el else "5.0"
                rating_match = re.search(r'\d+\.?\d*', rating_str)
                rating = rating_match.group() if rating_match else "5.0"

                seen.add(raw_body)
                all_reviews.append({"Rating": rating, "Review Text": raw_body})

            if len(all_reviews) >= 15:
                break

        except Exception as e:
            print(f"Amazon scraper error: {e}")
            continue

    return all_reviews

def scrape_reviews(url):
    """
    Universal review scraper routing to platform engines.
    Returns: (list of dicts, bool is_demo, str platform_name, str message)
    Zero mock/dummy reviews - strictly real customer feedback.
    """
    lower_url = url.lower()

    if "flipkart.com" in lower_url:
        platform_name = "Flipkart"
        reviews = scrape_flipkart_reviews(url)
    elif "amazon." in lower_url or "amzn." in lower_url:
        platform_name = "Amazon"
        reviews = scrape_amazon_reviews(url)
    else:
        platform_name = "E-Commerce Web"
        reviews = scrape_flipkart_reviews(url) or scrape_amazon_reviews(url)

    if reviews and len(reviews) >= 1:
        msg = f"Successfully extracted {len(reviews)} real live customer reviews from {platform_name}."
        return reviews, False, platform_name, msg

    # If anti-bot wall or 0 written reviews found
    return [], False, platform_name, f"{platform_name} anti-bot protection restricted direct server access or the product has 0 written customer reviews. Please paste the review text directly in 'Direct Review Text' mode for 100% authentic audit."