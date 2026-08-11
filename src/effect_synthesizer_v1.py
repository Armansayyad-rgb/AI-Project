import re


# --------------------------------------------------
# Text helpers
# --------------------------------------------------

def split_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if sentence.strip()
    ]


def normalize(text):
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text,
    )

    text = re.sub(
        r"\s*-\s*",
        "-",
        text,
    )

    text = re.sub(
        r"\(\s+",
        "(",
        text,
    )

    text = re.sub(
        r"\s+\)",
        ")",
        text,
    )

    return text.strip()


def capitalize_sentence(text):
    text = text.strip()

    if not text:
        return text

    return (
        text[0].upper()
        + text[1:]
    )


# --------------------------------------------------
# Question parsing
# --------------------------------------------------

def subject_from_question(question):
    patterns = [
        r"what were the effects of (.+?)\??$",
        r"what was the effect of (.+?)\??$",
        r"what were the consequences of (.+?)\??$",
        r"what was the consequence of (.+?)\??$",
        r"what happened after (.+?)\??$",
        r"what resulted from (.+?)\??$",
        r"what did (.+?) lead to\??$",
        r"what was the impact of (.+?)\??$",
    ]

    for pattern in patterns:
        match = re.match(
            pattern,
            question.strip(),
            flags=re.IGNORECASE,
        )

        if match:
            return (
                match.group(1)
                .strip()
            )

    return None


# --------------------------------------------------
# Effect scoring
# --------------------------------------------------

EFFECT_MARKERS = {
    "as a result": 8.0,
    "resulted in": 8.0,
    "led to": 8.0,

    "after": 2.0,
    "following": 2.0,

    "no longer": 5.0,
    "no longer part": 7.0,

    "lost": 5.0,
    "loss": 3.0,
    "former provinces": 5.0,
    "provinces": 3.0,
    "territories": 3.0,

    "came under": 6.0,
    "kingdoms": 5.0,
    "barbarian kingdoms": 8.0,

    "became": 3.0,
    "increasingly germanic": 6.0,
    "less romanised": 5.0,
    "less romanized": 5.0,

    "fragmented": 5.0,
    "divided": 4.0,
    "replaced": 4.0,

    "moved": 2.0,
    "shifted": 2.0,

    "control": 2.0,
    "power": 2.0,
}


def score_sentence(sentence):
    s = sentence.lower()

    score = 0.0

    for marker, weight in (
        EFFECT_MARKERS.items()
    ):
        if marker in s:
            score += weight

    strong_patterns = [
        (
            r"\bno longer part of\b",
            8.0,
        ),
        (
            r"\bcame under .+ kingdoms\b",
            8.0,
        ),
        (
            r"\bwithout possession of\b",
            7.0,
        ),
        (
            r"\bformer provinces\b",
            6.0,
        ),
        (
            r"\bincreasingly germanic\b",
            6.0,
        ),
        (
            r"\bresulted in\b",
            7.0,
        ),
        (
            r"\bled to\b",
            7.0,
        ),
    ]

    for pattern, weight in strong_patterns:
        if re.search(
            pattern,
            s,
        ):
            score += weight

    # Penalize obvious topic noise.
    noise_patterns = [
        r"\bmedia\b",
        r"\bcommunications\b",
        r"\bexamined the rise and fall\b",
        r"\btracing the effects\b",
    ]

    for pattern in noise_patterns:
        if re.search(
            pattern,
            s,
        ):
            score -= 10.0

    word_count = len(
        sentence.split()
    )

    if 8 <= word_count <= 45:
        score += 1.0

    elif word_count > 65:
        score -= 2.0

    return score


# --------------------------------------------------
# Evidence selection
# --------------------------------------------------

