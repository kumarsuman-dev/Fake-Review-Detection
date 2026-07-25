import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from langdetect import detect

# Pre-defined mock reviews for demo/fallback purposes
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
    """Detects the product category from the URL string."""
    url_lower = url.lower()
    if any(k in url_lower for k in ["headphone", "earbud", "sony", "audio", "noise", "sound", "speaker", "pods"]):
        return "headphones"
    elif any(k in url_lower for k in ["kindle", "book", "reader", "paperwhite", "novel"]):
        return "kindle"
    elif any(k in url_lower for k in ["chair", "desk", "office", "furniture", "seat", "stool"]):
        return "chair"
    return "default"

def scrape_reviews(url):
    """
    Scrapes customer reviews from a given product page URL.
    Falls back to mock reviews if Amazon blocks the request or finds 0 reviews.
    
    Parameters:
    url (str): The URL of the product page to scrape reviews from.
    
    Returns:
    (pd.DataFrame, bool): A DataFrame containing reviews, and a boolean indicating if demo fallback was used.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US, en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    category = detect_product_category(url)
    
    try:
        # Fetch the HTML content from the given URL
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for failed requests
        
        # Check if we hit the CAPTCHA page
        if "api-services-support@amazon.com" in response.text or "Captcha" in response.text or "automated access" in response.text:
            print("Amazon CAPTCHA detected. Falling back to demo reviews.")
            df_mock = pd.DataFrame(MOCK_REVIEWS[category])
            return df_mock, True
            
        soup = BeautifulSoup(response.content, 'html.parser')
        reviews = []
        
        # Try various selectors for review blocks
        review_selectors = ['[data-hook="review"]', '.review', '.a-section.review']
        review_blocks = []
        for selector in review_selectors:
            review_blocks = soup.select(selector)
            if review_blocks:
                break
                
        # Loop through each review block on the webpage
        for review_block in review_blocks:
            # Try various selectors for review text
            review_text = 'N/A'
            text_selectors = ['[data-hook="review-body"]', '.review-text-content', '.review-text', '.a-size-base.review-text']
            for ts in text_selectors:
                el = review_block.select_one(ts)
                if el:
                    review_text = el.get_text(strip=True)
                    break
            
            # Handling "Read more" scenario by extracting the full review if available
            if 'Read more' in review_text:
                full_review = review_block.select_one('.full-review')
                if full_review:
                    review_text = full_review.get_text(strip=True)
            
            # Try various selectors for rating
            rating_text = 'N/A'
            rating_selectors = ['[data-hook="review-star-rating"]', '.review-rating', '.a-icon-alt']
            for rs in rating_selectors:
                el = review_block.select_one(rs)
                if el:
                    rating_text = el.get_text(strip=True)
                    break
                    
            rating_match = re.search(r'\d+\.?\d*', rating_text)  # Extract numerical rating
            rating = rating_match.group() if rating_match else 'N/A'

            # Clean rating representation
            if rating == 'N/A' and 'out of 5 stars' in rating_text:
                rating = rating_text.split(' ')[0]

            # Perform language detection to ensure only English reviews are included
            try:
                if review_text != 'N/A' and len(review_text) > 10:
                    lang = detect(review_text)
                    if lang == 'en':  
                        reviews.append({
                            "Rating": rating,
                            "Review Text": review_text
                        })
            except Exception as lang_err:
                # If language detection fails, check if contains english words or just continue
                # To be safe, if we don't detect, but text is large, we can include it
                continue

        # Convert extracted reviews into a DataFrame
        if reviews and len(reviews) >= 2:
            df = pd.DataFrame(reviews)
            return df, False
        else:
            print("No/too few English reviews found on the page. Falling back to demo reviews.")
            df_mock = pd.DataFrame(MOCK_REVIEWS[category])
            return df_mock, True

    except Exception as e:
        print(f"Error scraping reviews ({e}). Falling back to demo reviews.")
        df_mock = pd.DataFrame(MOCK_REVIEWS[category])
        return df_mock, True