import re
import json
import pandas as pd
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CURL_CFFI = False

# Fallback benchmark dataset if a product page has 0 reviews or network fails
MOCK_REVIEWS = {
    "headphones": [
        {"Rating": "5.0", "Review Text": "The sound quality is outstanding. Active noise cancellation blocks out almost all office noise. The earcups are super comfortable for long hours."},
        {"Rating": "4.0", "Review Text": "Bought these for my daily commute. The sound is good and battery life is great, but the headband feels a bit tight on my head."},
        {"Rating": "1.0", "Review Text": "Extremely disappointed. The left earbud stopped working after just two weeks. For this price, I expected way better build quality."},
        {"Rating": "5.0", "Review Text": "This product is very excellent. The sound is very good and the performance is the best. I am extremely satisfied with this great item. Highly recommend."},
        {"Rating": "5.0", "Review Text": "Great headphones, very fast shipping. The quality is perfect and the design is very nice. I am very happy with my purchase of this product."},
        {"Rating": "2.0", "Review Text": "Sound is okay, but Bluetooth connectivity is terrible. It keeps disconnecting from my phone even when it is in my pocket. Frustrating."},
        {"Rating": "5.0", "Review Text": "Super comfort. Beautiful color. Very good sound. Highly recommend this wonderful model to everyone. Best purchase ever."},
        {"Rating": "4.5", "Review Text": "The battery life is the real highlight here—lasts almost 30 hours on a single charge. Sound signature is a bit bass-heavy but easily adjustable via the app."}
    ],
    "kindle": [
        {"Rating": "5.0", "Review Text": "The screen is incredibly clear and looks just like real paper. Reading in direct sunlight is a breeze, and the battery lasts for weeks."},
        {"Rating": "4.0", "Review Text": "It's a nice device, but the page turn animation feels slightly slow compared to my previous model. Still, it's very lightweight and easy to hold."},
        {"Rating": "2.0", "Review Text": "I hate the new software interface. It is confusing to navigate and keeps freezing. I might return this and go back to physical books."},
        {"Rating": "5.0", "Review Text": "Very good reader. This reader is the best reader in the world. Extremely satisfied with the reader performance. Very nice product."},
        {"Rating": "5.0", "Review Text": "Excellent item. The design is beautiful and the function is perfect. I like this product very much. Fast shipping, great seller."},
        {"Rating": "3.0", "Review Text": "The hardware is good, but Amazon ads on the lock screen are highly annoying. You have to pay extra to remove them. Feels cheap."},
        {"Rating": "5.0", "Review Text": "This reader is perfect. Extremely satisfied. Very good lighting. I read books every day now. Best product in the market."},
        {"Rating": "4.0", "Review Text": "Warm light setting makes a huge difference for night reading. The USB-C charging is finally here, which makes traveling with it much easier."}
    ],
    "chair": [
        {"Rating": "5.0", "Review Text": "Assembly was a bit tricky and took about 45 minutes, but once built, it offers excellent lumbar support. My back pain has significantly improved."},
        {"Rating": "4.0", "Review Text": "The seat cushion is firm, maybe a bit too firm for some, but it keeps my posture correct. The armrests are adjustable which is a nice touch."},
        {"Rating": "1.0", "Review Text": "The squeaking noise is unbearable! Every time I lean back it makes a loud creaking sound. The hydraulic lift also slowly sinks over time."},
        {"Rating": "5.0", "Review Text": "This chair is very wonderful. I am extremely satisfied with the chair performance. It has great comfort and excellent quality. Very good."},
        {"Rating": "5.0", "Review Text": "Perfect product, very fast shipping. The item is of high quality and the performance is outstanding. Very happy with this purchase."},
        {"Rating": "2.0", "Review Text": "The mesh backing started fraying after two months. Also, the wheels do not glide smoothly on hardwood floors. Not worth the price tag."},
        {"Rating": "5.0", "Review Text": "Very nice item. This chair is the best chair. Extremely comfortable. I sit for hours without pain. Very satisfied customer."},
        {"Rating": "4.5", "Review Text": "Solid steel frame makes the chair feel very sturdy. Tilt mechanism is smooth and tension adjustment works perfectly for my weight."}
    ],
    "default": [
        {"Rating": "4.0", "Review Text": "Exactly what I was looking for. The build quality is decent and it performs as advertised. Good value for money."},
        {"Rating": "3.0", "Review Text": "Item arrived with a small scratch on the side. Customer service was helpful and offered a partial refund, but still a bit annoying."},
        {"Rating": "1.0", "Review Text": "Waste of money. Did not work out of the box. Tried contacting the seller but received no response. Avoid this brand."},
        {"Rating": "5.0", "Review Text": "This product is the best product in the world. I am extremely satisfied with the product performance. It has great quality and excellent design. Very good."},
        {"Rating": "5.0", "Review Text": "Highly recommended. The product is of perfect quality and works very well. I am very happy with this purchase. Outstanding service."},
        {"Rating": "2.5", "Review Text": "Design is okay, but performance is mediocre. It gets very hot after 15 minutes of usage. Will probably return it."},
        {"Rating": "5.0", "Review Text": "Very excellent item. The performance is wonderful. Extremely satisfied with this purchase. Super fast delivery and great seller."},
        {"Rating": "4.5", "Review Text": "Does exactly what it's supposed to do. Packaged nicely and instruction manual was clear. Build material feels slightly cheap but it works."}
    ]
}

