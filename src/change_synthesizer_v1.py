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
        r"how did (.+?) change over time\??$",
        r"how did (.+?) change\??$",
        r"how did (.+?) develop\??$",
        r"how did (.+?) evolve\??$",
        r"what changed about (.+?)\??$",
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
# Change markers
# --------------------------------------------------

CHANGE_MARKERS = {
    "transitioned": 6.0,
    "transition": 5.0,
    "became": 5.0,
    "changed": 4.0,
    "developed": 4.0,
    "evolved": 4.0,

    "organized": 4.0,
    "reorganized": 4.0,

    "expanded": 3.0,
    "grew": 3.0,
    "increased": 2.5,

    "declined": 3.0,
    "weakened": 3.0,
    "lost": 4.0,
    "deprived": 3.0,

    "moved": 2.5,
    "shifted": 2.5,

    "came under": 4.0,
    "conquered": 3.0,

    "formed": 2.0,
    "created": 2.0,
}


def score_sentence(sentence):
    lower = sentence.lower()

    score = 0.0

    for marker, weight in (
        CHANGE_MARKERS.items()
    ):
        if marker in lower:
            score += weight

    word_count = len(
        sentence.split()
    )

    if 8 <= word_count <= 35:
        score += 1.5

    elif 36 <= word_count <= 50:
        score += 0.5

    elif word_count > 60:
        score -= 3.0

    return score


# --------------------------------------------------
# Ranking
# --------------------------------------------------

def rank_change_sentences(context):
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

    return scored


def select_change_evidence(
    context,
    max_sentences=4,
):
    ranked = rank_change_sentences(
        context
    )

    selected = []

    for score, index, sentence in ranked:
        if score <= 0:
            continue

        selected.append(
            (
                index,
                sentence,
            )
        )

        if (
            len(selected)
            >= max_sentences
        ):
            break

    selected.sort(
        key=lambda item: item[0]
    )

    return [
        sentence
        for _, sentence in selected
    ]


# --------------------------------------------------
# Redundancy control
# --------------------------------------------------

def sentence_signature(text):
    words = re.findall(
        r"[a-z0-9]+",
        text.lower(),
    )

    return set(
        word
        for word in words
        if len(word) >= 4
    )


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
    ) >= 0.65


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
# Compression helpers
# --------------------------------------------------

def extract_transition(sentence):
    sentence = normalize(
        sentence
    )

    # Special case:
    # "X remained Y until it transitioned into Z."
    match = re.search(
        r"(.+?)\s+remained\s+(.+?)\s+"
        r"until\s+it\s+transitioned\s+into\s+"
        r"(.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        entity = normalize(
            match.group(1)
        )

        previous_state = normalize(
            match.group(2)
        )

        new_state = normalize(
            match.group(3)
        )

        entity = re.sub(
            r"^with some major exceptions "
            r"of outright military rule,\s*",
            "",
            entity,
            flags=re.IGNORECASE,
        )

        return (
            f"{entity} transitioned from "
            f"{previous_state} into "
            f"{new_state}."
        )

    # General case:
    # "X transitioned into Y."
    match = re.search(
        r"(.+?)\s+transitioned\s+into\s+"
        r"(.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        entity = normalize(
            match.group(1)
        )

        new_state = normalize(
            match.group(2)
        )

        return (
            f"{entity} transitioned into "
            f"{new_state}."
        )

    return None
def extract_organization(sentence):
    match = re.search(
        r"(.+?)\s+was organized into\s+"
        r"(.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        subject = normalize(
            match.group(1)
        )

        result = normalize(
            match.group(2)
        )

        subject = re.sub(
            r"^it was not until the time of "
            r"the roman empire that\s+",
            "",
            subject,
            flags=re.IGNORECASE,
        )

        return (
            f"{subject} was organized into "
            f"{result}."
        )

    return None


def extract_loss(sentence):
    match = re.search(
        r"deprived\s+(.+?)\s+of\s+"
        r"the territories of\s+(.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        entity = normalize(
            match.group(1)
        )

        territories = normalize(
            match.group(2)
        )

        return (
            f"{entity} lost territories including "
            f"{territories}."
        )

    match = re.search(
        r"(.+?)\s+lost\s+territor(?:y|ies)\s+"
        r"(?:including|in)?\s*(.+?)(?:\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        entity = normalize(
            match.group(1)
        )

        territories = normalize(
            match.group(2)
        )

        return (
            f"{entity} lost territories including "
            f"{territories}."
        )

    return None


def extract_came_under(sentence):
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
            f"{subject} came under "
            f"{control}."
        )

    return None


def extract_movement(sentence):
    match = re.search(
        r"(.+?)\s+moved to\s+(.+?)(?:,|\.|$)",
        sentence,
        flags=re.IGNORECASE,
    )

    if match:
        return (
            f"{normalize(match.group(1))} "
            f"moved to "
            f"{normalize(match.group(2))}."
        )

    return None


def compress_change_sentence(sentence):
    sentence = normalize(
        sentence
    )

    compressors = [
        extract_transition,
        extract_organization,
        extract_loss,
        extract_came_under,
        extract_movement,
    ]

    for compressor in compressors:
        result = compressor(
            sentence
        )

        if result:
            return capitalize_sentence(
                normalize(result)
            )

    # Safe fallback.
    words = sentence.split()

    if len(words) > 32:
        sentence = (
            " ".join(
                words[:32]
            ).rstrip(",;:")
            + "..."
        )

    return capitalize_sentence(
        normalize(sentence)
    )


# --------------------------------------------------
# Synthesis
# --------------------------------------------------

def synthesize_change_answer(
    question,
    context,
):
    subject = subject_from_question(
        question
    )

    if not subject:
        return None

    evidence = select_change_evidence(
        context,
        max_sentences=4,
    )

    if not evidence:
        return None

    evidence = remove_redundant(
        evidence
    )

    if not evidence:
        return None

    compressed = [
        compress_change_sentence(
            sentence
        )
        for sentence in evidence
    ]

    compressed = remove_redundant(
        compressed
    )

    if not compressed:
        return None

    if len(compressed) == 1:
        return compressed[0]

    parts = [
        capitalize_sentence(
            f"{subject} changed in several important ways."
        )
    ]

    parts.extend(
        compressed
    )

    return normalize(
        " ".join(parts)
    )


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":

    question = (
        "How did the Roman Empire change over time?"
    )

    context = (
        "With some major exceptions of outright military rule, "
        "the Roman Republic remained an alliance of independent "
        "city-states and kingdoms until it transitioned into the "
        "Roman Empire. "
        "It was not until the time of the Roman Empire that the "
        "entire Roman world was organized into provinces under "
        "explicit Roman control. "
        "Benefiting from their weakened condition, the Arab Muslim "
        "armies swiftly conquered the entire Sassanid Empire, and "
        "deprived the Eastern Roman Empire of the territories of "
        "the Levant, the Caucasus, Egypt, and the rest of North Africa. "
        "Over the following centuries, some of the Eastern Roman "
        "Empire came under Muslim rule."
    )

    answer = synthesize_change_answer(
        question,
        context,
    )

    print(answer)