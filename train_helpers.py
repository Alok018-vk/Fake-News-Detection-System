import re


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"^[^(]{0,60}\(reuters\)\s*-?\s*", "", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_news_text(text):
    text_lower = text.lower().strip()
    words = text_lower.split()
    word_count = len(words)

    if word_count < 10:
        return False, "Text is too short (less than 10 words). Need more content."

    news_keywords = [
        "said", "report", "according", "government", "president",
        "minister", "police", "court", "election", "official",
        "statement", "announced", "sources", "india", "country",
        "party", "news", "investigation", "attack", "protest",
        "parliament", "congress", "agency", "media", "press",
        "journalist", "breaking", "update", "crisis", "military",
        "killed", "arrested", "economy", "policy", "law",
        "supreme", "high court", "modi", "bjp", "congress",
        "aap", "nda", "opposition", "lok sabha", "rajya sabha",
        "chief minister", "prime minister", "state", "district",
        "nation", "international", "world", "united nations"
    ]

    matches = sum(1 for kw in news_keywords if kw in text_lower)

    if matches >= 2:
        return True, "Looks like a news article."

    sentence_count = text.count(".") + text.count("!") + text.count("?")
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)

    if sentence_count >= 2 and 3.5 < avg_word_len < 8 and word_count > 30:
        return True, "Text has news-like structure."

    if word_count >= 50:
        return True, "Long text - may not be news but will try to classify."

    return False, "This doesn't look like a news article. Try pasting an actual news story."


def classify_text_type(text):
    text_lower = text.lower()

    social_patterns = ["#", "@", "lol", "omg", "lmao", "bruh", "smh",
                       "tweet", "retweet", "follow", "dm me", "tbh"]
    social_score = sum(1 for p in social_patterns if p in text_lower)

    opinion_patterns = ["i think", "i believe", "in my opinion", "i feel",
                        "personally", "my view", "we should", "must be",
                        "clearly", "obviously"]
    opinion_score = sum(1 for p in opinion_patterns if p in text_lower)

    news_patterns = ["reported", "according to", "officials said",
                     "sources say", "press release", "investigation",
                     "government", "authorities", "spokesperson"]
    news_score = sum(1 for p in news_patterns if p in text_lower)

    scores = {"news": news_score, "social_media": social_score,
              "opinion": opinion_score}
    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return "other"
    return best