def detect_product_category(url):
    url_lower = url.lower()
    if any(k in url_lower for k in ["headphone", "earbud", "sony", "audio", "noise", "sound", "speaker", "pods", "airpod"]):
        return "headphones"
    elif any(k in url_lower for k in ["kindle", "book", "reader", "paperwhite", "novel"]):
        return "kindle"
    elif any(k in url_lower for k in ["chair", "desk", "office", "furniture", "seat", "stool"]):
        return "chair"
    return "default"

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
    """Recursively extracts review objects from Flipkart window.__INITIAL_STATE__."""
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

def scrape_flipkart_reviews(url, max_pages=3):
    """
    Dedicated Flipkart multi-page review scraper.
    Uses JSON hydration parsing from window.__INITIAL_STATE__ and DOM fallback.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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
            kwargs = {"timeout": 15, "headers": headers}
            if HAS_CURL_CFFI:
                kwargs["impersonate"] = "chrome120"

            response = cffi_requests.get(target, **kwargs)
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

            # 2. Try HTML Fallback if JSON yielded nothing
            if not page_extracted:
                soup = BeautifulSoup(response.content, 'html.parser')
                verified_elements = soup.find_all(string=re.compile(r'Certified Buyer|Flipkart Customer'))
                for el in verified_elements:
                    container = el.find_parent(lambda tag: tag.name == 'div' and len(tag.get_text()) > 40)
                    if container:
                        rating_el = container.find(string=re.compile(r'^[1-5](\.0)?$'))
                        rating = "5.0"
                        if rating_el:
                            rm = re.search(r'\d+\.?\d*', rating_el.get_text() if hasattr(rating_el, 'get_text') else str(rating_el))
                            if rm: rating = rm.group()

                        txt = clean_review_text(container.get_text(" ", strip=True))
                        txt = re.sub(r'^[1-5](\.0)?\s*', '', txt).strip()
                        if len(txt) > 15:
                            page_extracted.append({"Rating": rating, "Review Text": txt})

            new_in_page = 0
            for r in page_extracted:
                t = r["Review Text"]
                if t not in seen and len(t) >= 10:
                    seen.add(t)
                    all_reviews.append(r)
                    new_in_page += 1

            # Stop if no reviews on this page or first page had none
            if new_in_page == 0:
                break

        except Exception as e:
            print(f"Flipkart scraper exception on page {page}: {e}")
            break

    return all_reviews

def scrape_amazon_reviews(url, max_pages=3):
    """Dedicated Amazon review scraper with ASIN extraction and TLS impersonation."""
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
            kwargs = {
                "timeout": 15,
                "headers": {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Upgrade-Insecure-Requests": "1"
                }
            }
            if HAS_CURL_CFFI:
                kwargs["impersonate"] = "chrome120"

            response = cffi_requests.get(target_url, **kwargs)
            if response.status_code != 200:
                continue

            html = response.text
            if "api-services-support@amazon.com" in html or "Type the characters you see in this image" in html:
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

            if len(all_reviews) >= 20:
                break

        except Exception as e:
            print(f"Amazon scraper error: {e}")
            continue

    return all_reviews

def scrape_reviews(url):
    """
    Universal review scraper routing to dedicated platform engines.
    Returns: (pd.DataFrame, bool is_demo, str platform_name, str notice_message)
    """
    category = detect_product_category(url)
    lower_url = url.lower()
    
    # Platform Routing
    if "flipkart.com" in lower_url:
        platform_name = "Flipkart"
        reviews = scrape_flipkart_reviews(url)
    elif "amazon." in lower_url or "amzn." in lower_url:
        platform_name = "Amazon"
        reviews = scrape_amazon_reviews(url)
    elif "walmart.com" in lower_url:
        platform_name = "Walmart"
        reviews = scrape_flipkart_reviews(url) or scrape_amazon_reviews(url)
    else:
        platform_name = "E-Commerce Web"
        reviews = scrape_flipkart_reviews(url) or scrape_amazon_reviews(url)

    # 1. Successfully extracted real live reviews
    if reviews and len(reviews) >= 1:
        msg = f"Successfully extracted {len(reviews)} real live customer reviews from {platform_name}."
        print(msg)
        return pd.DataFrame(reviews), False, platform_name, msg

    # 2. 0 reviews or automated access restricted -> Category benchmark dataset
    msg = f"{platform_name} returned 0 written reviews for this listing or restricted direct headless access. Loaded high-density benchmark reviews to evaluate model classification."
    print(f"Fallback triggered for {platform_name}: {msg}")
    df_mock = pd.DataFrame(MOCK_REVIEWS[category])
    return df_mock, True, platform_name, msg