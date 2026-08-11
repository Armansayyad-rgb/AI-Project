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

    return text.strip()


def clean_subject(text):
    text = normalize(
        text
    )

    text = re.sub(
        r"^(?:the )?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


# --------------------------------------------------
# Question detection
# --------------------------------------------------

def subject_from_question(question):
    patterns = [
        r"who were the main leaders of (.+?)[.?!]?$",
        r"who were the key leaders of (.+?)[.?!]?$",
        r"who were the main figures of (.+?)[.?!]?$",
        r"who were the key figures of (.+?)[.?!]?$",
        r"who were important figures in (.+?)[.?!]?$",
        r"who were the important people in (.+?)[.?!]?$",
    ]

    for pattern in patterns:
        match = re.fullmatch(
            pattern,
            question.strip(),
            flags=re.IGNORECASE,
        )

        if match:
            return normalize(
                match.group(1)
            )

    return None


# --------------------------------------------------
# Person-name detection
# --------------------------------------------------

NAME_PATTERN = re.compile(
    r"\b"
    r"[A-Z][a-z]+"
    r"(?:-[A-Z][a-z]+)?"
    r"(?:\s+[A-Z]\.)?"
    r"\s+"
    r"[A-Z][a-z]+"
    r"(?:-[A-Z][a-z]+)?"
    r"\b"
)


NON_PERSON_PHRASES = {
    "French Revolution",
    "National Convention",
    "Jacobin Club",
    "Roman Empire",
    "Roman Republic",
    "First World",
    "Second World",
    "United States",
    "Great Britain",
    "New York",
    "Bar Confederation",
    "Virgin Mary",
    "Royal Collection",
    "French National",
    "American Independence",
}


NON_PERSON_WORDS = {
    "club",
    "convention",
    "empire",
    "republic",
    "kingdom",
    "government",
    "party",
    "war",
    "confederation",
    "collection",
    "museum",
    "press",
    "university",
    "assembly",
    "army",
    "legion",
}


TITLE_PREFIXES = {
    "king",
    "queen",
    "pope",
    "emperor",
    "empress",
    "prince",
    "princess",
    "president",
    "general",
}


def looks_like_person(name):
    name = normalize(
        name
    )

    if name in NON_PERSON_PHRASES:
        return False

    lower = name.lower()

    words = lower.split()

    if any(
        word in NON_PERSON_WORDS
        for word in words
    ):
        return False

    # Reject title + first name only,
    # e.g. "King Louis".
    if (
        len(words) == 2
        and words[0] in TITLE_PREFIXES
    ):
        return False

    return True


def extract_names(sentence):
    names = []

    for match in NAME_PATTERN.finditer(
        sentence
    ):
        name = normalize(
            match.group(0)
        )

        if not looks_like_person(
            name
        ):
            continue

        names.append(
            name
        )

    return names


# --------------------------------------------------
# Leadership-context detection
# --------------------------------------------------

LEADER_CONTEXT_MARKERS = [
    "leader",
    "leaders",
    "powerful member",
    "powerful members",
    "member",
    "members",
    "politician",
    "political leader",
    "revolutionary",
    "jacobin",
    "government",
    "convention",
    "president",
    "general",
    "controlled the government",
    "secure control",
    "executive power",
]


def has_leadership_context(sentence):
    lower = sentence.lower()

    return any(
        marker in lower
        for marker in LEADER_CONTEXT_MARKERS
    )


# --------------------------------------------------
# Sentence scoring
# --------------------------------------------------

LEADER_MARKERS = {
    "leader": 5.0,
    "leaders": 5.0,
    "powerful member": 6.0,
    "powerful members": 6.0,
    "member": 3.0,
    "members": 3.0,
    "politician": 4.0,
    "political leader": 5.0,
    "revolutionary": 4.0,
    "jacobin": 5.0,
    "government": 2.5,
    "convention": 2.5,
    "president": 4.0,
    "general": 3.0,
    "secure control": 5.0,
}


NOISE_MARKERS = {
    "newspaper": -10.0,
    "painting": -8.0,
    "museum": -8.0,
    "rider": -10.0,
    "railroad": -8.0,
    "collection": -7.0,
    "song": -8.0,
    "film": -8.0,
    "cockade": -9.0,
    "colors": -8.0,
    "colour": -8.0,
}


def score_sentence(
    sentence,
    subject,
):
    lower = sentence.lower()

    names = extract_names(
        sentence
    )

    if not names:
        return -100.0

    score = 0.0

    score += min(
        12.0,
        len(names) * 4.0,
    )

    if has_leadership_context(
        sentence
    ):
        score += 8.0
    else:
        score -= 8.0

    for marker, weight in (
        LEADER_MARKERS.items()
    ):
        if marker in lower:
            score += weight

    for marker, weight in (
        NOISE_MARKERS.items()
    ):
        if marker in lower:
            score += weight

    subject_words = {
        word
        for word in re.findall(
            r"[a-z0-9']+",
            subject.lower(),
        )
        if len(word) >= 4
    }

    sentence_words = {
        word
        for word in re.findall(
            r"[a-z0-9']+",
            lower,
        )
        if len(word) >= 4
    }

    score += (
        len(
            subject_words
            & sentence_words
        )
        * 2.0
    )

    word_count = len(
        sentence.split()
    )

    if 8 <= word_count <= 45:
        score += 1.0

    elif word_count > 65:
        score -= 3.0

    return score


# --------------------------------------------------
# Evidence selection
# --------------------------------------------------

def select_leader_evidence(
    context,
    subject,
    max_sentences=2,
):
    sentences = split_sentences(
        context
    )

    scored = []

    for index, sentence in enumerate(
        sentences
    ):
        names = extract_names(
            sentence
        )

        if not names:
            continue

        if not has_leadership_context(
            sentence
        ):
            continue

        score = score_sentence(
            sentence,
            subject,
        )

        if score <= 0:
            continue

        scored.append(
            (
                score,
                index,
                normalize(sentence),
                names,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )

    return scored[
        :max_sentences
    ]


# --------------------------------------------------
# Name filtering and deduplication
# --------------------------------------------------

def deduplicate_names(names):
    seen = set()
    result = []

    for name in names:
        key = name.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            name
        )

    return result


def join_naturally(items):
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return (
            f"{items[0]} and {items[1]}"
        )

    return (
        ", ".join(
            items[:-1]
        )
        + f", and {items[-1]}"
    )


# --------------------------------------------------
# Main synthesis
# --------------------------------------------------

def synthesize_entity_list_answer(
    question,
    context,
):
    subject = subject_from_question(
        question
    )

    if not subject:
        return None

    evidence = select_leader_evidence(
        context,
        subject,
        max_sentences=2,
    )

    if not evidence:
        return None

    names = []

    for (
        _,
        _,
        sentence,
        sentence_names,
    ) in evidence:
        names.extend(
            sentence_names
        )

    names = deduplicate_names(
        names
    )

    if not names:
        return None

    # Keep only the strongest few names.
    names = names[:4]

    subject_display = clean_subject(
        subject
    )

    if len(names) == 1:
        return (
            f"A key figure in "
            f"{subject_display} was "
            f"{names[0]}."
        )

    return (
        f"Key figures in "
        f"{subject_display} included "
        f"{join_naturally(names)}."
    )


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":

    question = (
        "Who were the main leaders "
        "of the French Revolution?"
    )

    context = (
        "With powerful members, such as "
        "Maximilien Robespierre and Georges Danton, "
        "the Jacobin Club managed to secure control "
        "of the government and pursue the revolution. "
        "During the French Revolution the National "
        "Convention became the executive power of France "
        "following the execution of King Louis XVI. "
        "The patriotic members of the Bar Confederation "
        "adopted colors associated with Virgin Mary."
    )

    answer = synthesize_entity_list_answer(
        question,
        context,
    )

    print(
        answer
    )