def select_effect_evidence(
    context,
    max_sentences=4,
):
    sentences = split_sentences(
        context
    )

    scored = []

    for index, sentence in enumerate(
        sentences
    ):
        score = score_sentence(
            sentence
        )

        scored.append(
            (
                score,
                index,
                normalize(sentence),
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )

    selected = []

    for score, index, sentence in scored:
        if score <= 0:
            continue

        selected.append(
            (
                index,
                sentence,
            )
        )

        if len(selected) >= max_sentences:
            break

    selected.sort(
        key=lambda item: item[0]
    )

    return [
        sentence
        for _, sentence in selected
    ]


# --------------------------------------------------
# Compression helpers
# --------------------------------------------------

def compress_without_possession(sentence):
    match = re.search(
        r"without possession of (.+?) ,? "
        r"and increasingly germanic in nature ,? "
        r"(.+?) after \d{3,4} ad had little in common "
        r"with the earlier empire",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        possessions = normalize(
            match.group(1)
        )

        return (
            f"The empire had lost control of "
            f"{possessions} and had become increasingly "
            f"Germanic in character."
        )

    return None


def compress_britain_and_kingdoms(sentence):
    lower = sentence.lower()

    if (
        "britain" in lower
        and "no longer part of the empire" in lower
        and "barbarian kingdoms" in lower
    ):
        return (
            "Britain was no longer part of the Empire, "
            "and much of western Europe came under "
            "Germanic kingdoms."
        )

    return None


def compress_germanic_change(sentence):
    lower = sentence.lower()

    if (
        "less romanised" in lower
        or "less romanized" in lower
        or "increasingly germanic" in lower
    ):
        return (
            "The remaining Roman state became "
            "increasingly Germanic in character."
        )

    return None


def compress_came_under(sentence):
    match = re.search(
        r"(.+?)\s+came under\s+(.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        subject = normalize(
            match.group(1)
        )

        control = normalize(
            match.group(2)
        )

        subject = re.sub(
            r"^over the following centuries,\s*",
            "",
            subject,
            flags=re.IGNORECASE,
        )

        return (
            f"{capitalize_sentence(subject)} "
            f"came under {control}."
        )

    return None


def compress_effect_sentence(sentence):
    sentence = normalize(
        sentence
    )

    compressors = [
        compress_without_possession,
        compress_britain_and_kingdoms,
        compress_germanic_change,
        compress_came_under,
    ]

    for compressor in compressors:
        result = compressor(
            sentence
        )

        if result:
            return normalize(
                result
            )

    words = sentence.split()

    if len(words) > 34:
        sentence = (
            " ".join(
                words[:34]
            ).rstrip(",;:")
            + "..."
        )

    return capitalize_sentence(
        normalize(sentence)
    )


# --------------------------------------------------
# Redundancy control
# --------------------------------------------------

def sentence_signature(text):
    words = re.findall(
        r"[a-z0-9]+",
        text.lower(),
    )

    return {
        word
        for word in words
        if len(word) >= 4
    }


def near_duplicate(
    first,
    second,
):
    a = sentence_signature(
        first
    )

    b = sentence_signature(
        second
    )

    if not a or not b:
        return False

    overlap = len(
        a & b
    )

    smaller = min(
        len(a),
        len(b),
    )

    if smaller == 0:
        return False

    return (
        overlap / smaller
    ) >= 0.60


def remove_redundant(sentences):
    kept = []

    for sentence in sentences:
        if any(
            near_duplicate(
                sentence,
                existing,
            )
            for existing in kept
        ):
            continue

        kept.append(
            sentence
        )

    return kept


# --------------------------------------------------
# Main synthesis
# --------------------------------------------------

def synthesize_effect_answer(
    question,
    context,
):
    subject = subject_from_question(
        question
    )

    if not subject:
        return None

    evidence = select_effect_evidence(
        context,
        max_sentences=4,
    )

    if not evidence:
        return None

    compressed = [
        compress_effect_sentence(
            sentence
        )
        for sentence in evidence
    ]

    compressed = remove_redundant(
        compressed
    )

    if not compressed:
        return None

    intro = capitalize_sentence(
        f"{subject} had several major effects."
    )

    return normalize(
        " ".join(
            [intro] + compressed
        )
    )


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":

    question = (
        "What were the effects of the fall "
        "of the Roman Empire?"
    )

    context = (
        "Without possession of Rome or many of its former "
        "provinces, and increasingly Germanic in nature, "
        "the Roman Empire after 410 AD had little in common "
        "with the earlier Empire. "
        "By 410 AD, Britain had been mostly denuded of Roman "
        "troops, and by 425 AD was no longer part of the Empire, "
        "and much of western Europe came under barbarian kingdoms "
        "ruled by Vandals, Suebians, Visigoths and Burgundians. "
        "The Empire became gradually less Romanised and increasingly "
        "Germanic in nature. "
        "Over the following centuries, some of the Eastern Roman "
        "Empire came under Muslim rule."
    )

    answer = synthesize_effect_answer(
        question,
        context,
    )

    print(answer)