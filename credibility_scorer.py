import re


def h_clickbait(text):
    score = 100
    words = text.split()

    if len(words) == 0:
        return 50

    caps_count = sum(1 for w in words if w.isupper() and len(w) > 2)
    caps_ratio = caps_count / len(words)
    score -= min(caps_ratio * 200, 30)

    exclaim_count = text.count("!")
    score -= min(exclaim_count * 5, 20)

    clickbait_words = [
        "shocking", "unbelievable", "you won't believe", "must see",
        "breaking", "urgent", "exposed", "secret", "bombshell",
        "destroyed", "slammed", "blasted", "epic", "insane",
        "mind-blowing", "jaw-dropping", "horrifying", "disgusting",
        "share before deleted", "they don't want you to know",
        "wake up", "the truth about", "exposed", "busted"
    ]
    text_lower = text.lower()
    clickbait_matches = sum(1 for w in clickbait_words if w in text_lower)
    score -= min(clickbait_matches * 8, 30)

    return max(0, min(100, round(score)))


def h_source_quality(text):
    score = 30
    text_lower = text.lower()

    source_patterns = [
        "according to", "said in a statement", "reported by",
        "officials said", "spokesperson said", "press release",
        "reuters", "associated press", "pti", "ani", "ians",
        "quoted as saying", "in an interview", "told reporters",
        "government spokesperson", "ministry of", "press conference",
        "data shows", "study found", "research published",
        "census", "survey", "statistics"
    ]

    for pattern in source_patterns:
        if pattern in text_lower:
            score += 8

    name_pattern = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', text)
    if len(name_pattern) >= 2:
        score += 10

    date_patterns = re.findall(r'\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}', text)
    if date_patterns:
        score += 10

    return max(0, min(100, round(score)))


def h_emotional_tone(text):
    score = 100
    text_lower = text.lower()
    words = text_lower.split()

    if len(words) == 0:
        return 50

    emotional_words = [
        "outrage", "fury", "horrific", "terrifying", "evil",
        "corrupt", "traitor", "disgrace", "pathetic", "stupid",
        "idiot", "moron", "criminal", "monster", "villain",
        "hero", "savior", "miracle", "incredible", "amazing",
        "wonderful", "perfect", "genius", "brilliant", "divine",
        "hate", "love", "destroy", "crush", "annihilate"
    ]
    emotional_count = sum(1 for w in emotional_words if w in words)
    score -= min(emotional_count * 7, 40)

    attack_phrases = [
        "wake up", "open your eyes", "sheep", "sheeple",
        "liberal media", "fake news media", "mainstream media lies",
        "you are being lied to", "they don't want you"
    ]
    for phrase in attack_phrases:
        if phrase in text_lower:
            score -= 10

    return max(0, min(100, round(score)))


def h_structure(text):
    score = 50
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    if len(sentences) == 0:
        return 30

    avg_sent_len = len(words) / len(sentences)
    if 12 <= avg_sent_len <= 35:
        score += 15
    elif avg_sent_len > 50 or avg_sent_len < 5:
        score -= 15

    quote_count = text.count('"') // 2
    if quote_count >= 1:
        score += 10

    para_count = text.count("\n\n") + text.count("\n")
    if para_count >= 2:
        score += 10

    if 100 < len(words) < 2000:
        score += 10

    return max(0, min(100, round(score)))


def greedy_credibility_score(text):
    scores = {
        "clickbait_score": h_clickbait(text),
        "source_quality": h_source_quality(text),
        "emotional_tone": h_emotional_tone(text),
        "structure_quality": h_structure(text)
    }

    weights = {
        "clickbait_score": 0.20,
        "source_quality": 0.30,
        "emotional_tone": 0.25,
        "structure_quality": 0.25
    }

    overall = sum(scores[k] * weights[k] for k in scores)
    overall = round(overall, 1)

    if overall >= 70:
        verdict = "HIGH credibility - looks like a well-written news article"
    elif overall >= 50:
        verdict = "MEDIUM credibility - has some red flags but could be real"
    elif overall >= 30:
        verdict = "LOW credibility - several warning signs detected"
    else:
        verdict = "VERY LOW credibility - likely fake or heavily biased"

    return overall, scores, verdict
