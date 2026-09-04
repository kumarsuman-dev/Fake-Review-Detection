import re
import emoji
from nltk.stem import PorterStemmer

# Initialize Porter Stemmer (deterministic, zero download required)
stemmer = PorterStemmer()

# Standard NLTK English Stopwords (self-contained to eliminate 100MB+ nltk_data bundle)
ENGLISH_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
    'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
    'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
    'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
    'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
    "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain',
    'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't",
    'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma',
    'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't",
    'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
    'wouldn', "wouldn't"
}

# Contraction expansion dictionary
CONTRACTIONS = {
    "ain't": "am not", "aren't": "are not", "can't": "can not", "can't've": "can not have",
    "cause": "because", "could've": "could have", "couldn't": "could not", "couldn't've": "could not have",
    "didn't": "did not", "doesn't": "does not", "don't": "do not", "hadn't": "had not",
    "hasn't": "has not", "haven't": "have not", "he's": "he is", "how's": "how is",
    "i'm": "i am", "i've": "i have", "isn't": "is not", "it's": "it is", "let's": "let us",
    "should've": "should have", "shouldn't": "should not", "that's": "that is", "there's": "there is",
    "they're": "they are", "they've": "they have", "wasn't": "was not", "we're": "we are",
    "we've": "we have", "weren't": "were not", "what's": "what is", "where's": "where is",
    "who's": "who is", "why's": "why is", "won't": "will not", "would've": "would have",
    "wouldn't": "would not", "you're": "you are", "you've": "you have"
}

def handle_emojis(text):
    """Converts emojis into text descriptions."""
    try:
        return emoji.demojize(text)
    except Exception:
        return text

def lemmatize_and_stem(r):
    """Tokenizes, filters stopwords, and applies Porter stemming."""
    # Split tokens matching alphanumeric and punctuation
    words = re.findall(r"\w+|[^\w\s]", r)
    words = [w for w in words if w not in ENGLISH_STOPWORDS]
    stemmed_words = [stemmer.stem(w) for w in words]
    return " ".join(stemmed_words)

def preprocess_text(r):
    """Performs text preprocessing including lowercasing, currency expansion,
    contractions, emoji handling, stopword removal, and stemming."""
    r = str(r).lower().strip()

    # Replace common symbols with text representations
    r = r.replace("%", " percent")
    r = r.replace("$", " dollar ")
    r = r.replace("₹", " rupee ")
    r = r.replace("€", " euro ")
    r = r.replace("@", " at ")

    # Numerical abbreviations
    r = r.replace(",000,000,000 ", "b ")
    r = r.replace(",000,000 ", "m ")
    r = r.replace(",000 ", "k ")
    r = re.sub(r"([0-9]+)000000000", r"\1b", r)
    r = re.sub(r"([0-9]+)000000", r"\1m", r)
    r = re.sub(r"([0-9]+)000", r"\1k", r)

    # Expand contractions
    r_decontracted = [CONTRACTIONS.get(word, word) for word in r.split()]
    r = " ".join(r_decontracted)

    # Remove HTML tags
    r = re.sub(r"<.*?>", "", r)

    # Handle emojis
    r = handle_emojis(r)

    # Lemmatization / Stemming
    r = lemmatize_and_stem(r)

    return r